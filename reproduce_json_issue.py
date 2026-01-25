import sys
import os
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

# Mocking the md_to_html logic from publish_to_wechat.py
def md_to_html(md_content):
    html = markdown.markdown(md_content,
        extensions=['fenced_code', 'tables', 'codehilite'],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': True,
                'use_pygments': True,
                'noclasses': True
            }
        }
    )
    return html

def test_json_parsing():
    content = """
```json
{
  "sub": "10086",           // 内部员工工号
  "name": "张三",            // 姓名
  "role": ["admin", "hr"],  // 角色
  "iss": "Internal_IAM",    // 签发者
  "exp": 1718900000         // 过期时间
}
```
"""
    print("--- Input Markdown ---")
    print(content)

    html = md_to_html(content)

    print("\n--- Output HTML ---")
    print(html)

    if '<div class="highlight">' in html:
        print("\n✅ Processed by CodeHilite (Pygments)")
    else:
        print("\n❌ NOT processed by CodeHilite (Likely raw pre/code)")

if __name__ == "__main__":
    test_json_parsing()
