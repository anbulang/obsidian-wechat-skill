# Obsidian WeChat Publisher

[English](#english) | [中文](#中文)

---

## English

A Claude Code Skill that converts Obsidian Markdown to WeChat-compatible HTML and publishes directly to WeChat Official Account drafts.

### Features

- **Obsidian Flavored Markdown** → WeChat-compatible rich HTML
- **Admonition/Callout Support** - `ad-*` code blocks and `> [!type]` syntax
- **Mermaid Diagrams** - Auto-rendered via mermaid.ink API
- **Syntax Highlighting** - Pygments-based code highlighting with line numbers
- **Auto Footnotes** - Links automatically converted to footnotes (WeChat doesn't support clickable links)
- **Smart Cover Images** - Unsplash integration with Chinese keyword translation
- **One-Click Publish** - Direct publish to WeChat drafts via API

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/obsidian-wechat.git
   cd obsidian-wechat
   ```

2. **Install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure credentials**
   ```bash
   cp config/wechat-credentials.example.md config/wechat-credentials.local.md
   # Edit the file with your WeChat AppID and Secret
   ```

4. **Publish an article**
   ```bash
   ./publish.sh your-article.md
   ```

### Configuration

Edit `config/wechat-credentials.local.md`:

| Field | Required | Description |
|-------|----------|-------------|
| `appid` | Yes | WeChat Official Account AppID |
| `secret` | Yes | WeChat Official Account AppSecret |
| `default_author` | No | Default author name |
| `default_thumb_media_id` | No | Default cover image media ID |
| `unsplash_access_key` | No | Unsplash API key for auto cover |
| `enable_auto_cover` | No | Enable auto cover image from Unsplash |

### Article Frontmatter

```yaml
---
title: "Article Title"
author: "Author Name"
banner: "https://example.com/cover.jpg"  # or local path
digest: "Article summary"
---
```

### WeChat API Setup

1. Login to [WeChat Official Account Platform](https://mp.weixin.qq.com)
2. Go to **Settings & Development** → **Basic Configuration**
3. Copy your AppID and reset AppSecret
4. Add your public IP to the whitelist:
   ```bash
   curl -s ifconfig.me
   ```

### Using as Claude Code Skill

This project is a [Claude Code Skill](https://docs.anthropic.com/en/docs/claude-code). To use it:

1. **Install the skill** - Copy this folder to your Claude Code skills directory
2. **Trigger the skill** - Use natural language commands:
   - "Convert this article to WeChat format"
   - "Publish to WeChat drafts"
   - "Generate WeChat HTML"
3. **Claude will automatically**:
   - Read and parse your Markdown file
   - Convert to WeChat-compatible HTML
   - Upload images and publish to drafts

---

## 中文

一个 Claude Code Skill，将 Obsidian Markdown 转换为微信公众号兼容的 HTML，并支持一键发布到草稿箱。

### 功能特性

- **Obsidian 风格 Markdown** → 微信兼容富文本 HTML
- **Admonition/Callout 支持** - `ad-*` 代码块和 `> [!type]` 语法
- **Mermaid 图表** - 通过 mermaid.ink API 自动渲染
- **语法高亮** - 基于 Pygments 的代码高亮（带行号）
- **自动脚注** - 链接自动转换为脚注（微信不支持可点击链接）
- **智能封面图** - Unsplash 集成，支持中文关键词自动翻译
- **一键发布** - 通过 API 直接发布到微信草稿箱

### 快速开始

1. **克隆仓库**
   ```bash
   git clone https://github.com/yourusername/obsidian-wechat.git
   cd obsidian-wechat
   ```

2. **安装依赖**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **配置凭证**
   ```bash
   cp config/wechat-credentials.example.md config/wechat-credentials.local.md
   # 编辑文件，填入你的微信 AppID 和 Secret
   ```

4. **发布文章**
   ```bash
   ./publish.sh your-article.md
   ```

### 配置说明

编辑 `config/wechat-credentials.local.md`：

| 字段 | 必填 | 说明 |
|------|------|------|
| `appid` | 是 | 微信公众号 AppID |
| `secret` | 是 | 微信公众号 AppSecret |
| `default_author` | 否 | 默认作者名 |
| `default_thumb_media_id` | 否 | 默认封面图素材 ID |
| `unsplash_access_key` | 否 | Unsplash API 密钥（自动封面） |
| `enable_auto_cover` | 否 | 启用 Unsplash 自动封面 |

### 文章 Frontmatter

```yaml
---
title: "文章标题"
author: "作者名"
banner: "https://example.com/cover.jpg"  # 或本地路径
digest: "文章摘要"
---
```

### 自动封面功能

当文章没有指定封面时，系统会：

1. 从文章标题/内容提取关键词
2. 使用三层降级策略翻译中文关键词：
   - 内置字典快速匹配
   - Google 翻译 API
   - 随机分类（nature, technology, business 等）
3. 调用 Unsplash API 搜索匹配图片
4. 自动下载并上传到微信素材库

### 微信 API 配置

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入 **设置与开发** → **基本配置**
3. 复制 AppID，重置 AppSecret
4. 添加公网 IP 到白名单：
   ```bash
   curl -s ifconfig.me
   ```

### 错误处理

| 错误码 | 原因 | 解决方案 |
|--------|------|----------|
| 40164 | IP 不在白名单 | 添加公网 IP 到白名单 |
| 40001 | Token 无效 | 重新获取 access_token |
| 45009 | 调用超限 | 等待后重试 |

### 作为 Claude Code Skill 使用

本项目是一个 [Claude Code Skill](https://docs.anthropic.com/en/docs/claude-code)。使用方法：

1. **安装 Skill** - 将此文件夹复制到 Claude Code skills 目录
2. **触发 Skill** - 使用自然语言命令：
   - "把这篇文章转换成微信公众号格式"
   - "发布到微信公众号草稿箱"
   - "生成公众号 HTML"
   - 提到"微信公众号排版"
3. **Claude 会自动**：
   - 读取并解析 Markdown 文件
   - 转换为微信兼容 HTML
   - 上传图片并发布到草稿箱

**Skill 目录结构：**

```
~/.claude/skills/obsidian-wechat/
├── SKILL.md          # Skill 定义（必需）
├── config/           # 凭证配置
├── references/       # 参考文档
└── publish_to_wechat.py  # 发布脚本
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Issues and Pull Requests are welcome!
