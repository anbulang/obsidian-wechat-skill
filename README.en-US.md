

# Obsidian WeChat Official Account Publisher

Converts Obsidian-style Markdown into rich-text HTML compatible with WeChat Official Account drafts, automatically handling images, videos, Mermaid charts, Callouts, code highlighting, cover images, and the publishing API.

This is a ready-to-install agent skill: you can publish articles directly via the command line using `./publish.sh`, or allow agents like Claude Code and Codex to automatically invoke it when "WeChat Official Account formatting/publishing" is needed.

## Highlights

- **Obsidian-First**: Supports `![[image.png]]`, `![[video.mp4|Title]]`, Callouts, Admonitions, and article metadata.
- **WeChat Official Account Compatible**: Links are automatically converted to footnotes, critical styles are inlined to prevent the WeChat editor from filtering common CSS/JavaScript.
- **Media Processing Pipeline**: Local/remote images are uploaded to WeChat's image CDN; local MP4s are uploaded as permanent video assets and then referenced in the body.
- **Mermaid Chart Rendering**: Mermaid charts are converted to images and uploaded, so no JavaScript is needed in the draft.
- **Cover Image Handling**: Supports `thumb_media_id`, local/remote covers, default covers, and optional AI-generated covers.
- **Style Themes**: Built-in `classic` and `deepblue` themes, switchable via article metadata or command line.
- **Draft Publishing**: Automatically fetches/refreshes `access_token` and calls the WeChat Official Account draft API.
- **Compatible with skills.sh**: The root directory includes a standard `SKILL.md`, discoverable and installable via the `skills` CLI tool.

## Quick Start

```bash
git clone https://github.com/anbulang/obsidian-wechat-skill.git
cd obsidian-wechat-skill

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config/wechat-credentials.example.md config/wechat-credentials.local.md
```

Edit `config/wechat-credentials.local.md` to fill in your WeChat Official Account `appid` and `secret`, then publish:

```bash
./publish.sh path/to/article.md
```

Specify a style theme:

```bash
./publish.sh path/to/article.md --style deepblue
```

## Install as Skill

This repository follows the agent skill format, and the `skills` CLI tool will discover the `SKILL.md` in the root directory.

1. Install from a Git repository:

```bash
npx skills add https://github.com/anbulang/obsidian-wechat-skill.git --skill obsidian-wechat
npx skills add anbulang/obsidian-wechat-skill --skill obsidian-wechat
```

2. To install for a specific agent:

```bash
npx skills add anbulang/obsidian-wechat-skill --skill obsidian-wechat --agent codex
npx skills add anbulang/obsidian-wechat-skill --skill obsidian-wechat --agent claude-code
```

3. Configure WeChat Official Account credentials. Navigate to the installed skill directory and copy the example config:

```bash
cp config/wechat-credentials.example.md config/wechat-credentials.local.md
```

Edit `config/wechat-credentials.local.md` and fill in the WeChat Official Account `appid` and `secret`. Without local credentials, the skill can still be used to convert HTML, but cannot publish to drafts.

List discoverable skills during local development:

```bash
npx skills add . --list
```

> I performed a static compatibility check locally: `SKILL.md` is located in the root directory, and the metadata includes `name: obsidian-wechat` and `description`, meeting the discovery requirements of the `skills` CLI tool. Actually running `npx skills add . --list` requires downloading the CLI tool online, which is blocked by the security policy of this environment due to unfixed `npx` remote execution.

## Article Format

Minimal example:

```markdown
---
title: "文章标题"
author: "作者名"
digest: "摘要会显示在草稿列表中"
banner: "cover.jpg"
style: "deepblue"
---

# 标题

正文内容。

![[images/demo.png|配图说明]]

![[clips/demo.mp4|演示视频]]
```

### Article Metadata Fields

| Field                                  | Required | Description                                                       |
| -------------------------------------- | -------- | ----------------------------------------------------------------- |
| `title`                              | No       | Article title; defaults to "Untitled Article" if not set.         |
| `author`                             | No       | Author; defaults to `default_author`.                             |
| `digest`                             | No       | Summary; also used as a candidate for video descriptions.         |
| `thumb_media_id`                     | No       | ID of an already uploaded cover asset; highest priority.          |
| `banner` / `cover` / `image`     | No       | Local or HTTPS cover image.                                       |
| `source_url`                         | No       | "Read Original" link.                                             |
| `style` / `theme`                  | No       | `classic` or `deepblue`.                                          |
| `video_introduction`                 | No       | Video asset description; falls back to `digest` or video title.   |
| `open_comment`                       | No       | `0` to disable comments, `1` to enable comments.                  |

### Images & Videos

Images:

```markdown
![[image.png]]
![[folder/image.webp|Image Caption]]
![Image Caption](https://example.com/image.png)
```

Videos:

```markdown
![[demo.mp4|Video Title]]
![Video Title](demo.mp4)
![Tencent Video](https://v.qq.com/x/page/a0189rvrjbi.html)
```

Video Limitations:

- Only local `.mp4` files are supported.
- WeChat permanent video assets are limited to 10MB.
- Remote video URLs will not be automatically downloaded or uploaded.
- Formats like `.mov` and `.webm` are recognized as videos but will explicitly error out to prevent accidental upload via the image pipeline.
- After uploading a local MP4, a visible asset card and `media_id` are retained in the body; the WeChat draft API does not guarantee automatic rendering of the asset library `media_id` into a player.
- To automatically display a player in the draft, it is recommended to use Tencent Video links, which the script will convert to the common WeChat `video_iframe`.

## Style Examples

### `deepblue`: Deep Blue Business Long-Form

Matches the blue heading block style in the screenshot: ideal for long-form articles on AI, management, consulting, and tech reviews. It uses deep blue as the primary accent color, displays H2 headings as centered blue-background white-text button-style titles, and features tighter body paragraphs for extended reading.

Usage:

```yaml
---
title: "为什么你的 AI-First 战略大概率是错的"
style: "deepblue"
---
```

Example content:

```markdown
> [!info]
> 原文：Peter Pang《Why Your AI-First Strategy Is Probably Wrong》
> 链接：https://x.com/intuitiveml/status/204354596699750791

## 开头：一天完成过去六周的产品循环

上周三上午 10 点，团队上线了一个新功能。

这也是这篇文章最值得讨论的地方：
**AI-first 不是使用 AI。AI-first 是围绕 AI 重建组织。**

## 一、AI-assisted 和 AI-first 是两回事

很多公司说自己 AI-first，其实只是 AI-assisted。
```

Visual characteristics:

- Primary color is deep blue
- H2 headings are centered deep-blue background white-text blocks
- H3 headings feature a left deep-blue vertical line and a dashed bottom border
- Bold text is emphasized in deep blue
- Body text is optimized for longer paragraphs and alternating image/text layouts

### `classic`: Red Accent Knowledge Article

Matches the red heading, light warm table, and orange Question Callout style in the screenshot: suitable for architecture design, technical solutions, tutorials, and Q&A articles. It retains a default warm background with more pronounced heading and table emphasis, ideal for structured explanations.

Usage:

```yaml
---
title: "关于统一认证中心设计的思考"
style: "classic"
---
```

Example content:

```markdown
> [!question] Question
> 如果使用 OAuth 2.0 协议来设计一个公司内部的单点登录系统？
> 用户入口主要是“XX通 APP”，通过 XX 通登录到集成门户。

## 一、核心概念映射

| 实体 | 角色 | 说明 |
| --- | --- | --- |
| XX通 APP | 外部 IdP | 整个链路的信任源头，负责用户初次实名认证。 |
| 集成门户 | Client 与 IdP | 对外信任 XX 通，对内签发访问令牌。 |
| 内部业务系统 | Resource Server | OA、HR、财务等业务应用。 |

## 二、总体架构设计

建议采用 BFF 或独立 IAM 服务模式。
```

Visual characteristics:

- Primary color is red
- Callouts use a light background with a prominent left border
- Tables have a light warm background, with more prominent headers and emphasized text
- H2 headings feature a red left border and dashed separators
- Ideal for tutorials, solutions, design documents, and Q&A content

## Configuration

Copy and modify the example configuration:

```bash
cp config/wechat-credentials.example.md config/wechat-credentials.local.md
```

Core fields:

| Field                        | Required | Description                                    |
| ---------------------------- | -------- | ---------------------------------------------- |
| `appid`                    | Yes      | WeChat Official Account AppID.                 |
| `secret`                   | Yes      | WeChat Official Account AppSecret.             |
| `access_token`             | No       | Auto-cached; no manual input required.         |
| `token_expires`            | No       | Auto-cached; no manual input required.         |
| `default_author`           | No       | Default author.                                |
| `default_thumb_media_id`   | No       | Default cover asset ID.                        |
| `default_style`            | No       | Default style, `classic` or `deepblue`.        |
| `ai_cover`                 | No       | Optional AI auto-cover configuration, disabled by default. |

You also need to whitelist your current public IP in the WeChat Official Account backend:

```bash
curl -s ifconfig.me
```

## How It Works

```mermaid
flowchart LR
  A[Markdown 原文] --> B[解析文章元数据]
  B --> C[预处理 Obsidian 语法]
  C --> D[上传图片和视频]
  D --> E[转换为微信 HTML]
  E --> F[解析封面素材 ID]
  F --> G[创建草稿]
```

Publishing workflow:

1. Read Markdown and parse article metadata.
2. Process Obsidian embeds, Callouts, Admonitions, and Mermaid.
3. Upload body images to `/cgi-bin/media/uploadimg`.
4. Upload body MP4s to `/cgi-bin/material/add_material?type=video`.
5. Generate WeChat-compatible HTML.
6. Parse or upload the cover image to obtain `thumb_media_id`.
7. Call `/cgi-bin/draft/add` to create the draft.

## Project Structure

```text
.
├── SKILL.md                         # Skill definition
├── agents/openai.yaml               # Optional display metadata for skill clients
├── publish_to_wechat.py             # Conversion and publishing script
├── publish.sh                       # CLI wrapper for the Python script
├── config/
│   └── wechat-credentials.example.md
├── references/
│   ├── admonition-mapping.md
│   ├── mermaid-handling.md
│   ├── style-themes.md
│   ├── wechat-api.md
│   └── wechat-css-styles.md
└── test_*.py
```

## Development

Run full tests:

```bash
pytest -q
```

Run media-related tests:

```bash
pytest -q test_image_processing.py test_video_processing.py
```

Validate skill metadata locally:

```bash
.venv/bin/python3 - <<'PY'
from pathlib import Path
import yaml

text = Path("SKILL.md").read_text()
_, frontmatter, _ = text.split("---", 2)
data = yaml.safe_load(frontmatter)
assert data["name"] == "obsidian-wechat"
assert data["description"]
print("SKILL.md frontmatter OK")
PY
```

## Security Notes

- Do not commit `config/wechat-credentials.local.md`.
- `*.local.md`, virtual environments, caches, and generated cover caches are added to ignore rules.
- Remote image URLs must use HTTPS and are checked to ensure they do not point to intranet or localhost addresses.
- The script will not execute JavaScript embedded in Markdown content.
- AI auto-cover is disabled by default; external image generation services are only requested when a provider is explicitly configured and `ai_cover.enabled: true` is set.

## FAQ

| Symptom             | Possible Cause                                      | Solution                                                       |
| ------------------- | --------------------------------------------------- | -------------------------------------------------------------- |
| `40164`           | Current IP is not in the WeChat Official Account whitelist. | Add your current public IP in the WeChat Official Account backend. |
| `40001` / `42001` | Invalid or expired token.                           | The script will auto-refresh once; if it still fails, check `appid` and `secret`. |
| Missing cover       | `thumb_media_id`, cover image, AI cover, or default cover not configured. | Configure `default_thumb_media_id` or add a `banner`.       |
| Image upload failed | Unsupported image format/size, or insecure remote URL. | Use JPG/PNG/GIF, keep file size within limits, and use a public HTTPS URL. |
| Video upload failed | Not a local MP4, or exceeds 10MB.                   | Convert and compress to a local `.mp4`.                      |
| Skill not discovered | `SKILL.md` metadata missing or invalid.           | Ensure root `SKILL.md` contains `name` and `description`.   |

## License

MIT. See [LICENSE](LICENSE) for details.
