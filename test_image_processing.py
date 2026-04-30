#!/usr/bin/env python3
import os
import socket
import sys
import tempfile
import types
from unittest.mock import patch

import publish_to_wechat as wechat


class FakeStreamResponse:
    def __init__(self, chunks, headers=None, status_code=200):
        self._chunks = chunks
        self.headers = headers or {}
        self.status_code = status_code
        self.is_redirect = False
        self.is_permanent_redirect = False
        self.closed = False

    def iter_content(self, chunk_size):
        for chunk in self._chunks:
            yield chunk

    @property
    def content(self):
        raise AssertionError("remote image download should stream chunks, not read resp.content")

    def close(self):
        self.closed = True


def with_fake_upload(fn):
    original = wechat.upload_image
    calls = []

    def fake_upload(token, src):
        calls.append(src)
        name = os.path.basename(src)
        return f"https://mmbiz.qpic.cn/{name}"

    wechat.upload_image = fake_upload
    try:
        fn(calls)
    finally:
        wechat.upload_image = original


def test_standard_markdown_relative_image():
    with tempfile.TemporaryDirectory() as tmp:
        article_dir = os.path.join(tmp, "notes")
        image_dir = os.path.join(article_dir, "images")
        os.makedirs(image_dir)
        image_path = os.path.join(image_dir, "a.png")
        open(image_path, "wb").write(b"png")

        content = "hello\n\n![Alt](images/a.png)\n\nworld"

        def run(calls):
            _, body = wechat.process_content_workflow(content, "token", article_dir)
            assert calls == [os.path.realpath(image_path)]
            assert 'src="https://mmbiz.qpic.cn/a.png"' in body
            assert 'alt="Alt"' in body

        with_fake_upload(run)


def test_obsidian_embed_image_variants():
    with tempfile.TemporaryDirectory() as tmp:
        image_path = os.path.join(tmp, "image.png")
        nested_path = os.path.join(tmp, "folder", "b.png")
        os.makedirs(os.path.dirname(nested_path))
        open(image_path, "wb").write(b"png")
        open(nested_path, "wb").write(b"png")

        content = "\n".join([
            "![[image.png]]",
            "![[folder/b.png|描述]]",
            "![[image.png|300]]",
        ])

        def run(calls):
            _, body = wechat.process_content_workflow(content, "token", tmp)
            assert calls == [os.path.realpath(image_path), os.path.realpath(nested_path), os.path.realpath(image_path)]
            assert 'alt="image"' in body
            assert 'alt="描述"' in body
            assert body.count("https://mmbiz.qpic.cn/image.png") == 2
            assert "https://mmbiz.qpic.cn/b.png" in body

        with_fake_upload(run)


def test_obsidian_embed_finds_unique_file_in_vault():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".obsidian"))
        article_dir = os.path.join(tmp, "notes", "posts")
        attachment_dir = os.path.join(tmp, "assets", "wechat")
        os.makedirs(article_dir)
        os.makedirs(attachment_dir)
        image_path = os.path.join(attachment_dir, "fig_1__codex_drives_the_app_.webp")
        open(image_path, "wb").write(b"webp")

        content = "![[fig_1__codex_drives_the_app_.webp]]"

        def run(calls):
            _, body = wechat.process_content_workflow(content, "token", article_dir)
            assert calls == [os.path.realpath(image_path)]
            assert 'src="https://mmbiz.qpic.cn/fig_1__codex_drives_the_app_.webp"' in body

        with_fake_upload(run)


def test_obsidian_embed_duplicate_vault_filenames_abort():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".obsidian"))
        article_dir = os.path.join(tmp, "notes")
        first_dir = os.path.join(tmp, "assets", "one")
        second_dir = os.path.join(tmp, "assets", "two")
        os.makedirs(article_dir)
        os.makedirs(first_dir)
        os.makedirs(second_dir)
        open(os.path.join(first_dir, "duplicate.webp"), "wb").write(b"1")
        open(os.path.join(second_dir, "duplicate.webp"), "wb").write(b"2")

        try:
            wechat.process_content_workflow("![[duplicate.webp]]", "token", article_dir)
        except RuntimeError as e:
            assert "Vault 中存在多个同名图片" in str(e)
        else:
            raise AssertionError("duplicate vault filenames should abort")


def test_remote_image_keeps_url_for_upload():
    content = "![Remote](https://example.com/a.png)"

    def run(calls):
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]):
            _, body = wechat.process_content_workflow(content, "token", "/tmp")
            assert calls == ["https://example.com/a.png"]
            assert 'src="https://mmbiz.qpic.cn/a.png"' in body

    with_fake_upload(run)


def test_first_body_image_source_prefers_earliest_image_syntax():
    content = "\n".join([
        "intro",
        "![[cover.webp|说明]]",
        "![Later](later.png)",
    ])
    assert wechat.extract_first_body_image_source(content) == "cover.webp"


def test_remote_image_upload_streams_to_temp_file_and_cleans_up():
    response = FakeStreamResponse(
        [b"abc", b"def"],
        headers={"Content-Type": "image/png", "Content-Length": "6"},
    )
    post_paths = []
    unlinked = []

    original_request_response = wechat.request_response
    original_request_json = wechat.request_json
    original_unlink = wechat.os.unlink

    def fake_request_response(*args, **kwargs):
        assert kwargs.get("stream") is True
        return response

    def fake_request_json(method, url, files=None, **kwargs):
        assert method == "POST"
        media = files["media"]
        post_paths.append(media[1].name)
        assert media[1].read() == b"abcdef"
        return {"url": "https://mmbiz.qpic.cn/streamed.png"}

    def fake_unlink(path):
        unlinked.append(path)
        original_unlink(path)

    wechat.request_response = fake_request_response
    wechat.request_json = fake_request_json
    wechat.os.unlink = fake_unlink
    try:
        result = wechat.upload_image("token", "https://example.com/a.png")
        assert result == "https://mmbiz.qpic.cn/streamed.png"
        assert len(post_paths) == 1
        assert unlinked == post_paths
        assert not os.path.exists(post_paths[0])
        assert response.closed is True
    finally:
        wechat.request_response = original_request_response
        wechat.request_json = original_request_json
        wechat.os.unlink = original_unlink


def test_webp_upload_converts_to_png_and_cleans_temp_file():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            from PIL import Image
        except ImportError:
            print("跳过 WebP 转换测试: 未安装 Pillow")
            return

        image_path = os.path.join(tmp, "source.webp")
        Image.new("RGB", (2, 2), color=(255, 0, 0)).save(image_path, format="WEBP")
        uploaded = {}
        unlinked = []

        original_request_json = wechat.request_json
        original_unlink = wechat.os.unlink

        def fake_request_json(method, url, files=None, **kwargs):
            media = files["media"]
            uploaded["filename"] = media[0]
            uploaded["content_type"] = media[2]
            uploaded["path"] = media[1].name
            assert media[1].read(8).startswith(b"\x89PNG")
            return {"url": "https://mmbiz.qpic.cn/source.png"}

        def fake_unlink(path):
            unlinked.append(path)
            original_unlink(path)

        wechat.request_json = fake_request_json
        wechat.os.unlink = fake_unlink
        try:
            result = wechat.upload_image("token", image_path)
            assert result == "https://mmbiz.qpic.cn/source.png"
            assert uploaded["filename"] == "source.png"
            assert uploaded["content_type"] == "image/png"
            assert uploaded["path"] in unlinked
            assert not os.path.exists(uploaded["path"])
            assert os.path.exists(image_path)
        finally:
            wechat.request_json = original_request_json
            wechat.os.unlink = original_unlink


def test_svg_upload_converts_to_png_with_cairosvg_and_cleans_temp_file():
    with tempfile.TemporaryDirectory() as tmp:
        image_path = os.path.join(tmp, "diagram.svg")
        open(image_path, "w").write('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        uploaded = {}
        unlinked = []

        fake_cairosvg = types.ModuleType("cairosvg")

        def fake_svg2png(url, write_to):
            assert url == image_path
            with open(write_to, "wb") as f:
                f.write(b"\x89PNG\r\n\x1a\nfake")

        fake_cairosvg.svg2png = fake_svg2png
        original_cairosvg = sys.modules.get("cairosvg")
        original_request_json = wechat.request_json
        original_unlink = wechat.os.unlink

        def fake_request_json(method, url, files=None, **kwargs):
            media = files["media"]
            uploaded["filename"] = media[0]
            uploaded["content_type"] = media[2]
            uploaded["path"] = media[1].name
            assert media[1].read(8).startswith(b"\x89PNG")
            return {"url": "https://mmbiz.qpic.cn/diagram.png"}

        def fake_unlink(path):
            unlinked.append(path)
            original_unlink(path)

        sys.modules["cairosvg"] = fake_cairosvg
        wechat.request_json = fake_request_json
        wechat.os.unlink = fake_unlink
        try:
            result = wechat.upload_image("token", image_path)
            assert result == "https://mmbiz.qpic.cn/diagram.png"
            assert uploaded["filename"] == "diagram.png"
            assert uploaded["content_type"] == "image/png"
            assert uploaded["path"] in unlinked
            assert not os.path.exists(uploaded["path"])
            assert os.path.exists(image_path)
        finally:
            if original_cairosvg is None:
                sys.modules.pop("cairosvg", None)
            else:
                sys.modules["cairosvg"] = original_cairosvg
            wechat.request_json = original_request_json
            wechat.os.unlink = original_unlink


def test_remote_image_download_rejects_oversized_content_length():
    response = FakeStreamResponse(
        [b"x"],
        headers={"Content-Type": "image/jpeg", "Content-Length": str(wechat.MAX_REMOTE_IMAGE_BYTES + 1)},
    )
    original_request_response = wechat.request_response
    try:
        wechat.request_response = lambda *args, **kwargs: response
        assert wechat.download_image_to_temp("https://example.com/huge.jpg") is None
        assert response.closed is True
    finally:
        wechat.request_response = original_request_response


def test_remote_image_download_rejects_oversized_stream_and_deletes_temp():
    response = FakeStreamResponse(
        [b"1234", b"5678"],
        headers={"Content-Type": "image/jpeg"},
    )
    unlinked = []
    original_request_response = wechat.request_response
    original_unlink = wechat.os.unlink

    def fake_unlink(path):
        unlinked.append(path)
        original_unlink(path)

    wechat.request_response = lambda *args, **kwargs: response
    wechat.os.unlink = fake_unlink
    try:
        assert wechat.download_image_to_temp("https://example.com/huge.jpg", max_bytes=5) is None
        assert len(unlinked) == 1
        assert not os.path.exists(unlinked[0])
        assert response.closed is True
    finally:
        wechat.request_response = original_request_response
        wechat.os.unlink = original_unlink


def test_generated_mermaid_png_is_deleted_after_upload():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"png")
        mermaid_path = f.name

    original_render = wechat.render_mermaid_locally
    original_upload = wechat.upload_image
    try:
        wechat.render_mermaid_locally = lambda code: mermaid_path
        wechat.upload_image = lambda token, src: "https://mmbiz.qpic.cn/mermaid.png"
        _, body = wechat.process_content_workflow("```mermaid\ngraph TD\n```", "token", "/tmp")
        assert "https://mmbiz.qpic.cn/mermaid.png" in body
        assert not os.path.exists(mermaid_path)
    finally:
        wechat.render_mermaid_locally = original_render
        wechat.upload_image = original_upload
        if os.path.exists(mermaid_path):
            os.unlink(mermaid_path)


def test_local_image_does_not_fall_back_to_cwd():
    with tempfile.TemporaryDirectory() as tmp:
        article_dir = os.path.join(tmp, "article")
        cwd_dir = os.path.join(tmp, "cwd")
        os.makedirs(article_dir)
        os.makedirs(cwd_dir)
        open(os.path.join(cwd_dir, "leak.png"), "wb").write(b"png")

        old_cwd = os.getcwd()
        os.chdir(cwd_dir)
        try:
            try:
                wechat.process_content_workflow("![Leak](leak.png)", "token", article_dir)
            except RuntimeError as e:
                assert "本地图片不存在: leak.png" in str(e)
            else:
                raise AssertionError("image outside article dir should abort")
        finally:
            os.chdir(old_cwd)


def test_local_image_rejects_absolute_file_and_parent_paths():
    with tempfile.TemporaryDirectory() as tmp:
        article_dir = os.path.join(tmp, "article")
        os.makedirs(article_dir)
        outside_path = os.path.join(tmp, "outside.png")
        open(outside_path, "wb").write(b"png")

        cases = [
            (outside_path, "本地图片必须使用文章目录内的相对路径"),
            (f"file://{outside_path}", "本地图片不允许使用 URL scheme"),
            ("../outside.png", "本地图片路径不允许包含 .."),
        ]

        for src, expected in cases:
            try:
                wechat.process_content_workflow(f"![Bad]({src})", "token", article_dir)
            except RuntimeError as e:
                assert expected in str(e)
            else:
                raise AssertionError(f"unsafe path should abort: {src}")


def test_mermaid_alt_does_not_bypass_absolute_path_restriction():
    with tempfile.TemporaryDirectory() as tmp:
        outside_path = os.path.join(tmp, "outside.png")
        article_dir = os.path.join(tmp, "article")
        os.makedirs(article_dir)
        open(outside_path, "wb").write(b"png")

        try:
            wechat.process_content_workflow(f"![MERMAID_DIAGRAM]({outside_path})", "token", article_dir)
        except RuntimeError as e:
            assert "本地图片必须使用文章目录内的相对路径" in str(e)
        else:
            raise AssertionError("spoofed Mermaid image should not bypass local path checks")


def test_remote_image_rejects_http_and_private_hosts():
    cases = [
        ("http://example.com/a.png", "远程图片仅允许 https URL"),
        ("https://localhost/a.png", "远程图片不允许使用 localhost"),
        ("https://127.0.0.1/a.png", "远程图片主机解析到不安全地址"),
        ("https://169.254.169.254/a.png", "远程图片主机解析到不安全地址"),
    ]

    for src, expected in cases:
        try:
            wechat.process_content_workflow(f"![Bad]({src})", "token", "/tmp")
        except RuntimeError as e:
            assert expected in str(e)
        else:
            raise AssertionError(f"unsafe remote URL should abort: {src}")


def test_missing_image_aborts_publish_content():
    try:
        wechat.process_content_workflow("![Missing](missing.png)", "token", "/tmp")
    except RuntimeError as e:
        assert "图片处理失败，已中止发布" in str(e)
        assert "missing.png" in str(e)
    else:
        raise AssertionError("missing image should abort")


def main():
    test_standard_markdown_relative_image()
    test_obsidian_embed_image_variants()
    test_obsidian_embed_finds_unique_file_in_vault()
    test_obsidian_embed_duplicate_vault_filenames_abort()
    test_remote_image_keeps_url_for_upload()
    test_first_body_image_source_prefers_earliest_image_syntax()
    test_remote_image_upload_streams_to_temp_file_and_cleans_up()
    test_webp_upload_converts_to_png_and_cleans_temp_file()
    test_svg_upload_converts_to_png_with_cairosvg_and_cleans_temp_file()
    test_remote_image_download_rejects_oversized_content_length()
    test_remote_image_download_rejects_oversized_stream_and_deletes_temp()
    test_generated_mermaid_png_is_deleted_after_upload()
    test_local_image_does_not_fall_back_to_cwd()
    test_local_image_rejects_absolute_file_and_parent_paths()
    test_mermaid_alt_does_not_bypass_absolute_path_restriction()
    test_remote_image_rejects_http_and_private_hosts()
    test_missing_image_aborts_publish_content()
    print("✅ 图片处理测试通过")


if __name__ == "__main__":
    main()
