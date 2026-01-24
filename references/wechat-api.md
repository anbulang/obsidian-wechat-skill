# 微信公众号 API 调用指南

本文档描述如何通过 curl 命令调用微信公众号 API，实现一键发布到草稿箱。

## API 端点概览

| 功能 | 端点 | 方法 |
|------|------|------|
| 获取 access_token | `/cgi-bin/token` | GET |
| 上传文章内图片 | `/cgi-bin/media/uploadimg` | POST |
| 上传永久素材 | `/cgi-bin/material/add_material` | POST |
| 创建草稿 | `/cgi-bin/draft/add` | POST |

**Base URL**: `https://api.weixin.qq.com`

---

## 1. 获取 access_token

### 请求

```bash
curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${APPID}&secret=${SECRET}"
```

### 响应

```json
{
  "access_token": "ACCESS_TOKEN",
  "expires_in": 7200
}
```

### 错误响应

```json
{
  "errcode": 40001,
  "errmsg": "invalid credential, access_token is invalid or not latest"
}
```

### 缓存策略

- access_token 有效期 7200 秒（2小时）
- 建议在 `wechat-credentials.local.md` 中缓存 token 和过期时间
- 每次调用前检查是否过期，过期则重新获取

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 40001 | AppSecret 错误 | 检查 secret 配置 |
| 40164 | IP 不在白名单 | 添加本机公网 IP 到白名单 |
| 40013 | AppID 无效 | 检查 appid 配置 |

---

## 2. 上传文章内图片

文章正文中的图片需要先上传到微信服务器，获取微信 CDN URL。

### 请求

```bash
curl -s -X POST \
  "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${TOKEN}" \
  -F "media=@/path/to/image.png"
```

### 响应

```json
{
  "url": "https://mmbiz.qpic.cn/mmbiz_png/xxx/0?wx_fmt=png"
}
```

### 注意事项

- 支持格式：jpg, png, gif（不支持 webp）
- 图片大小：不超过 10MB
- 返回的 URL 永久有效，无需素材 ID
- 适用于文章正文中的配图

---

## 3. 上传封面图（永久素材）

封面图需要作为永久素材上传，获取 media_id。

### 请求

```bash
curl -s -X POST \
  "https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${TOKEN}&type=image" \
  -F "media=@/path/to/cover.jpg"
```

### 响应

```json
{
  "media_id": "MEDIA_ID",
  "url": "https://mmbiz.qpic.cn/..."
}
```

### 注意事项

- 封面图推荐尺寸：900x383 或 2.35:1 比例
- 大图展示需要宽度 > 400px
- media_id 是永久有效的

---

## 4. 创建草稿

### 请求

```bash
curl -s -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${TOKEN}" \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "articles": [
    {
      "title": "文章标题",
      "author": "作者名",
      "digest": "文章摘要，不填则自动截取正文前54字",
      "content": "<p>HTML内容</p>",
      "thumb_media_id": "封面图的media_id",
      "need_open_comment": 0,
      "only_fans_can_comment": 0,
      "content_source_url": "原文链接（可选）"
    }
  ]
}
EOF
```

### 响应

```json
{
  "media_id": "DRAFT_MEDIA_ID"
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| title | 是 | 文章标题，64字以内 |
| author | 否 | 作者名，8字以内 |
| digest | 否 | 摘要，不填自动截取 |
| content | 是 | HTML 正文内容 |
| thumb_media_id | 是 | 封面图素材 ID |
| need_open_comment | 否 | 0-关闭评论，1-开启 |
| content_source_url | 否 | "阅读原文"链接 |

---

## 完整发布流程

### Shell 脚本示例

```bash
#!/bin/bash

# 配置
APPID="your_appid"
SECRET="your_secret"
ARTICLE_FILE="article.md"

# 1. 获取 access_token
echo "获取 access_token..."
RESPONSE=$(curl -s "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${APPID}&secret=${SECRET}")
TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "获取 token 失败: $RESPONSE"
  exit 1
fi
echo "Token 获取成功"

# 2. 上传图片（如有本地图片）
# UPLOAD_RESPONSE=$(curl -s -X POST \
#   "https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token=${TOKEN}" \
#   -F "media=@/path/to/image.png")
# IMG_URL=$(echo $UPLOAD_RESPONSE | grep -o '"url":"[^"]*"' | cut -d'"' -f4)

# 3. 创建草稿
echo "创建草稿..."
DRAFT_RESPONSE=$(curl -s -X POST \
  "https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "articles": [{
      "title": "测试文章",
      "author": "作者",
      "content": "<p>这是测试内容</p>",
      "thumb_media_id": "YOUR_THUMB_MEDIA_ID"
    }]
  }')

MEDIA_ID=$(echo $DRAFT_RESPONSE | grep -o '"media_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$MEDIA_ID" ]; then
  echo "创建草稿失败: $DRAFT_RESPONSE"
  exit 1
fi

echo "草稿创建成功！media_id: $MEDIA_ID"
echo "请登录公众号后台 -> 草稿箱 查看"
```

---

## 错误处理

### 通用错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| -1 | 系统繁忙 | 重试 |
| 40001 | access_token 无效 | 重新获取 token |
| 40004 | 无效媒体类型 | 检查文件格式 |
| 40009 | 图片大小超限 | 压缩到 10MB 以内 |
| 45009 | 接口调用超限 | 等待后重试 |
| 45157 | 标题包含敏感词 | 修改标题 |
| 45166 | 内容包含敏感词 | 修改内容 |

### 重试策略

```bash
# 带重试的 curl 请求
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  RESPONSE=$(curl -s --connect-timeout 10 --max-time 30 "$URL")
  ERRCODE=$(echo $RESPONSE | grep -o '"errcode":[0-9]*' | cut -d':' -f2)

  if [ "$ERRCODE" = "" ] || [ "$ERRCODE" = "0" ]; then
    break
  fi

  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "请求失败，重试 $RETRY_COUNT/$MAX_RETRIES..."
  sleep 2
done
```

---

## IP 白名单配置

1. 登录公众号后台
2. 设置与开发 → 基本配置 → IP 白名单
3. 添加你的公网 IP

### 获取本机公网 IP

```bash
curl -s ifconfig.me
# 或
curl -s ipinfo.io/ip
```

---

## 调试技巧

### 查看完整响应

```bash
curl -v "https://api.weixin.qq.com/cgi-bin/token?..."
```

### 格式化 JSON 输出

```bash
curl -s "..." | python3 -m json.tool
# 或
curl -s "..." | jq .
```

### 检查 HTML 内容编码

确保 content 字段中的 HTML 正确转义：
- `"` → `\"`
- 换行符 → `\n` 或移除
- 特殊字符正确编码
