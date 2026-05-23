#!/usr/bin/env python3
import json
import os
import tempfile

import publish_to_wechat as wechat


def patch_attr(name, value):
    original = getattr(wechat, name, None)
    setattr(wechat, name, value)
    return original


def restore_attr(name, original):
    if original is None:
        delattr(wechat, name)
    else:
        setattr(wechat, name, original)


def test_obsidian_mp4_embed_uploads_video_material():
    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "demo.mp4")
        open(video_path, "wb").write(b"mp4")
        calls = []

        original_video = patch_attr(
            "upload_video_material",
            lambda token, src, title, introduction: calls.append((token, src, title, introduction)) or "VIDEO_MEDIA_ID",
        )
        original_image = patch_attr(
            "upload_image",
            lambda token, src: (_ for _ in ()).throw(AssertionError("video should not use image upload")),
        )

        try:
            _, body = wechat.process_content_workflow("![[demo.mp4|演示视频]]", "token", tmp)
        finally:
            restore_attr("upload_video_material", original_video)
            restore_attr("upload_image", original_image)

        assert calls == [("token", os.path.realpath(video_path), "演示视频", "演示视频")]
        assert "VIDEO_MEDIA_ID" in body
        assert "mpvideo" in body


def test_standard_markdown_mp4_embed_uploads_video_material():
    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "clip.mp4")
        open(video_path, "wb").write(b"mp4")
        calls = []

        original_video = patch_attr(
            "upload_video_material",
            lambda token, src, title, introduction: calls.append((src, title, introduction)) or "VIDEO_MEDIA_ID",
        )

        try:
            _, body = wechat.process_content_workflow("![剪辑](clip.mp4)", "token", tmp)
        finally:
            restore_attr("upload_video_material", original_video)

        assert calls == [(os.path.realpath(video_path), "剪辑", "剪辑")]
        assert "VIDEO_MEDIA_ID" in body
        assert "mpvideo" in body


def test_non_mp4_video_embed_aborts_before_image_upload():
    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "demo.mov")
        open(video_path, "wb").write(b"mov")

        try:
            wechat.process_content_workflow("![[demo.mov]]", "token", tmp)
        except RuntimeError as e:
            assert "仅支持 MP4" in str(e)
        else:
            raise AssertionError("non-MP4 video embeds should abort")


def test_upload_video_material_posts_description():
    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "demo.mp4")
        open(video_path, "wb").write(b"mp4")
        captured = {}

        def fake_request_json(method, url, **kwargs):
            captured["method"] = method
            captured["url"] = url
            captured["data"] = kwargs.get("data")
            media = kwargs["files"]["media"]
            captured["media"] = (media[0], media[2], media[1].read())
            return {"media_id": "VIDEO_MEDIA_ID"}

        original_request = patch_attr("request_json", fake_request_json)
        try:
            result = wechat.upload_video_material("token", video_path, "标题", "简介")
        finally:
            restore_attr("request_json", original_request)

        assert result == "VIDEO_MEDIA_ID"
        assert captured["method"] == "POST"
        assert captured["url"].endswith("/material/add_material?access_token=token&type=video")
        assert captured["media"] == ("demo.mp4", "video/mp4", b"mp4")
        assert json.loads(captured["data"]["description"]) == {"title": "标题", "introduction": "简介"}


def test_video_html_survives_markdown_conversion():
    body = wechat.build_wechat_video_html("VIDEO_MEDIA_ID", "演示", "/tmp/demo.mp4")
    html = wechat.md_to_html(body)

    assert "<mpvideo" in html
    assert 'data-mediaid="VIDEO_MEDIA_ID"' in html
    assert 'data-title="演示"' in html
