#!/usr/bin/env python3
import os
import tempfile

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
            assert calls == [image_path]
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
            assert calls == [image_path]
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
    test_remote_banner_uses_temp_file_and_cleans_up()
    test_explicit_cover_failure_does_not_fall_back_to_default()
    test_default_cover_is_used_when_no_article_cover_exists()
    print("✅ 封面处理测试通过")


if __name__ == "__main__":
    main()
