#!/usr/bin/env python3
import time
import requests

import publish_to_wechat as wechat


def patch_attr(name, value):
    original = getattr(wechat, name)
    setattr(wechat, name, value)
    return original


def test_unexpired_token_is_reused():
    config = {
        "appid": "appid",
        "secret": "secret",
        "access_token": "cached-token",
        "token_expires": time.time() + 3600,
    }

    original = patch_attr("request_json", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("should not refresh")))
    try:
        assert wechat.get_access_token(config) == "cached-token"
    finally:
        setattr(wechat, "request_json", original)


def test_expired_token_is_refreshed():
    config = {
        "appid": "appid",
        "secret": "secret",
        "access_token": "old-token",
        "token_expires": time.time() - 10,
    }
    calls = []

    def fake_request_json(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return {"access_token": "new-token", "expires_in": 7200}

    original = patch_attr("request_json", fake_request_json)
    try:
        assert wechat.get_access_token(config) == "new-token"
        assert config["access_token"] == "new-token"
        assert config["token_expires"] > time.time() + 7000
        assert calls[0][0] == "GET"
        assert calls[0][2]["params"]["secret"] == "secret"
    finally:
        setattr(wechat, "request_json", original)


def test_request_json_passes_timeout_to_requests():
    calls = []

    class FakeResponse:
        text = '{"ok": true}'

        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    def fake_request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return FakeResponse()

    original = wechat.requests.request
    wechat.requests.request = fake_request
    try:
        assert wechat.request_json("POST", "https://example.test/api", data=b"{}") == {"ok": True}
        assert calls[0][2]["timeout"] == wechat.DEFAULT_HTTP_TIMEOUT
    finally:
        wechat.requests.request = original


def test_request_error_includes_redacted_response_body():
    class FakeResponse:
        text = '{"error":{"code":"ModelNotOpen","message":"secret=should-hide token=abc"}}'

        def raise_for_status(self):
            raise requests.HTTPError("404 Client Error: Not Found", response=self)

    def fake_request(method, url, **kwargs):
        return FakeResponse()

    original = wechat.requests.request
    wechat.requests.request = fake_request
    try:
        try:
            wechat.request_json("POST", "https://example.test/api")
        except wechat.WechatRequestError as e:
            message = str(e)
            assert "ModelNotOpen" in message
            assert "secret=<redacted>" in message
            assert "token=<redacted>" in message
            assert "should-hide" not in message
            assert "abc" not in message
        else:
            raise AssertionError("HTTP error should raise")
    finally:
        wechat.requests.request = original


def test_draft_add_refreshes_token_once_on_invalid_token():
    config = {
        "appid": "appid",
        "secret": "secret",
        "access_token": "old-token",
        "token_expires": time.time() + 3600,
    }
    calls = []

    def fake_request_json(method, url, **kwargs):
        calls.append((method, url, kwargs))
        if "/draft/add" in url and "old-token" in url:
            return {"errcode": 40001, "errmsg": "invalid credential"}
        if "/token" in url:
            return {"access_token": "new-token", "expires_in": 7200}
        if "/draft/add" in url and "new-token" in url:
            return {"media_id": "draft-media"}
        raise AssertionError(f"unexpected call: {method} {url}")

    original = patch_attr("request_json", fake_request_json)
    try:
        result = wechat.publish_draft("old-token", {"articles": [{"title": "T"}]}, config)
        assert result == {"media_id": "draft-media"}
        draft_urls = [url for _, url, _ in calls if "/draft/add" in url]
        assert len(draft_urls) == 2
        assert "old-token" in draft_urls[0]
        assert "new-token" in draft_urls[1]
        assert config["access_token"] == "new-token"
    finally:
        setattr(wechat, "request_json", original)


def main():
    test_unexpired_token_is_reused()
    test_expired_token_is_refreshed()
    test_request_json_passes_timeout_to_requests()
    test_request_error_includes_redacted_response_body()
    test_draft_add_refreshes_token_once_on_invalid_token()
    print("✅ HTTP/token 稳定性测试通过")


if __name__ == "__main__":
    main()
