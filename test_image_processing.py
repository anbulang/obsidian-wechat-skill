#!/usr/bin/env python3
import os
import tempfile

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
    test_missing_image_aborts_publish_content()
    print("✅ 图片处理测试通过")


if __name__ == "__main__":
    main()
