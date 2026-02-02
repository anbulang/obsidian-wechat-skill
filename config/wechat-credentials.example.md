---
appid: "your_appid_here"
secret: "your_secret_here"
access_token: ""
token_expires: 0
default_author: "作者名"
default_thumb_media_id: ""
# Unsplash 自动封面配置（可选）
unsplash_access_key: ""
enable_auto_cover: true
---
# 微信公众号凭证配置示例

> **重要**: 复制此文件为 `wechat-credentials.local.md` 并填入真实凭证。
> `*.local.md` 文件已加入 `.gitignore`，不会被提交到 Git 仓库。

## 配置说明

### 必填项

| 字段   | 说明             | 获取方式                             |
| ------ | ---------------- | ------------------------------------ |
| appid  | 公众号 AppID     | 公众号后台 → 设置与开发 → 基本配置 |
| secret | 公众号 AppSecret | 同上，需管理员扫码确认               |

### 可选项

| 字段                   | 说明           | 用途                     |
| ---------------------- | -------------- | ------------------------ |
| access_token           | 缓存的访问令牌 | 自动填充，无需手动设置   |
| token_expires          | 令牌过期时间戳 | 自动填充，无需手动设置   |
| default_author         | 默认作者名     | 文章未指定 author 时使用 |
| default_thumb_media_id | 默认封面图 ID  | 文章未指定封面时使用     |
| unsplash_access_key    | Unsplash API 密钥 | 自动封面功能             |
| enable_auto_cover      | 启用自动封面   | true/false               |

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

3. **创建本地配置**
   ```bash
   cp config/wechat-credentials.example.md config/wechat-credentials.local.md
   ```

4. **填写凭证**
   - 编辑 `wechat-credentials.local.md`
   - 将 `your_appid_here` 替换为实际 AppID
   - 将 `your_secret_here` 替换为实际 AppSecret

## 验证配置

```bash
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=YOUR_APPID&secret=YOUR_SECRET"
```

成功响应：
```json
{"access_token":"xxx","expires_in":7200}
```

如果返回错误码 40164，说明 IP 白名单未配置。

## Unsplash 自动封面（可选）

1. 访问 [Unsplash Developers](https://unsplash.com/developers)
2. 创建应用获取 Access Key
3. 填入 `unsplash_access_key` 字段
4. 设置 `enable_auto_cover: true`
