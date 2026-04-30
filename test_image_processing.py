#!/usr/bin/env python3
import os
import tempfile

import publish_to_wechat as wechat


class FakeStreamResponse:
    def __init__(self, chunks, headers=None, status_code=200):
        self._chunks = chunks
        self.headers = headers or {}
        self.status_code = status_code
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
            assert calls == [image_path]
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
            assert calls == [image_path, nested_path, image_path]
            assert 'alt="image"' in body
            assert 'alt="描述"' in body
            assert body.count("https://mmbiz.qpic.cn/image.png") == 2
            assert "https://mmbiz.qpic.cn/b.png" in body

        with_fake_upload(run)


def test_remote_image_keeps_url_for_upload():
    content = "![Remote](https://example.com/a.png)"

    def run(calls):
        _, body = wechat.process_content_workflow(content, "token", "/tmp")
        assert calls == ["https://example.com/a.png"]
        assert 'src="https://mmbiz.qpic.cn/a.png"' in body

    with_fake_upload(run)


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
    test_remote_image_keeps_url_for_upload()
    test_remote_image_upload_streams_to_temp_file_and_cleans_up()
    test_remote_image_download_rejects_oversized_content_length()
    test_remote_image_download_rejects_oversized_stream_and_deletes_temp()
    test_generated_mermaid_png_is_deleted_after_upload()
    test_missing_image_aborts_publish_content()
    print("✅ 图片处理测试通过")


if __name__ == "__main__":
    main()
