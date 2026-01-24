import json
import requests
import re
import sys

# 配置信息
ACCESS_TOKEN = "100_bF2ybgQhIfqbSjfNM_etv-Rwz_TFp22YkH8HJTg3MsH3xkXZF5xgYup_NLHH8OH2WxgibVykk3C_1P2hp7gxMpQLMWE-lcEX2942teIxP-HmB5tpG7ixXithcxsLGSaADAOJV"
DEFAULT_THUMB_MEDIA_ID = "PeAJK_viCcf8q7R1gKlTu5CAjuLlWVxBvvLbaq2FiCeGJZRHeZYWSrdS_jx8orOG"
AUTHOR = "Chaucer"

def simple_md_to_html(md_path):
    with open(md_path, 'r') as f:
        content = f.read()

    # 移除 frontmatter
    content = re.sub(r'^---[\s\S]*?---\n', '', content)

    # 基础 HTML 转换 (实际生产应使用更完善的转换器)
    html_lines = []
    html_lines.append('<section id="nice" style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif; font-size: 16px; line-height: 1.6; word-wrap: break-word;">')

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue

        if line.startswith('# '):
            html_lines.append(f'<h1 style="font-size: 24px; font-weight: bold; margin: 20px 0 10px; padding-bottom: 5px; border-bottom: 1px solid #eaecef;">{line[2:]}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2 style="font-size: 20px; font-weight: bold; margin: 18px 0 10px; padding-left: 10px; border-left: 4px solid #448aff;">{line[3:]}</h2>')
        elif line.startswith('❓'):
            html_lines.append(f'<section style="background: #fff3cd; padding: 15px; border-radius: 4px; margin: 15px 0; color: #856404;"><strong>{line}</strong></section>')
        else:
            html_lines.append(f'<p style="margin-bottom: 15px; color: #333;">{line}</p>')

    html_lines.append('</section>')
    return '\n'.join(html_lines)

def publish():
    print("正在转换 Markdown...")
    html_content = simple_md_to_html('SSO_Design.md')

    article_data = {
        "articles": [{
            "title": "统一认证中心设计方案",
            "author": AUTHOR,
            "digest": "基于 OAuth 2.0 的企业级单点登录架构设计，解决外部 APP 集成与内部业务系统导航的经典场景。",
            "content": html_content,
            "thumb_media_id": DEFAULT_THUMB_MEDIA_ID,
            "need_open_comment": 0
        }]
    }

    print("正在调用微信 API...")
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={ACCESS_TOKEN}"
    response = requests.post(url, json=article_data)

    print("API 响应:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    publish()
