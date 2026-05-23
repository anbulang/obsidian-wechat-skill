# 微信公众号样式主题

发布脚本支持可配置样式主题。主题会同时影响 `#nice` 基础 CSS 和关键标签的内联样式，保证微信公众号编辑器过滤 `<style>` 后仍尽量保留视觉效果。

## 可用主题

| 主题 | 说明 | 使用场景 |
|------|------|----------|
| `classic` | 当前原有样式，红色强调、浅暖背景 | 默认兼容样式 |
| `deepblue` | 参考文章 `https://mp.weixin.qq.com/s/vUL75vlAxkBHhp5Gwqudfg` 的深蓝商务样式 | 企业、AI、管理、咨询类长文 |

## 选择方式

### 文章 Frontmatter

```yaml
---
title: "文章标题"
style: deepblue
---
```

也可以使用 `theme: deepblue`，含义相同。

### 命令行

```bash
./publish.sh your-article.md --style deepblue
```

命令行参数优先级最高，其次是文章 frontmatter，最后是 `config/wechat-credentials.local.md` 中的 `default_style`。如果都未配置，使用 `classic`。

### 全局默认

```yaml
---
default_style: deepblue
---
```

## 主题特征

### classic

这是已保存的原始样式：

- 主色：`#db4c3f`
- 容器：浅暖色 `#fffdf9`，`20px` 内边距，`8px` 圆角
- 标题：H1 居中下划线，H2/H3 红色左边框和虚线下边框
- 正文：`16px` 字号，偏 GitHub Markdown 风格

### deepblue

从参考文章中提取的主要排版特征：

- 主色：`rgb(15, 76, 129)`
- 正文：`14px` 字号，`1.75` 行高，`0.1em` 字间距，`1.5em 8px` 段落边距
- H2：居中深蓝底白字，`display: table`，`8px` 圆角，轻微阴影
- H3：左侧深蓝竖线加深蓝虚线下边框
- 加粗：使用深蓝强调色

## 新增主题时

在 `publish_to_wechat.py` 中新增：

1. 一个 `<style>` 块常量
2. 一个内联样式字典
3. `STYLE_THEMES` 中的主题条目

内联样式字典至少需要包含：`h1`、`h2`、`h3`、`h4`、`strong`、`th`、`td`、`hr`、`list_container`、`list_item`、`pre`、`inline_code`。
