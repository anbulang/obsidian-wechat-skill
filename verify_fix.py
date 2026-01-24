import sys
import os

# Ensure we can import the module
sys.path.append(os.getcwd())

from publish_to_wechat import process_mermaid, process_admonitions, process_footnotes

def test_mermaid():
    content = "```mermaid\ngraph TD;\n    A-->B;\n```"
    result = process_mermaid(content)
    print("--- Mermaid Result ---")
    print(result)
    if "mermaid.ink/img/" in result:
        print("✅ Mermaid conversion successful")
    else:
        print("❌ Mermaid conversion failed")

def test_admonition():
    content = "```ad-tip\ntitle: Test Tip\nThis is a tip.\n```"
    result = process_admonitions(content)
    print("\n--- Admonition Result ---")
    print(result)
    # Tip maps to abstract style (teal color)
    if "This is a tip" in result and "Test Tip" in result:
        print("✅ Admonition conversion successful")
    else:
        print("❌ Admonition conversion failed")

def test_footnote():
    content = "Link to [Google](https://google.com)"
    result = process_footnotes(content)
    print("\n--- Footnote Result ---")
    print(result)
    if "footnotes" in result and "Google: https://google.com" in result:
        print("✅ Footnote conversion successful")
    else:
        print("❌ Footnote conversion failed")

if __name__ == "__main__":
    test_mermaid()
    test_admonition()
    test_footnote()
