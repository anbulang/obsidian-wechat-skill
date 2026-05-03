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


def test_cover_alias_field_has_priority_over_ai_cover():
    with tempfile.TemporaryDirectory() as tmp:
        cover_path = os.path.join(tmp, "cover.webp")
        open(cover_path, "wb").write(b"cover")
        calls = []
        original = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "cover_media")
        original_ai = patch_attr("generate_ai_cover_image", lambda config, frontmatter, body: calls.append("ai") or None)
        try:
            result = wechat.resolve_thumb_media_id(
                {"image": "cover.webp"},
                {"default_thumb_media_id": "default_media", "ai_cover": {"enabled": True}},
                "token",
                tmp,
            )
            assert result == "cover_media"
            assert calls == [os.path.realpath(cover_path)]
        finally:
            setattr(wechat, "upload_cover_material", original)
            setattr(wechat, "generate_ai_cover_image", original_ai)


def test_legacy_unsplash_cover_is_skipped_when_ai_cover_enabled():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"png")
        temp_path = f.name

    calls = []
    original_generate = patch_attr("generate_ai_cover_image", lambda config, frontmatter, body: temp_path)
    original_upload = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "ai_media")
    try:
        result = wechat.resolve_thumb_media_id(
            {"banner": "https://images.unsplash.com/photo-123?q=85", "title": "Title"},
            {"default_thumb_media_id": "default_media", "ai_cover": {"enabled": True}},
            "token",
            "/tmp",
            "body",
        )
        assert result == "ai_media"
        assert calls == [temp_path]
    finally:
        setattr(wechat, "generate_ai_cover_image", original_generate)
        setattr(wechat, "upload_cover_material", original_upload)
        if os.path.exists(temp_path):
            os.unlink(temp_path)


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
    result = wechat.resolve_thumb_media_id(
        {"title": "Title"},
        {"default_thumb_media_id": "default_media"},
        "token",
        "/tmp",
    )
    assert result == "default_media"


def test_body_first_image_is_not_used_as_cover():
    with tempfile.TemporaryDirectory() as tmp:
        image_path = os.path.join(tmp, "body.png")
        open(image_path, "wb").write(b"png")
        calls = []
        original = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "body_media")
        try:
            result = wechat.resolve_thumb_media_id(
                {"title": "Title"},
                {"default_thumb_media_id": "default_media"},
                "token",
                tmp,
                "![[body.png]]",
            )
            assert result == "default_media"
            assert calls == []
        finally:
            setattr(wechat, "upload_cover_material", original)


def test_ai_cover_is_used_before_default_cover():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"png")
        temp_path = f.name

    calls = []
    original_generate = patch_attr("generate_ai_cover_image", lambda config, frontmatter, body: temp_path)
    original_upload = patch_attr("upload_cover_material", lambda token, src: calls.append(src) or "ai_media")
    try:
        result = wechat.resolve_thumb_media_id(
            {"title": "Title", "digest": "Digest"},
            {"default_thumb_media_id": "default_media", "ai_cover": {"enabled": True}},
            "token",
            "/tmp",
            "正文内容",
        )
        assert result == "ai_media"
        assert calls == [temp_path]
        assert not os.path.exists(temp_path)
    finally:
        setattr(wechat, "generate_ai_cover_image", original_generate)
        setattr(wechat, "upload_cover_material", original_upload)
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_ai_cover_failure_falls_back_to_default_cover():
    original_generate = patch_attr("generate_ai_cover_image", lambda config, frontmatter, body: (_ for _ in ()).throw(RuntimeError("boom")))
    try:
        result = wechat.resolve_thumb_media_id(
            {"title": "Title"},
            {"default_thumb_media_id": "default_media", "ai_cover": {"enabled": True}},
            "token",
            "/tmp",
            "body",
        )
        assert result == "default_media"
    finally:
        setattr(wechat, "generate_ai_cover_image", original_generate)


def test_openai_ai_cover_adapter_writes_base64_image():
    payloads = []
    original_request_json = wechat.request_json
    try:
        wechat.request_json = lambda method, url, **kwargs: payloads.append((method, url, kwargs)) or {
            "data": [{"b64_json": "iVBORw0KGgo="}]
        }
        path = wechat.generate_ai_cover_image(
            {
                "ai_cover": {
                    "enabled": True,
                    "provider": "openai",
                    "api_key": "secret-key",
                    "base_url": "https://api.example.com/v1",
                    "model": "gpt-image-2",
                }
            },
            {"title": "标题", "digest": "摘要"},
            "# 正文",
        )
        assert os.path.exists(path)
        assert open(path, "rb").read().startswith(b"\x89PNG")
        assert payloads[0][0] == "POST"
        assert payloads[0][1] == "https://api.example.com/v1/images/generations"
        assert payloads[0][2]["json"]["model"] == "gpt-image-2"
        assert "secret-key" in payloads[0][2]["headers"]["Authorization"]
    finally:
        if 'path' in locals():
            os.unlink(path)
        wechat.request_json = original_request_json


def test_doubao_ai_cover_adapter_writes_base64_image():
    payloads = []
    original_request_json = wechat.request_json
    try:
        wechat.request_json = lambda method, url, **kwargs: payloads.append((method, url, kwargs)) or {
            "code": 0,
            "message": "success",
            "data": ["iVBORw0KGgo="],
        }
        path = wechat.generate_ai_cover_image(
            {
                "ai_cover": {
                    "enabled": True,
                    "provider": "doubao",
                    "api_key": "doubao-key",
                    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                    "model": "doubao-seedream-5-0-260128",
                    "size": "2K",
                    "output_format": "png",
                    "response_format": "b64_json",
                    "watermark": False,
                }
            },
            {"title": "标题", "digest": "摘要"},
            "# 正文",
        )
        assert os.path.exists(path)
        assert open(path, "rb").read().startswith(b"\x89PNG")
        assert payloads[0][0] == "POST"
        assert payloads[0][1] == "https://ark.cn-beijing.volces.com/api/v3/images/generations"
        assert payloads[0][2]["headers"]["Authorization"] == "Bearer doubao-key"
        assert payloads[0][2]["json"] == {
            "model": "doubao-seedream-5-0-260128",
            "prompt": payloads[0][2]["json"]["prompt"],
            "size": "2K",
            "output_format": "png",
            "response_format": "b64_json",
            "watermark": False,
        }
    finally:
        if 'path' in locals():
            os.unlink(path)
        wechat.request_json = original_request_json


def test_doubao_ai_cover_adapter_downloads_url_response():
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"jpg")
        temp_path = f.name

    original_request_json = wechat.request_json
    original_download = patch_attr("download_image_to_temp", lambda url: temp_path)
    try:
        wechat.request_json = lambda method, url, **kwargs: {"data": ["https://example.com/cover.jpg"]}
        with patch.object(socket, "getaddrinfo", return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]):
            path = wechat.generate_ai_cover_image(
                {
                    "ai_cover": {
                        "enabled": True,
                        "provider": "doubao",
                        "api_key": "doubao-key",
                        "model": "doubao-seedream-5-0-260128",
                        "response_format": "url",
                    }
                },
                {"title": "Title"},
                "body",
            )
        assert path == temp_path
    finally:
        wechat.request_json = original_request_json
        setattr(wechat, "download_image_to_temp", original_download)
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_gemini_ai_cover_adapter_writes_inline_data_image():
    original_request_json = wechat.request_json
    payloads = []
    try:
        wechat.request_json = lambda method, url, **kwargs: payloads.append((method, url, kwargs)) or {
            "candidates": [{
                "content": {
                    "parts": [{
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": "iVBORw0KGgo=",
                        }
                    }]
                }
            }]
        }
        path = wechat.generate_ai_cover_image(
            {
                "ai_cover": {
                    "enabled": True,
                    "provider": "gemini",
                    "api_key": "gemini-key",
                    "base_url": "https://generativelanguage.googleapis.com/v1beta",
                    "model": "gemini-3.1-flash-image-preview",
                    "aspect_ratio": "16:9",
                    "image_size": "2K",
                }
            },
            {"title": "Title"},
            "body",
        )
        assert os.path.exists(path)
        assert open(path, "rb").read().startswith(b"\x89PNG")
        assert payloads[0][0] == "POST"
        assert payloads[0][1] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent"
        assert payloads[0][2]["headers"]["x-goog-api-key"] == "gemini-key"
        assert payloads[0][2]["json"]["generationConfig"]["responseModalities"] == ["TEXT", "IMAGE"]
        assert payloads[0][2]["json"]["generationConfig"]["imageConfig"] == {"aspectRatio": "16:9", "imageSize": "2K"}
    finally:
        wechat.request_json = original_request_json
        if 'path' in locals():
            os.unlink(path)


def test_nanobanana_provider_alias_uses_gemini_adapter():
    calls = []
    original_request_json = wechat.request_json
    try:
        wechat.request_json = lambda method, url, **kwargs: calls.append(url) or {
            "candidates": [{"content": {"parts": [{"inline_data": {"data": "iVBORw0KGgo=", "mime_type": "image/png"}}]}}]
        }
        path = wechat.generate_ai_cover_image(
            {
                "ai_cover": {
                    "enabled": True,
                    "provider": "nanobanana",
                    "api_key": "gemini-key",
                    "model": "gemini-3.1-flash-image-preview",
                }
            },
            {"title": "Title"},
            "body",
        )
        assert calls == ["https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent"]
    finally:
        wechat.request_json = original_request_json
        if 'path' in locals():
            os.unlink(path)


def test_gemini_endpoint_expands_model_placeholder():
    endpoint = wechat._ai_cover_endpoint(
        "gemini",
        {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "endpoint": "/models/{model}:generateContent",
            "model": "gemini-3.1-flash-image-preview",
        },
    )
    assert endpoint == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent"


def main():
    test_thumb_media_id_has_highest_priority()
    test_banner_local_path_is_resolved_from_article_dir()
    test_banner_path_local_path_is_resolved_from_article_dir()
    test_cover_alias_field_has_priority_over_ai_cover()
    test_legacy_unsplash_cover_is_skipped_when_ai_cover_enabled()
    test_remote_banner_uses_temp_file_and_cleans_up()
    test_explicit_cover_failure_does_not_fall_back_to_default()
    test_cover_rejects_unsafe_local_sources()
    test_cover_rejects_unsafe_remote_sources()
    test_remote_download_validates_redirect_target()
    test_default_cover_is_used_when_no_article_cover_exists()
    test_body_first_image_is_not_used_as_cover()
    test_ai_cover_is_used_before_default_cover()
    test_ai_cover_failure_falls_back_to_default_cover()
    test_openai_ai_cover_adapter_writes_base64_image()
    test_doubao_ai_cover_adapter_writes_base64_image()
    test_doubao_ai_cover_adapter_downloads_url_response()
    test_gemini_ai_cover_adapter_writes_inline_data_image()
    test_nanobanana_provider_alias_uses_gemini_adapter()
    test_gemini_endpoint_expands_model_placeholder()
    print("✅ 封面处理测试通过")


if __name__ == "__main__":
    main()
