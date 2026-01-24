#!/usr/bin/env python3
"""
测试 Mermaid 渲染功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from publish_to_wechat import process_mermaid

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

def main():
    print("=" * 60)
    print("Mermaid 渲染测试")
    print("=" * 60)

    result = process_mermaid(test_content)

    print("\n" + "=" * 60)
    print("处理结果:")
    print("=" * 60)
    print(result)

    # 检查是否包含图片或降级代码块
    if '![](' in result or 'mermaid-fallback' in result:
        print("\n✅ 测试通过: Mermaid 代码块已被处理")
    else:
        print("\n❌ 测试失败: Mermaid 代码块未被处理")

if __name__ == "__main__":
    main()
