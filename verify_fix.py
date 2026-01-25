import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from publish_to_wechat import md_to_html
except ImportError:
    print("Error importing publish_to_wechat")
    sys.exit(1)

test_md = """
# Test Document

## List Test
- Item 1
- Item 2
  - Nested Item 1

1. Ordered 1
2. Ordered 2

## Code Block Test
```python
def hello():
    print("Hello World")
    return True
```

Inline code: `print("hello")`
"""

html = md_to_html(test_md)
print(html)
