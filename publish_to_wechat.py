#!/usr/bin/env python3
import os
import re
import json
import time
import requests
import yaml
import markdown
import base64
import subprocess
import tempfile
import zlib
from urllib.parse import urlparse
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter


# ================= 配置区域 =================
CONFIG_FILE = "config/wechat-credentials.local.md"
WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"

# Admonition 配置 (图标使用 SVG)
ADMONITION_ICONS = {
    'pencil': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path><path d="m15 5 4 4"></path></svg>',
    'clipboard-list': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><path d="M12 11h4"></path><path d="M12 16h4"></path><path d="M8 11h.01"></path><path d="M8 16h.01"></path></svg>',
    'info': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>',
    'check-circle-2': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>',
    'flame': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path></svg>',
    'check': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M20 6 9 17l-5-5"></path></svg>',
    'help-circle': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><path d="M12 17h.01"></path></svg>',
    'alert-triangle': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>',
    'x': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>',
    'zap': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
    'bug': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="m8 2 1.88 1.88"></path><path d="M14.12 3.88 16 2"></path><path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"></path><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"></path><path d="M12 20v-9"></path><path d="M6.53 9C4.6 8.8 3 7.1 3 5"></path><path d="M6 13H2"></path><path d="M3 21c0-2.1 1.7-3.9 3.8-4"></path><path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"></path><path d="M22 13h-4"></path><path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"></path></svg>',
    'list': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
    'quote': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"></path><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"></path></svg>'
}

ADMONITION_TYPES = {
    'note': {'color': '#448aff', 'bg': 'rgba(68, 138, 255, 0.1)', 'icon': 'pencil'},
    'abstract': {'color': '#00bfa5', 'bg': 'rgba(0, 191, 165, 0.1)', 'icon': 'clipboard-list'},
    'info': {'color': '#448aff', 'bg': 'rgba(68, 138, 255, 0.1)', 'icon': 'info'},
    'todo': {'color': '#448aff', 'bg': 'rgba(68, 138, 255, 0.1)', 'icon': 'check-circle-2'},
    'tip': {'color': '#00bfa5', 'bg': 'rgba(0, 191, 165, 0.1)', 'icon': 'flame'},
    'success': {'color': '#00c853', 'bg': 'rgba(0, 200, 83, 0.1)', 'icon': 'check'},
    'question': {'color': '#ffab00', 'bg': 'rgba(255, 171, 0, 0.1)', 'icon': 'help-circle'},
    'warning': {'color': '#ff9100', 'bg': 'rgba(255, 171, 0, 0.1)', 'icon': 'alert-triangle'},
    'failure': {'color': '#ff5252', 'bg': 'rgba(255, 82, 82, 0.1)', 'icon': 'x'},
    'danger': {'color': '#ff5252', 'bg': 'rgba(255, 82, 82, 0.1)', 'icon': 'zap'},
    'bug': {'color': '#ff5252', 'bg': 'rgba(255, 82, 82, 0.1)', 'icon': 'bug'},
    'example': {'color': '#7c4dff', 'bg': 'rgba(124, 77, 255, 0.1)', 'icon': 'list'},
    'quote': {'color': '#9e9e9e', 'bg': 'rgba(158, 158, 158, 0.1)', 'icon': 'quote'}
}

ADMONITION_ALIASES = {
    'summary': 'abstract', 'tldr': 'abstract',
    'hint': 'tip', 'important': 'tip',
    'check': 'success', 'done': 'success',
    'help': 'question', 'faq': 'question',
    'caution': 'warning', 'attention': 'warning',
    'fail': 'failure', 'missing': 'failure',
    'error': 'danger', 'cite': 'quote'
}

# 基础样式
BASIC_STYLE = """
<style>
  #nice { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #333; word-wrap: break-word; }
  #nice h1 { font-size: 22px; font-weight: bold; margin: 20px 0 10px; text-align: center; padding-bottom: 5px; border-bottom: 2px solid #db4c3f; }
  #nice h2 { font-size: 20px; font-weight: bold; margin: 18px 0 10px; padding: 5px 10px; border-left: 5px solid #db4c3f; border-bottom: 1px dashed #db4c3f; background: #fff5f5; line-height: 1.5; }
  #nice h3 { font-size: 18px; font-weight: bold; margin: 16px 0 8px; }
  #nice p { margin-bottom: 15px; text-align: justify; }
  #nice code { background-color: rgba(27,31,35,.05); border-radius: 3px; font-size: 85%; margin: 0; padding: .2em .4em; font-family: SFMono-Regular,Consolas,Liberation Mono,Menlo,Courier,monospace; }
  #nice pre { background: #f6f8fa; border-radius: 4px; padding: 16px; overflow: auto; line-height: 1.45; }
  #nice pre code { background: transparent; padding: 0; white-space: pre; }
  #nice blockquote { margin: 0 0 16px; padding: 0 1em; color: #6a737d; border-left: .25em solid #db4c3f; background-color: #fff5f5; }
  #nice img { max-width: 100%; border-radius: 4px; display: block; margin: 20px auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  #nice ul, #nice ol { padding-left: 2em; margin-bottom: 16px; }
  #nice li { margin-bottom: 4px; }
  #nice table { display: block; width: 100%; overflow: auto; margin-bottom: 16px; border-spacing: 0; border-collapse: collapse; }
  #nice tr { background-color: #fff; border-top: 1px solid #fabec9; }
  #nice tr:nth-child(2n) { background-color: #fff5f5; }
  #nice th, #nice td { padding: 6px 13px; border: 1px solid #fabec9; }
  #nice th { font-weight: 600; color: #db4c3f; background-color: #fff5f5; }
  #nice strong { color: #db4c3f; }
  #nice hr { border: none; border-top: 1px dashed #db4c3f; margin: 30px 0; }
  /* Admonition/Mermaid 相关样式 */
  .callout-icon svg { width: 20px; height: 20px; vertical-align: middle; }
  .footnotes { font-size: 14px; color: #666; margin-top: 40px; padding-top: 20px; border-top: 1px dashed #db4c3f; }
  .footnote-item { margin-bottom: 10px; }
</style>
"""

# ================= 工具函数 =================

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件 {CONFIG_FILE} 不存在")
    with open(CONFIG_FILE, 'r') as f:
        content = f.read()
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
    return {}

def get_access_token(config):
    if config.get('access_token'):
        return config['access_token']
    url = f"{WECHAT_API_BASE}/token"
    params = {
        "grant_type": "client_credential",
        "appid": config['appid'],
        "secret": config['secret']
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    if 'access_token' in data:
        return data['access_token']
    else:
        raise Exception(f"获取 Token 失败: {data}")

def upload_image(token, image_path_or_url):
    url = f"{WECHAT_API_BASE}/media/uploadimg?access_token={token}"
    files = {}
    if image_path_or_url.startswith(('http://', 'https://')):
        try:
            # 添加 User-Agent 避免被反爬拦截
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            img_resp = requests.get(image_path_or_url, headers=headers, timeout=30)

            # 基础验证
            if img_resp.status_code != 200:
                print(f"下载图片失败，状态码: {img_resp.status_code}")
                return None

            if not img_resp.content:
                print("下载图片内容为空")
                return None

            # 动态检测 Content-Type
            content_type = img_resp.headers.get('Content-Type', '').lower()

            # 映射扩展名
            ext_map = {
                'image/png': '.png',
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/gif': '.gif',
                'image/webp': '.webp'
            }
            # 默认使用 .jpg
            ext = ext_map.get(content_type, '.jpg')

            # 如果没有获取到 Content-Type，默认为 image/jpeg
            if not content_type:
                content_type = 'image/jpeg'

            filename = f'image{ext}'

            # 使用检测到的类型和文件名
            files = {'media': (filename, img_resp.content, content_type)}

        except Exception as e:
            print(f"下载图片失败: {e}")
            return None
    else:
        if not os.path.exists(image_path_or_url):
            print(f"本地图片不存在: {image_path_or_url}")
            return None
        files = {'media': open(image_path_or_url, 'rb')}

    resp = requests.post(url, files=files)
    data = resp.json()
    if 'url' in data:
        return data['url']
    else:
        print(f"上传图片失败: {data}")
        return None

# ================= 新增处理函数 =================

def render_mermaid_with_playwright(mermaid_code):
    """
    使用 Playwright 在浏览器中渲染 Mermaid 图表
    """
    try:
        # 创建临时 HTML 文件
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 80px;
            background: white;
            display: inline-block;
        }}
        #mermaid-container {{
            background: white;
        }}
        /* 优化字体大小，确保清晰度 */
        .mermaid text {{
            font-size: 16px !important;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}
        .mermaid .edgeLabel {{
            font-size: 14px !important;
            background-color: white !important;
            padding: 4px !important;
        }}
        .mermaid .sequenceNumber {{
            fill: #333 !important;
            stroke: #333 !important;
            stroke-width: 2px !important;
        }}
        /* Ensure sequence number text is white */
        .mermaid text.sequenceNumber,
        .mermaid .sequenceNumber text {{
            fill: #fff !important;
            stroke: none !important;
        }}
    </style>
</head>
<body>
    <div id="mermaid-container">
        <pre class="mermaid">
{mermaid_code}
        </pre>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                fontSize: '16px',
                fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
                primaryTextColor: '#000',
                lineColor: '#333',
                nodePadding: 20,
                sequenceNumberColor: '#fff',
                sequenceNumberBgColor: '#000'
            }},
            flowchart: {{
                htmlLabels: true,
                curve: 'basis',
                padding: 40,
                nodeSpacing: 50,
                rankSpacing: 50
            }},
            sequence: {{
                showSequenceNumbers: true,
                diagramMarginX: 40,
                diagramMarginY: 40,
                actorMargin: 50,
                width: 150,
                height: 65,
                boxMargin: 20,
                messageMargin: 35,
                fontSize: 16,
                messageFontSize: 14,
                noteFontSize: 14,
                actorFontSize: 16,
                messageFontWeight: 400,
                wrap: true
            }}
        }});
    </script>
</body>
</html>
"""

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            html_path = f.name

        # 生成输出路径
        output_path = html_path.replace('.html', '.png')

        # 使用 subprocess 调用 Claude Code 的 Playwright MCP
        # 注意：这里需要通过命令行调用，因为 MCP 工具在 Python 脚本中不可直接访问
        # 替代方案：使用 playwright 库（需要安装 playwright）
        try:
            import playwright.sync_api as pw
            with pw.sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # 彻底回滚到标准配置：1000px 宽度 + 2x 缩放
                # 这保证了布局舒展且清晰度足够
                page = browser.new_page(
                    viewport={'width': 1000, 'height': 800},
                    device_scale_factor=2
                )
                page.goto(f'file://{html_path}')

                # 等待渲染
                page.wait_for_timeout(3000)

                # 获取 SVG 元素并截图
                element = page.query_selector('.mermaid svg')
                if element:
                    element.screenshot(
                        path=output_path,
                        scale='device',
                        omit_background=True
                    )
                else:
                    page.screenshot(path=output_path, full_page=True)

                browser.close()

            # 清理临时 HTML
            os.unlink(html_path)
            return output_path

        except ImportError:
            print("警告: playwright 库未安装，尝试使用 Kroki.io")
            os.unlink(html_path)
            return None

    except Exception as e:
        print(f"Playwright 渲染失败: {e}")
        return None

def render_mermaid_with_kroki(mermaid_code):
    """
    使用 Kroki.io API 渲染 Mermaid 图表（备用方案）
    """
    try:
        import zlib
        # Kroki 使用 deflate + base64 编码
        compressed = zlib.compress(mermaid_code.encode('utf-8'), level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
        kroki_url = f"https://kroki.io/mermaid/png/{encoded}"

        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(kroki_url, headers=headers, timeout=15)

        if response.status_code == 200 and response.content:
            # 保存到临时文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
                f.write(response.content)
                return f.name
        else:
            print(f"Kroki.io 返回错误: {response.status_code}")
            return None

    except Exception as e:
        print(f"Kroki.io 渲染失败: {e}")
        return None

def render_mermaid_locally(mermaid_code):
    """
    使用多层降级策略渲染 Mermaid 图表
    策略: Playwright → Kroki.io → None (显示代码块)
    """
    print("  [1/3] 尝试使用 Playwright 本地渲染...")
    result = render_mermaid_with_playwright(mermaid_code)
    if result:
        print("  ✓ Playwright 渲染成功")
        return result

    print("  [2/3] 尝试使用 Kroki.io API...")
    result = render_mermaid_with_kroki(mermaid_code)
    if result:
        print("  ✓ Kroki.io 渲染成功")
        return result

    print("  [3/3] 所有渲染方案失败，将显示为代码块")
    return None

def process_mermaid(content):
    """将 Mermaid 代码块转换为图片或优雅降级为代码块"""
    pattern = r'```mermaid\s*\n([\s\S]*?)```'

    def repl(m):
        code = m.group(1).strip()
        print("\n处理 Mermaid 图表...")

        # 使用多层降级策略渲染
        local_image_path = render_mermaid_locally(code)

        if local_image_path:
            # 返回带居中样式的 HTML 图片标签（稍后会被替换为微信 CDN URL）
            # 使用 PLACEHOLDER 标记，等图片上传后再替换
            return f'![MERMAID_DIAGRAM]({local_image_path})'
        else:
            # 所有渲染方案失败，生成格式化的降级代码块
            print("  → 降级为格式化代码块显示")
            # 转换为 HTML 格式的代码块（与微信兼容）
            escaped_code = code.replace('<', '&lt;').replace('>', '&gt;')
            fallback_html = f"""
<section class="mermaid-fallback" style="background: #f5f7fa; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #909399;">
  <p style="color: #606266; font-size: 14px; margin: 0 0 12px; font-weight: 600;">
    📊 流程图 (Mermaid)
  </p>
  <pre style="background: #fff; padding: 12px; border-radius: 4px; overflow-x: auto; margin: 0; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.5; color: #303133;"><code>{escaped_code}</code></pre>
  <p style="color: #909399; font-size: 12px; margin: 12px 0 0; font-style: italic;">
    提示: 图表渲染暂时不可用，已显示原始代码
  </p>
</section>
"""
            return fallback_html

    return re.sub(pattern, repl, content)

def process_admonitions(content):
    """将 Admonition 代码块转换为 HTML"""
    # 匹配 ```ad-type ... ``` 块
    pattern = r'```ad-(\w+)(?:[ \t]+title:[ \t]*(.*))?\n([\s\S]*?)```'

    def repl(m):
        ad_type = m.group(1).lower()
        title = m.group(2)
        body = m.group(3)

        # 处理别名
        if ad_type in ADMONITION_ALIASES:
            ad_type = ADMONITION_ALIASES[ad_type]

        # 获取样式配置 (默认使用 note)
        config = ADMONITION_TYPES.get(ad_type, ADMONITION_TYPES['note'])

        # 默认标题
        if not title:
            title = ad_type.capitalize()
        else:
            title = title.strip()

        # 图标 SVG
        icon_svg = ADMONITION_ICONS.get(config['icon'], ADMONITION_ICONS['pencil'])

        # 递归处理正文 Markdown
        # 注意：这里我们使用 markdown 库来渲染内部内容，确保加粗、链接等生效
        body_html = markdown.markdown(body, extensions=['fenced_code', 'tables'])

        # 生成 HTML (内联样式以适应微信)
        html = f"""
<section class="admonition" style="border-radius: 4px; margin: 16px 0; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
  <section class="admonition-title" style="display: flex; align-items: center; padding: 8px 12px; background: {config['bg']};">
    <span style="color: {config['color']}; margin-right: 8px; display: flex; align-items: center;">
      {icon_svg}
    </span>
    <span style="font-weight: 600; color: {config['color']};">{title}</span>
  </section>
  <section class="admonition-content" style="padding: 12px 16px; background: {config['bg']}; border-left: 4px solid {config['color']};">
    <div style="font-size: 16px; color: #333; line-height: 1.6;">
    {body_html}
    </div>
  </section>
</section>
"""
        return html

    return re.sub(pattern, repl, content)

def process_footnotes(content):
    """将 [text](url) 链接转换为脚注形式"""
    links = []

    def repl(m):
        text = m.group(1)
        url = m.group(2)
        links.append({'text': text, 'url': url})
        index = len(links)
        # 微信不支持外链，转为蓝色文字 + 上标
        return f'<span style="color: #3370ff;">{text}</span><sup style="color: #3370ff; font-weight: bold;">[{index}]</sup>'

    # 匹配 Markdown 链接，排除图片 ![]()
    # 使用断言 (?<!!) 确保前面不是 !
    pattern = r'(?<!!)\[(.*?)\]\((.*?)\)'
    content = re.sub(pattern, repl, content)

    # 生成脚注列表
    if links:
        content += '\n\n<div class="footnotes">'
        content += '<h4 style="font-size: 14px; color: #999; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 5px;">引用链接</h4>'
        for i, link in enumerate(links):
            index = i + 1
            content += f'<div class="footnote-item"><span style="color: #3370ff; font-weight: bold;">[{index}]</span> {link["text"]}: {link["url"]}</div>'
        content += '</div>'

    return content

def process_content_workflow(content, token):
    """完整的 Markdown 处理工作流"""

    # 1. 提取 Frontmatter
    frontmatter = {}
    body = content
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end():]

    # [新增] 列表空行清理：移除列表项之间的多余空行，防止微信编辑器渲染异常
    # 1. 紧凑化无序列表
    body = re.sub(r'(\n\s*[-*+]\s+.*)\n\n+(?=\s*[-*+]\s+)', r'\1\n', body)
    # 2. 紧凑化有序列表
    body = re.sub(r'(\n\s*\d+\.\s+.*)\n\n+(?=\s*\d+\.\s+)', r'\1\n', body)

    # 2. Mermaid 处理 (转为图片链接)
    body = process_mermaid(body)

    # 3. 图片上传 (处理所有 ![]()，包括刚才生成的 Mermaid 图片)
    def replace_img(m):
        alt = m.group(1)
        src = m.group(2)
        print(f"正在上传图片: {src}")
        wechat_url = upload_image(token, src)
        if wechat_url:
            # 检查是否是 Mermaid 图表（通过 alt 或路径判断）
            is_mermaid = 'MERMAID_DIAGRAM' in alt or '/tmp' in src

            if is_mermaid:
                # Mermaid 图表使用居中样式的 HTML
                return f'''
<section class="mermaid-wrapper" style="text-align: center; margin: 24px 0;">
  <img src="{wechat_url}" alt="流程图" style="max-width: 100%; height: auto; display: inline-block; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 4px;" />
</section>
'''
            else:
                # 普通图片也居中显示
                return f'''
<section class="image-wrapper" style="text-align: center; margin: 20px 0;">
  <img src="{wechat_url}" alt="{alt}" style="max-width: 100%; height: auto; display: inline-block; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />
</section>
'''
        return m.group(0)

    body = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_img, body)

    # 4. Admonition 处理 (转为 HTML)
    # 注意：此时 body 里的图片已经是微信链接了，HTML 渲染时会保留
    body = process_admonitions(body)

    # 5. 链接转脚注
    body = process_footnotes(body)

    return frontmatter, body

def md_to_html(md_content):
    """Markdown 转 HTML"""
    # 转换剩余的 Markdown (如列表、粗体等)
    # 启用 codehilite 扩展以支持代码高亮
    # 启用 fenced_code 以支持 ``` 语法
    html = markdown.markdown(md_content,
        extensions=['fenced_code', 'tables', 'codehilite'],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': True,
                'use_pygments': True,
                'noclasses': True  # 关键：生成内联样式
            }
        }
    )

    # 添加全局背景色 (暖杏色/信纸色)
    final_html = f"""
    <section id="nice" style="background-color: #fffdf9; padding: 20px; border-radius: 8px;">
        {BASIC_STYLE}
        {html}
    </section>
    """
    # 简单的样式增强 (强制内联关键样式，确保在微信中生效)
    # H1: 居中，底部实线
    final_html = final_html.replace('<h1>', '<h1 style="font-size: 22px; font-weight: bold; margin: 20px 0 10px; text-align: center; padding-bottom: 5px; border-bottom: 2px solid #db4c3f;">')

    # H2: 左侧粗线，底部虚线，去除了背景色(整体背景色已设)
    h2_style = 'style="font-size: 20px; font-weight: bold; margin: 25px 0 15px; padding: 5px 10px; border-left: 5px solid #db4c3f; border-bottom: 1px dashed #db4c3f; line-height: 1.5;"'
    final_html = final_html.replace('<h2>', f'<h2 {h2_style}>')

    # H3: 同样应用 H2 的样式
    h3_style = 'style="font-size: 18px; font-weight: bold; margin: 22px 0 12px; padding: 5px 10px; border-left: 5px solid #db4c3f; border-bottom: 1px dashed #db4c3f; line-height: 1.5;"'
    final_html = final_html.replace('<h3>', f'<h3 {h3_style}>')

    # H4: 增加 H4 样式 (稍小一些，保持风格)
    # 去除背景色，只保留左侧线条
    h4_style = 'style="font-size: 16px; font-weight: bold; margin: 20px 0 10px; padding: 4px 8px; border-left: 4px solid #db4c3f; line-height: 1.5;"'
    final_html = final_html.replace('<h4>', f'<h4 {h4_style}>')

    # Strong: 铁锈红字体
    final_html = final_html.replace('<strong>', '<strong style="color: #db4c3f; font-weight: bold;">')

    # List Containers: 增加缩进，防止序号/列表点被吞
    # 恢复缩进为 25px
    list_style = 'style="margin-bottom: 16px; padding-left: 25px;"'
    final_html = final_html.replace('<ul>', f'<ul {list_style}>')
    final_html = final_html.replace('<ol>', f'<ol {list_style}>')

    # List Items: 序号/圆点改为红色，正文保持黑色
    # 策略：设置 li 颜色为红色，然后将 li 的内容包裹在 span 中重置为黑色
    final_html = final_html.replace('<li>', '<li style="color: #db4c3f; margin-bottom: 4px;">')
    # 正则替换 li 内容，包裹 span 黑色 + block display 以确保换行缩进正常
    final_html = re.sub(r'<li>(?!<p>)(.*?)</li>', r'<li><span style="color: #333; display: block;">\1</span></li>', final_html, flags=re.DOTALL)

    # Code Blocks (Pre + Code): 优化代码块样式
    # 不再统一替换 pre/code，而是依赖 Pygments 生成的高亮 HTML
    # 但 Pygments 生成的只是 <div class="highlight"><pre>...</pre></div>
    # 我们需要给最外层容器加卡片样式，并给 pre 加样式

    # 1. 给 Pygments 容器 (.highlight) 增加卡片样式
    # 暖米色背景 + 暖灰边框 + 圆角 + 内边距
    # 注意：这里移除了 overflow-x: auto，交给了内部的 pre 处理，避免双重滚动条
    highlight_container_style = 'background: #f7f1e3; border: 1px solid #e6dec5; border-radius: 5px; padding: 10px 15px; margin: 15px 0;'
    final_html = final_html.replace('<div class="highlight">', f'<div class="highlight" style="{highlight_container_style}">')

    # 2. 给 pre 标签加样式 (消除默认 margin，字体设置)
    # Pygments 的 pre 通常包含 span 元素
    # 关键修改：强制 white-space: pre 以保留格式化 (换行和缩进)
    # 关键修改：overflow-x: auto 允许横向滚动
    pre_style = 'margin: 0; line-height: 1.5; font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace; font-size: 13px; color: #333; white-space: pre; overflow-x: auto; border: none; padding: 0;'
    final_html = final_html.replace('<pre>', f'<pre style="{pre_style}">')

    # 3. 清理代码块内部 span 的背景色
    # Pygments 生成的 span 可能会自带 background-color，导致每行代码有独立背景，这很难看
    # 我们需要移除 span 标签中的 background 样式，统一使用外层容器的背景
    def clean_span_background(match):
        block = match.group(0)
        # 移除 background-color: ...; 或 background: ...;
        block = re.sub(r'background(-color)?:\s*[^;"]+;?', '', block)
        return block

    # 仅针对 <div class="highlight"> 内部的内容进行清理
    # 使用正则非贪婪匹配捕获代码块
    final_html = re.sub(r'(<div class="highlight"[^>]*>.*?</div>)', clean_span_background, final_html, flags=re.DOTALL)

    # 4. 兜底处理：如果有未被 Pygments 处理的普通代码块 (比如缩进式代码块)
    # 它们通常是 <pre><code>...</code></pre> 结构
    # 此时我们需要手动加样式
    # 注意：Pygments 生成的 pre 里面通常直接是 span，没有 code 标签 (或者 formatter 设置不同)
    # 如果 markdown 解析器保留了 <pre><code> 结构且没被高亮处理：
    fallback_pre_style = 'background: #f7f1e3; border: 1px solid #e6dec5; border-radius: 5px; padding: 15px; overflow-x: auto; margin: 15px 0; color: #333; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.5;'
    final_html = final_html.replace('<pre><code>', f'<pre style="{fallback_pre_style}"><code>')

    # Inline Code: 优化行内代码样式
    # 策略：查找所有 code 标签，排除掉已经带有 style 属性的 (即上面处理过的块级代码)
    # 去除粉红色背景，只保留铁锈红文字和淡淡的灰色背景，更清爽
    inline_code_style = 'background: #f0f0f0; color: #db4c3f; padding: 2px 4px; border-radius: 3px; font-family: Consolas, Monaco, monospace; font-size: 14px; margin: 0 2px;'

    def replace_inline_code(match):
        attrs = match.group(1)
        # 如果已经有 style 属性，说明是代码块内部的 code，跳过
        if 'style=' in attrs:
            return match.group(0)
        # 排除掉 pre 标签内部的 code (虽然上面的逻辑已经尽量规避，但为了双重保险)
        return f'<code {attrs} style="{inline_code_style}">'

    final_html = re.sub(r'<code([^>]*)>', replace_inline_code, final_html)
    # 如果 li 内部有 p，则给 p 加样式
    final_html = final_html.replace('<p>', '<p style="margin-bottom: 15px; line-height: 1.6; color: #333; text-align: justify;">')

    # Table headers: 铁锈红字体 + 暖色背景
    final_html = final_html.replace('<th>', '<th style="font-weight: 600; color: #db4c3f; padding: 6px 13px; border: 1px solid #e6dec5; background: #f7f1e3;">')

    # Table cells: 暖灰边框
    final_html = final_html.replace('<td>', '<td style="padding: 6px 13px; border: 1px solid #e6dec5;">')

    # HR: 渐变分割线 (中间深两边浅)
    # 使用 linear-gradient 实现渐变
    final_html = re.sub(r'<hr\s*/?>', '<hr style="border: 0; height: 1px; background-image: linear-gradient(to right, rgba(219, 76, 63, 0), rgba(219, 76, 63, 1), rgba(219, 76, 63, 0)); margin: 40px 0;">', final_html)

    return final_html

def publish_draft(token, article_data):
    url = f"{WECHAT_API_BASE}/draft/add?access_token={token}"
    json_str = json.dumps(article_data, ensure_ascii=False)
    # print(f"【调试】发送数据预览 (前200字符):\n{json_str[:200]}...")
    json_bytes = json_str.encode('utf-8')
    resp = requests.post(
        url,
        data=json_bytes,
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )
    return resp.json()

# ================= 主流程 =================

def main(file_path):
    print(f"开始处理文件: {file_path}")

    # 1. 加载配置
    try:
        config = load_config()
        token = get_access_token(config)
        print("Token 获取成功")
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    # 2. 读取文件
    with open(file_path, 'r') as f:
        raw_content = f.read()

    # 3. 处理内容 (工作流)
    print("正在处理 Markdown 内容...")
    frontmatter, processed_body = process_content_workflow(raw_content, token)

    # 4. 转换 HTML
    html_content = md_to_html(processed_body)

    # 5. 准备发布
    thumb_media_id = frontmatter.get('thumb_media_id', config.get('default_thumb_media_id'))
    if not thumb_media_id:
        print("警告: 未找到封面图 (thumb_media_id)，请在 frontmatter 中指定，否则发布可能失败")

    article = {
        "title": frontmatter.get('title', "未命名文章"),
        "author": frontmatter.get('author', config.get('default_author')),
        "digest": frontmatter.get('digest', ""),
        "content": html_content,
        "content_source_url": frontmatter.get('source_url', ""),
        "thumb_media_id": thumb_media_id,
        "need_open_comment": frontmatter.get('open_comment', 0)
    }

    payload = {"articles": [article]}

    # 6. 发布
    print("正在发布到草稿箱...")
    result = publish_draft(token, payload)
    print("发布结果:", json.dumps(result, indent=2, ensure_ascii=False))

    if 'media_id' in result:
        print(f"\n✅ 发布成功! Media ID: {result['media_id']}")
    else:
        print("\n❌ 发布失败")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("请提供 Markdown 文件路径")
