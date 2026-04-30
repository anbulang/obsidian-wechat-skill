#!/usr/bin/env python3
import os
import socket
import tempfile
from unittest.mock import patch

import publish_to_wechat as wechat


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


def test_remote_image_keeps_url_for_upload():
    content = "![Remote](https://example.com/a.png)"

    def run(calls):
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]):
            _, body = wechat.process_content_workflow(content, "token", "/tmp")
            assert calls == ["https://example.com/a.png"]
            assert 'src="https://mmbiz.qpic.cn/a.png"' in body

    with_fake_upload(run)


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
    test_remote_image_keeps_url_for_upload()
    test_local_image_does_not_fall_back_to_cwd()
    test_local_image_rejects_absolute_file_and_parent_paths()
    test_mermaid_alt_does_not_bypass_absolute_path_restriction()
    test_remote_image_rejects_http_and_private_hosts()
    test_missing_image_aborts_publish_content()
    print("✅ 图片处理测试通过")


if __name__ == "__main__":
    main()
