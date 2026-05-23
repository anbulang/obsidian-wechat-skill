# Obsidian 微信公众号发布器

把 Obsidian 风格 Markdown 转成微信公众号草稿箱可用的富文本 HTML，并自动处理图片、视频、Mermaid 图表、Callout、代码高亮、封面和发布接口。

这是一个可直接安装的智能体技能：既可以在命令行里用 `./publish.sh` 发布文章，也可以让 Claude Code、Codex 等智能体在需要“微信公众号排版/发布”时自动调用。

## 亮点

- **Obsidian 优先**：支持 `![[image.png]]`、`![[video.mp4|标题]]`、Callout、Admonition 和文章元数据。
- **微信公众号兼容**：链接自动转脚注，关键样式内联，避免微信编辑器过滤常见 CSS/JavaScript。
- **媒体处理流水线**：本地/远程图片上传到微信图片 CDN，本地 MP4 上传为永久视频素材后在正文中引用。
- **Mermaid 图表渲染**：Mermaid 图表转图片后上传，草稿中无需 JavaScript。
- **封面处理**：支持 `thumb_media_id`、本地/远程封面、默认封面和可选 AI 自动封面。
- **样式主题**：内置 `classic` 和 `deepblue`，可通过文章元数据或命令行切换。
- **草稿箱发布**：自动获取/刷新 `access_token`，调用微信公众号草稿箱接口。
- **兼容 skills.sh**：根目录包含标准 `SKILL.md`，可被 `skills` 命令行工具发现和安装。

## 快速开始

```bash
git clone https://github.com/anbulang/obsidian-wechat-skill.git
cd obsidian-wechat-skill

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

## 作为智能体技能安装

本仓库遵循智能体技能格式，`skills` 命令行工具会发现根目录的 `SKILL.md`。

从 Git 仓库安装：

```bash
npx skills add https://github.com/anbulang/obsidian-wechat-skill.git --skill obsidian-wechat
npx skills add anbulang/obsidian-wechat-skill --skill obsidian-wechat
```

安装到特定智能体：

```bash
npx skills add anbulang/obsidian-wechat-skill --skill obsidian-wechat --agent codex
npx skills add anbulang/obsidian-wechat-skill --skill obsidian-wechat --agent claude-code
```

本地开发时列出可发现的技能：

```bash
npx skills add . --list
```

> 我在本地做了静态兼容性检查：`SKILL.md` 位于仓库根目录，元数据包含 `name: obsidian-wechat` 和 `description`，符合 `skills` 命令行工具的发现要求。实际 `npx skills add . --list` 需要联网下载命令行工具，本环境的安全策略阻止了未固定的 `npx` 远程执行。

## 文章格式

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

### 文章元数据字段

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `title` | 否 | 文章标题；未设置时使用“未命名文章”。 |
| `author` | 否 | 作者；默认来自 `default_author`。 |
| `digest` | 否 | 摘要；也会作为视频简介的候选值。 |
| `thumb_media_id` | 否 | 已上传的封面素材 ID，优先级最高。 |
| `banner` / `cover` / `image` | 否 | 本地或 HTTPS 封面图。 |
| `source_url` | 否 | “阅读原文”链接。 |
| `style` / `theme` | 否 | `classic` 或 `deepblue`。 |
| `video_introduction` | 否 | 视频素材简介；未设置时使用 `digest` 或视频标题。 |
| `open_comment` | 否 | `0` 关闭评论，`1` 开启评论。 |

### 图片与视频

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

## 样式示例

### `deepblue`：深蓝商务长文

对应截图里的蓝色标题块风格：适合 AI、管理、咨询、技术评论类长文。它使用深蓝色作为主强调色，二级标题居中显示为蓝底白字按钮状标题，正文段落更紧凑，适合长篇阅读。

使用方式：

```yaml
---
title: "为什么你的 AI-First 战略大概率是错的"
style: "deepblue"
---
```

示例内容：

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

视觉特征：

- 主色为深蓝
- 二级标题为居中的深蓝底白字标题块
- 三级标题使用左侧深蓝竖线和虚线下边框
- 加粗文本使用深蓝强调
- 正文适合较长段落和图文交替

### `classic`：红色强调知识文

对应截图里的红色标题、浅暖表格和橙色 Question Callout 风格：适合架构设计、技术方案、教程和问答型文章。它保留默认暖色背景，标题和表格强调更明显，适合结构化说明。

使用方式：

```yaml
---
title: "关于统一认证中心设计的思考"
style: "classic"
---
```

示例内容：

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

视觉特征：

- 主色为红色
- Callout 使用浅色背景和醒目的左侧边框
- 表格为浅暖底色，表头和强调文本更突出
- 二级标题使用红色左边框和虚线分隔
- 适合教程、方案、设计文档和问答型内容

## 配置

复制示例配置后修改：

```bash
cp config/wechat-credentials.example.md config/wechat-credentials.local.md
```

核心字段：

| 字段 | 是否必填 | 说明 |
| --- | --- | --- |
| `appid` | 是 | 微信公众号 AppID。 |
| `secret` | 是 | 微信公众号 AppSecret。 |
| `access_token` | 否 | 自动缓存，无需手填。 |
| `token_expires` | 否 | 自动缓存，无需手填。 |
| `default_author` | 否 | 默认作者。 |
| `default_thumb_media_id` | 否 | 默认封面素材 ID。 |
| `default_style` | 否 | 默认样式，`classic` 或 `deepblue`。 |
| `ai_cover` | 否 | 可选 AI 自动封面配置，默认关闭。 |

微信公众号后台还需要配置当前公网 IP 白名单：

```bash
curl -s ifconfig.me
```

## 工作原理

```mermaid
flowchart LR
  A[Markdown 原文] --> B[解析文章元数据]
  B --> C[预处理 Obsidian 语法]
  C --> D[上传图片和视频]
  D --> E[转换为微信 HTML]
  E --> F[解析封面素材 ID]
  F --> G[创建草稿]
```

发布流程：

1. 读取 Markdown，解析文章元数据。
2. 处理 Obsidian 嵌入、Callout、Admonition、Mermaid。
3. 上传正文图片到 `/cgi-bin/media/uploadimg`。
4. 上传正文 MP4 到 `/cgi-bin/material/add_material?type=video`。
5. 生成微信兼容 HTML。
6. 解析或上传封面，获取 `thumb_media_id`。
7. 调用 `/cgi-bin/draft/add` 创建草稿。

## 项目结构

```text
.
├── SKILL.md                         # 技能定义
├── agents/openai.yaml               # 技能客户端可选展示元数据
├── publish_to_wechat.py             # 转换与发布脚本
├── publish.sh                       # Python 脚本的命令行包装
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

## 开发

运行完整测试：

```bash
pytest -q
```

运行媒体相关测试：

```bash
pytest -q test_image_processing.py test_video_processing.py
```

本地验证技能元数据：

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

## 安全说明

- 不要提交 `config/wechat-credentials.local.md`。
- `*.local.md`、虚拟环境、缓存和生成封面缓存已加入忽略规则。
- 远程图片 URL 必须使用 HTTPS，并会检查是否指向内网或本机地址。
- 脚本不会执行 Markdown 内容中的 JavaScript。
- AI 自动封面默认关闭；只有明确配置提供商并设置 `ai_cover.enabled: true` 后才会请求外部生图服务。

## 常见问题

| 现象 | 可能原因 | 解决方式 |
| --- | --- | --- |
| `40164` | 当前 IP 不在微信公众号白名单 | 在微信公众号后台加入当前公网 IP。 |
| `40001` / `42001` | Token 无效或过期 | 脚本会自动刷新一次；若仍失败，检查 `appid` 和 `secret`。 |
| 缺少封面 | 未配置 `thumb_media_id`、封面图、AI 封面或默认封面 | 配置 `default_thumb_media_id` 或添加 `banner`。 |
| 图片上传失败 | 图片格式/大小不支持，或远程 URL 不安全 | 使用 JPG/PNG/GIF，控制大小，并使用公开 HTTPS URL。 |
| 视频上传失败 | 不是本地 MP4，或超过 10MB | 转换并压缩为本地 `.mp4`。 |
| 技能无法被发现 | `SKILL.md` 元数据缺失或无效 | 确保根目录 `SKILL.md` 包含 `name` 和 `description`。 |

## 许可证

MIT。详见 [LICENSE](LICENSE)。
