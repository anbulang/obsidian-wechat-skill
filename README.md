# Obsidian WeChat Publisher

把 Obsidian Flavored Markdown 转成微信公众号草稿箱可用的富文本 HTML，并自动处理图片、视频、Mermaid、Callout、代码高亮、封面和发布 API。

这是一个可直接安装的 Agent Skill：既可以在命令行里用 `./publish.sh` 发布文章，也可以让 Claude Code、Codex 等 agent 在需要“微信公众号排版/发布”时自动调用。

## Highlights

- **Obsidian-first**: 支持 `![[image.png]]`、`![[video.mp4|标题]]`、Callout、Admonition、Frontmatter。
- **WeChat-ready HTML**: 链接转脚注，样式内联，避免微信编辑器过滤常见 CSS/JS。
- **Media pipeline**: 本地/远程图片上传到微信 CDN，本地 MP4 上传为永久视频素材后在正文中引用。
- **Mermaid rendering**: Mermaid 图表转图片后上传，草稿中无需 JavaScript。
- **Cover handling**: 支持 `thumb_media_id`、本地/远程封面、默认封面和可选 AI 自动封面。
- **Style themes**: 内置 `classic` 和 `deepblue`，可通过 Frontmatter 或 CLI 切换。
- **Draft publishing**: 自动获取/刷新 `access_token`，调用微信公众号草稿箱 API。
- **skills.sh compatible**: 根目录包含标准 `SKILL.md`，可被 `skills` CLI 发现和安装。

## Quick Start

```bash
git clone <repo-url>
cd obsidian-wechat

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config/wechat-credentials.example.md config/wechat-credentials.local.md
```

编辑 `config/wechat-credentials.local.md`，填入微信公众号 `appid` 和 `secret`，然后发布：

```bash
./publish.sh path/to/article.md
```

指定样式主题：

```bash
./publish.sh path/to/article.md --style deepblue
```

## Install As A Skill

本仓库遵循 Agent Skills 格式，`skills` CLI 会发现根目录的 `SKILL.md`。

从 Git 仓库安装：

```bash
npx skills add <git-url> --skill obsidian-wechat
npx skills add <owner>/<repo> --skill obsidian-wechat
```

安装到特定 agent：

```bash
npx skills add <owner>/<repo> --skill obsidian-wechat --agent codex
npx skills add <owner>/<repo> --skill obsidian-wechat --agent claude-code
```

本地开发时列出可发现的 skill：

```bash
npx skills add . --list
```

> 我在本地做了静态兼容性检查：`SKILL.md` 位于仓库根目录，frontmatter 包含 `name: obsidian-wechat` 和 `description`，符合 `skills` CLI 的发现要求。实际 `npx skills add . --list` 需要联网下载 CLI，本环境的安全策略阻止了未固定的 `npx` 远程执行。

## Article Format

最小示例：

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

### Frontmatter

| Field | Required | Description |
| --- | --- | --- |
| `title` | No | 文章标题；未设置时使用“未命名文章”。 |
| `author` | No | 作者；默认来自 `default_author`。 |
| `digest` | No | 摘要；也会作为视频简介的候选值。 |
| `thumb_media_id` | No | 已上传的封面素材 ID，优先级最高。 |
| `banner` / `cover` / `image` | No | 本地或 HTTPS 封面图。 |
| `source_url` | No | “阅读原文”链接。 |
| `style` / `theme` | No | `classic` 或 `deepblue`。 |
| `video_introduction` | No | 视频素材简介；未设置时使用 `digest` 或视频标题。 |
| `open_comment` | No | `0` 关闭评论，`1` 开启评论。 |

### Media

图片：

```markdown
![[image.png]]
![[folder/image.webp|图片说明]]
![图片说明](https://example.com/image.png)
```

视频：

```markdown
![[demo.mp4|视频标题]]
![视频标题](demo.mp4)
```

视频限制：

- 仅支持本地 `.mp4`
- 微信永久视频素材限制为 10MB
- 远程视频 URL 不会自动下载上传
- `.mov`、`.webm` 等会被识别为视频，但会明确报错，避免误走图片上传

## Configuration

复制示例配置后修改：

```bash
cp config/wechat-credentials.example.md config/wechat-credentials.local.md
```

核心字段：

| Field | Required | Description |
| --- | --- | --- |
| `appid` | Yes | 微信公众号 AppID。 |
| `secret` | Yes | 微信公众号 AppSecret。 |
| `access_token` | No | 自动缓存，无需手填。 |
| `token_expires` | No | 自动缓存，无需手填。 |
| `default_author` | No | 默认作者。 |
| `default_thumb_media_id` | No | 默认封面素材 ID。 |
| `default_style` | No | 默认样式，`classic` 或 `deepblue`。 |
| `ai_cover` | No | 可选 AI 自动封面配置，默认关闭。 |

微信公众号后台还需要配置当前公网 IP 白名单：

```bash
curl -s ifconfig.me
```

## How It Works

```mermaid
flowchart LR
  A[Markdown] --> B[Parse frontmatter]
  B --> C[Preprocess Obsidian syntax]
  C --> D[Upload images and videos]
  D --> E[Convert Markdown to WeChat HTML]
  E --> F[Resolve cover media_id]
  F --> G[Create draft]
```

发布流程：

1. 读取 Markdown，解析 Frontmatter。
2. 处理 Obsidian 嵌入、Callout、Admonition、Mermaid。
3. 上传正文图片到 `/cgi-bin/media/uploadimg`。
4. 上传正文 MP4 到 `/cgi-bin/material/add_material?type=video`。
5. 生成微信兼容 HTML。
6. 解析或上传封面，获取 `thumb_media_id`。
7. 调用 `/cgi-bin/draft/add` 创建草稿。

## Project Structure

```text
.
├── SKILL.md                         # Agent Skill definition
├── agents/openai.yaml               # Optional UI metadata for skill-aware clients
├── publish_to_wechat.py             # Converter and publisher
├── publish.sh                       # Thin wrapper around the Python script
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

Run the test suite:

```bash
pytest -q
```

Run focused tests:

```bash
pytest -q test_image_processing.py test_video_processing.py
```

Validate skill frontmatter locally:

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
- `*.local.md`, virtual environments, caches, and generated cover cache are ignored.
- Remote image URLs must be HTTPS and are checked to avoid private/loopback hosts.
- The script does not execute JavaScript from Markdown content.
- AI cover generation is opt-in; set `ai_cover.enabled: true` only after configuring a provider intentionally.

## Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `40164` | IP not in WeChat whitelist | Add your public IP in WeChat Official Account settings. |
| `40001` / `42001` | Token invalid or expired | The script refreshes once automatically; check `appid/secret` if it persists. |
| Missing cover | No `thumb_media_id`, cover, AI cover, or default cover | Configure `default_thumb_media_id` or add `banner`. |
| Image upload failed | Unsupported/oversized image or unsafe URL | Use JPG/PNG/GIF, keep under WeChat limits, or use HTTPS public URLs. |
| Video upload failed | Not local MP4 or over 10MB | Convert/compress to local `.mp4`. |
| Skill not found by CLI | Invalid/missing `SKILL.md` frontmatter | Ensure `name` and `description` exist in root `SKILL.md`. |

## License

MIT. See [LICENSE](LICENSE).
