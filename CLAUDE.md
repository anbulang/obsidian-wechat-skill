# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Claude Code Skill，用于将 Obsidian Flavored Markdown 转换为微信公众号兼容的富文本 HTML，并支持一键发布到草稿箱。

## 触发方式

用户通过以下方式触发此 Skill：
- "把这篇文章转换成微信公众号格式"
- "生成公众号 HTML"
- "发布到微信公众号草稿箱"
- 提到"微信公众号排版"

## 架构说明

- **SKILL.md** - 主技能定义，包含完整的转换规则和工作流程
- **references/** - 参考文档（类型映射、CSS 样式、Mermaid 处理、API 指南）
- **config/wechat-credentials.local.md** - 本地凭证配置（敏感，勿提交）

## 关键转换规则

### Admonition 类型映射
查阅 `references/admonition-mapping.md` 获取完整的类型别名映射（如 `tldr`→`abstract`、`hint`→`tip`）和对应的 Lucide SVG 图标。

### CSS 样式
所有样式基于 `#nice` 选择器体系，参考 `references/wechat-css-styles.md`。由于微信可能过滤 `<style>` 标签，关键样式需内联。

### Mermaid 处理
使用 mermaid.ink API：`https://mermaid.ink/img/{base64编码的图表定义}`

## 微信 API 工作流

```
读取 MD → 解析 frontmatter → 获取 access_token → 上传图片 → 处理封面 → MD→HTML → draft/add API
```

关键 API 端点（Base URL: `https://api.weixin.qq.com`）：
- `/cgi-bin/token` - 获取 access_token
- `/cgi-bin/media/uploadimg` - 上传文章内图片
- `/cgi-bin/material/add_material` - 上传封面（永久素材）
- `/cgi-bin/draft/add` - 创建草稿

## 微信兼容性注意事项

- 避免使用 `position: fixed/sticky`、`animation`、`filter`、`clip-path`
- 不支持 JavaScript
- 图片使用 `max-width: 100%`
- 超链接必须转为脚注格式
- 封面图推荐尺寸：900x383 或 2.35:1 比例
