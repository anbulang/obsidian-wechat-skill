#!/usr/bin/env python3
import publish_to_wechat as wechat


def test_classic_theme_is_default_and_preserved():
    html = wechat.md_to_html("# 标题\n\n正文")

    assert 'data-style-theme="classic"' in html
    assert 'border-bottom: 2px solid #db4c3f' in html
    assert 'background-color: #fffdf9' in html


def test_deepblue_theme_can_be_selected():
    html = wechat.md_to_html("## 小标题\n\n**重点**内容", "deepblue")

    assert 'data-style-theme="deepblue"' in html
    assert 'background: rgb(15, 76, 129)' in html
    assert 'letter-spacing: 0.1em' in html
    assert 'color: rgb(15, 76, 129); font-weight: bold;' in html


def test_frontmatter_style_precedes_config_default():
    frontmatter = {"style": "deepblue"}
    config = {"default_style": "classic"}

    assert wechat.choose_article_style(frontmatter, config) == "deepblue"


def test_cli_style_precedes_frontmatter():
    frontmatter = {"style": "classic"}
    config = {"default_style": "classic"}

    assert wechat.choose_article_style(frontmatter, config, "deepblue") == "deepblue"


def test_unknown_style_raises_helpful_error():
    try:
        wechat.md_to_html("正文", "missing")
    except ValueError as e:
        assert "未知样式主题" in str(e)
        assert "classic" in str(e)
        assert "deepblue" in str(e)
    else:
        raise AssertionError("unknown styles should fail explicitly")


def main():
    test_classic_theme_is_default_and_preserved()
    test_deepblue_theme_can_be_selected()
    test_frontmatter_style_precedes_config_default()
    test_cli_style_precedes_frontmatter()
    test_unknown_style_raises_helpful_error()
    print("✅ 样式主题测试通过")


if __name__ == "__main__":
    main()
