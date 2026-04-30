#!/usr/bin/env python3
import os
import socket
import tempfile
from unittest.mock import patch

import publish_to_wechat as wechat


def patch_attr(name, value):
    original = getattr(wechat, name)
    setattr(wechat, name, value)
    return original


def test_thumb_media_id_has_highest_priority():
    called = []
    original = patch_attr("upload_cover_material", lambda token, src: called.append(src))
    try:
        result = wechat.resolve_thumb_media_id(
            {"thumb_media_id": "existing_media", "banner": "cover.png"},
            {"default_thumb_media_id": "default_media"},
            "token",
            "/tmp",
        )
        assert result == "existing_media"
        assert called == []
    finally:
        setattr(wechat, "upload_cover_material", original)


def test_banner_local_path_is_resolved_from_article_dir():
    with tempfile.TemporaryDirectory() as tmp:
        image_path = os.path.join(tmp, "cover.png")
        open(image_path, "wb").write(b"png")
        calls = []
        original = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "cover_media")
        try:
            result = wechat.resolve_thumb_media_id(
                {"banner": "cover.png"},
                {"default_thumb_media_id": "default_media"},
                "token",
                tmp,
            )
            assert result == "cover_media"
            assert calls == [os.path.realpath(image_path)]
        finally:
            setattr(wechat, "upload_cover_material", original)


def test_banner_path_local_path_is_resolved_from_article_dir():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "assets"))
        image_path = os.path.join(tmp, "assets", "cover.jpg")
        open(image_path, "wb").write(b"jpg")
        calls = []
        original = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "cover_media")
        try:
            result = wechat.resolve_thumb_media_id(
                {"banner_path": "assets/cover.jpg"},
                {"default_thumb_media_id": "default_media"},
                "token",
                tmp,
            )
            assert result == "cover_media"
            assert calls == [os.path.realpath(image_path)]
        finally:
            setattr(wechat, "upload_cover_material", original)


def test_cover_alias_field_has_priority_over_body_first_image():
    with tempfile.TemporaryDirectory() as tmp:
        cover_path = os.path.join(tmp, "cover.webp")
        body_path = os.path.join(tmp, "body.webp")
        open(cover_path, "wb").write(b"cover")
        open(body_path, "wb").write(b"body")
        calls = []
        original = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "cover_media")
        try:
            result = wechat.resolve_thumb_media_id(
                {"image": "cover.webp"},
                {"default_thumb_media_id": "default_media"},
                "token",
                tmp,
                "body.webp",
            )
            assert result == "cover_media"
            assert calls == [os.path.realpath(cover_path)]
        finally:
            setattr(wechat, "upload_cover_material", original)


def test_body_first_image_is_used_before_default_cover():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".obsidian"))
        article_dir = os.path.join(tmp, "notes")
        asset_dir = os.path.join(tmp, "Troubleshooting", "images")
        os.makedirs(article_dir)
        os.makedirs(asset_dir)
        image_path = os.path.join(asset_dir, "fig_1__codex_drives_the_app_.webp")
        open(image_path, "wb").write(b"webp")

        calls = []
        original = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "first_image_media")
        try:
            result = wechat.resolve_thumb_media_id(
                {"title": "Title"},
                {"default_thumb_media_id": "default_media"},
                "token",
                article_dir,
                "fig_1__codex_drives_the_app_.webp",
            )
            assert result == "first_image_media"
            assert calls == [os.path.realpath(image_path)]
        finally:
            setattr(wechat, "upload_cover_material", original)


def test_remote_banner_uses_temp_file_and_cleans_up():
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"jpg")
        temp_path = f.name

    calls = []
    original_download = patch_attr("download_image_to_temp", lambda url: temp_path)
    original_upload = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "cover_media")
    try:
        result = wechat.resolve_thumb_media_id(
            {"banner": "https://example.com/cover.jpg"},
            {"default_thumb_media_id": "default_media"},
            "token",
            "/tmp",
        )
        assert result == "cover_media"
        assert calls == [temp_path]
        assert not os.path.exists(temp_path)
    finally:
        setattr(wechat, "download_image_to_temp", original_download)
        setattr(wechat, "upload_cover_material", original_upload)
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_explicit_cover_failure_does_not_fall_back_to_default():
    try:
        wechat.resolve_thumb_media_id(
            {"banner": "missing.png"},
            {"default_thumb_media_id": "default_media"},
            "token",
            "/tmp",
        )
    except RuntimeError as e:
        assert "banner 封面处理失败" in str(e)
        assert "missing.png" in str(e)
    else:
        raise AssertionError("missing explicit cover should abort")


def test_cover_rejects_unsafe_local_sources():
    with tempfile.TemporaryDirectory() as tmp:
        article_dir = os.path.join(tmp, "article")
        os.makedirs(article_dir)
        outside_path = os.path.join(tmp, "cover.png")
        open(outside_path, "wb").write(b"png")

        cases = [
            (outside_path, "本地图片必须使用文章目录内的相对路径"),
            (f"file://{outside_path}", "本地图片不允许使用 URL scheme"),
            ("../cover.png", "本地图片路径不允许包含 .."),
        ]

        for src, expected in cases:
            try:
                wechat.resolve_thumb_media_id(
                    {"banner": src},
                    {"default_thumb_media_id": "default_media"},
                    "token",
                    article_dir,
                )
            except RuntimeError as e:
                assert expected in str(e)
            else:
                raise AssertionError(f"unsafe cover should abort: {src}")


def test_cover_rejects_unsafe_remote_sources():
    cases = [
        ("http://example.com/cover.png", "远程图片仅允许 https URL"),
        ("https://localhost/cover.png", "远程图片不允许使用 localhost"),
        ("https://10.0.0.1/cover.png", "远程图片主机解析到不安全地址"),
    ]

    for src, expected in cases:
        try:
            wechat.resolve_thumb_media_id(
                {"banner": src},
                {"default_thumb_media_id": "default_media"},
                "token",
                "/tmp",
            )
        except RuntimeError as e:
            assert expected in str(e)
        else:
            raise AssertionError(f"unsafe cover URL should abort: {src}")


def test_remote_download_validates_redirect_target():
    class Response:
        status_code = 302
        content = b""
        headers = {"Location": "https://127.0.0.1/private.png"}
        is_redirect = True
        is_permanent_redirect = False

        def close(self):
            pass

    def fake_request_response(*args, **kwargs):
        return Response()

    with (
        patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]),
        patch.object(wechat, "request_response", fake_request_response),
    ):
        try:
            wechat._safe_get_remote_image("https://example.com/cover.png")
        except ValueError as e:
            assert "远程图片主机解析到不安全地址" in str(e)
        else:
            raise AssertionError("unsafe redirect target should abort")


def test_default_cover_is_used_when_no_article_cover_exists():
    original = patch_attr("get_auto_cover", lambda config, token, title, digest: None)
    try:
        result = wechat.resolve_thumb_media_id(
            {"title": "Title"},
            {"default_thumb_media_id": "default_media"},
            "token",
            "/tmp",
        )
        assert result == "default_media"
    finally:
        setattr(wechat, "get_auto_cover", original)


def main():
    test_thumb_media_id_has_highest_priority()
    test_banner_local_path_is_resolved_from_article_dir()
    test_banner_path_local_path_is_resolved_from_article_dir()
    test_cover_alias_field_has_priority_over_body_first_image()
    test_body_first_image_is_used_before_default_cover()
    test_remote_banner_uses_temp_file_and_cleans_up()
    test_explicit_cover_failure_does_not_fall_back_to_default()
    test_cover_rejects_unsafe_local_sources()
    test_cover_rejects_unsafe_remote_sources()
    test_remote_download_validates_redirect_target()
    test_default_cover_is_used_when_no_article_cover_exists()
    print("✅ 封面处理测试通过")


if __name__ == "__main__":
    main()
