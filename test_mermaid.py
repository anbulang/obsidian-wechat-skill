#!/usr/bin/env python3
"""
测试 Mermaid 渲染功能
"""
import sys
import os
import types

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

import publish_to_wechat as wechat

# 测试用的 Markdown 内容
test_content = """
# 测试文档

这是一个包含 Mermaid 图表的测试文档。

```mermaid
graph TD
    A[开始] --> B{判断条件}
    B -->|是| C[执行操作]
    B -->|否| D[跳过]
    C --> E[结束]
    D --> E
```

## 另一个图表

```mermaid
sequenceDiagram
    Alice->>Bob: 你好 Bob
    Bob-->>Alice: 你好 Alice
    Alice->>Bob: 最近怎么样?
    Bob-->>Alice: 很好，谢谢!
```

测试完成。
"""

def test_playwright_failure_closes_resources_and_deletes_temp_html():
    state = {"html_path": None, "context_closed": False, "browser_closed": False}

    class FakePage:
        def goto(self, url):
            state["html_path"] = url.removeprefix("file://")
            assert os.path.exists(state["html_path"])
            raise RuntimeError("boom")

    class FakeContext:
        def new_page(self):
            return FakePage()

        def close(self):
            state["context_closed"] = True

    class FakeBrowser:
        def new_context(self, **kwargs):
            return FakeContext()

        def close(self):
            state["browser_closed"] = True

    class FakeChromium:
        def launch(self, **kwargs):
            return FakeBrowser()

    class FakePlaywright:
        chromium = FakeChromium()

    class FakeSyncPlaywright:
        def __enter__(self):
            return FakePlaywright()

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_playwright_module = types.ModuleType("playwright")
    fake_sync_api = types.ModuleType("playwright.sync_api")
    fake_sync_api.sync_playwright = lambda: FakeSyncPlaywright()
    fake_playwright_module.sync_api = fake_sync_api
    original_playwright = sys.modules.get("playwright")
    original_sync_api = sys.modules.get("playwright.sync_api")
    sys.modules["playwright"] = fake_playwright_module
    sys.modules["playwright.sync_api"] = fake_sync_api

    try:
        result = wechat.render_mermaid_with_playwright("graph TD\nA-->B")
        assert result is None
        assert state["context_closed"] is True
        assert state["browser_closed"] is True
        assert state["html_path"]
        assert not os.path.exists(state["html_path"])
    finally:
        if original_playwright is None:
            sys.modules.pop("playwright", None)
        else:
            sys.modules["playwright"] = original_playwright
        if original_sync_api is None:
            sys.modules.pop("playwright.sync_api", None)
        else:
            sys.modules["playwright.sync_api"] = original_sync_api


def main():
    html = wechat._build_mermaid_html('graph TD\nA["</pre><script>alert(1)</script>"]')
    assert '</pre><script>alert(1)</script>' not in html
    assert '&lt;/pre&gt;&lt;script&gt;alert(1)&lt;/script&gt;' in html

    print("=" * 60)
    print("Mermaid 渲染测试")
    print("=" * 60)

    original = wechat.render_mermaid_locally
    wechat.render_mermaid_locally = lambda code: None
    try:
        result = wechat.process_mermaid(test_content)
    finally:
        wechat.render_mermaid_locally = original

    print("\n" + "=" * 60)
    print("处理结果:")
    print("=" * 60)
    print(result)

    # 检查是否包含图片或降级代码块
    if '![MERMAID_DIAGRAM](' in result or 'mermaid-fallback' in result:
        print("\n✅ 测试通过: Mermaid 代码块已被处理")
    else:
        print("\n❌ 测试失败: Mermaid 代码块未被处理")

    test_playwright_failure_closes_resources_and_deletes_temp_html()
    print("✅ Playwright 异常清理测试通过")

if __name__ == "__main__":
    main()
