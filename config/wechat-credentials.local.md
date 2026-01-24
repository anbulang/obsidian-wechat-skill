---
appid: "wx71274cc3191e9890"
secret: "fc882cc380e3673dfa3a44fa35692171"
access_token: ""
token_expires: 0
default_author: "Chaucer"
default_thumb_media_id: "PeAJK_viCcf8q7R1gKlTu5CAjuLlWVxBvvLbaq2FiCeGJZRHeZYWSrdS_jx8orOG"
---
# 微信公众号凭证配置

> **安全提示**: 此文件包含敏感凭证，请勿提交到 Git 仓库！

## 配置说明

### 必填项

| 字段  | 说明             | 获取方式                             |
| ----- | ---------------- | ------------------------------------ |
| appid | 公众号 AppID     | 公众号后台 → 设置与开发 → 基本配置 |
| appid | 公众号 AppSecret | 同上，需管理员扫码确认               |

### 可选项

| 字段                   | 说明           | 用途                     |
| ---------------------- | -------------- | ------------------------ |
| access_token           | 缓存的访问令牌 | 自动填充，无需手动设置   |
| token_expires          | 令牌过期时间戳 | 自动填充，无需手动设置   |
| default_author         | 默认作者名     | 文章未指定 author 时使用 |
| default_thumb_media_id | 默认封面图 ID  | 文章未指定封面时使用     |

## 配置步骤

1. **获取 AppID 和 AppSecret**

   - 登录 [微信公众平台](https://mp.weixin.qq.com)
   - 进入「设置与开发」→「基本配置」
   - 复制 AppID（开发者ID）
   - 点击重置 AppSecret 并保存
2. **配置 IP 白名单**

   - 在同一页面找到「IP白名单」
   - 添加你的公网 IP：
     ```bash
     curl -s ifconfig.me
     ```
3. **填写凭证**

   - 将上方 frontmatter 中的 `your_appid_here` 替换为实际 AppID
   - 将 `your_secret_here` 替换为实际 AppSecret

## 上传默认封面图

如需设置默认封面，先上传一张图片获取 media_id：

```bash
# 1. 获取 token
TOKEN=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=YOUR_APPID&secret=YOUR_SECRET" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

# 2. 上传封面图
curl -s -X POST \
  "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${TOKEN}&type=image" \
  -F "media=@/path/to/cover.jpg"
```

将返回的 `media_id` 填入上方的 `default_thumb_media_id`。

## 验证配置

运行以下命令测试配置是否正确：

```bash
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=YOUR_APPID&secret=YOUR_SECRET"
```

成功响应示例：

```json
{"access_token":"xxx","expires_in":7200}
```

如果返回错误码 40164，说明 IP 白名单未配置。
