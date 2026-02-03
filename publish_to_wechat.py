#!/usr/bin/env python3
import os
import re
import json
import base64
import tempfile
import zlib
import random
from html.parser import HTMLParser

import requests
import yaml
import markdown

# ================= 配置 =================

CONFIG_FILE = "config/wechat-credentials.local.md"
WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"
UNSPLASH_API_BASE = "https://api.unsplash.com"

# 中文停用词（用于关键词提取）
CHINESE_STOPWORDS = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '什么', '如何', '为什么', '怎么', '怎样'}

# 中文技术词汇到英文的映射（提升 Unsplash 搜索效果）
KEYWORD_TRANSLATIONS = {
    '认证': 'authentication', '登录': 'login', '安全': 'security',
    '架构': 'architecture', '设计': 'design', '系统': 'system',
    '数据': 'data', '分析': 'analytics', '人工智能': 'artificial intelligence',
    '机器学习': 'machine learning', '深度学习': 'deep learning',
    '编程': 'programming', '开发': 'development', '代码': 'code',
    '网络': 'network', '云计算': 'cloud computing', '服务器': 'server',
    '数据库': 'database', '接口': 'API', '前端': 'frontend',
    '后端': 'backend', '移动': 'mobile', '应用': 'application',
    '用户': 'user', '产品': 'product', '项目': 'project',
    '团队': 'team', '管理': 'management', '效率': 'efficiency',
    '创新': 'innovation', '技术': 'technology', '解决方案': 'solution',
    '统一': 'unified', '中心': 'center', '平台': 'platform',
    '集成': 'integration', '门户': 'portal', '单点登录': 'SSO',
}

# Unsplash 通用分类（翻译失败时的降级选项）
UNSPLASH_FALLBACK_CATEGORIES = [
    'technology', 'business', 'abstract', 'minimal',
    'workspace', 'nature', 'architecture', 'gradient'
]

# Admonition SVG 图标
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

# 内联样式常量
STYLES = {
    'h1': 'font-size: 22px; font-weight: bold; margin: 20px 0 10px; text-align: center; padding-bottom: 5px; border-bottom: 2px solid #db4c3f;',
    'h2': 'font-size: 20px; font-weight: bold; margin: 25px 0 15px; padding: 5px 10px; border-left: 5px solid #db4c3f; border-bottom: 1px dashed #db4c3f; line-height: 1.5;',
    'h3': 'font-size: 18px; font-weight: bold; margin: 22px 0 12px; padding: 5px 10px; border-left: 5px solid #db4c3f; border-bottom: 1px dashed #db4c3f; line-height: 1.5;',
    'h4': 'font-size: 16px; font-weight: bold; margin: 20px 0 10px; padding: 4px 8px; border-left: 4px solid #db4c3f; line-height: 1.5;',
    'strong': 'color: #db4c3f; font-weight: bold;',
    'th': 'font-weight: 600; color: #db4c3f; padding: 6px 13px; border: 1px solid #e6dec5; background: #f7f1e3;',
    'td': 'padding: 6px 13px; border: 1px solid #e6dec5;',
    'hr': 'border: 0; height: 1px; background-image: linear-gradient(to right, rgba(219, 76, 63, 0), rgba(219, 76, 63, 1), rgba(219, 76, 63, 0)); margin: 40px 0;',
    'list_container': "list-style: none; margin: 0em 8px 1.5em; padding: 0px; text-align: left; line-height: 1.75; font-family: 'PingFang SC', -apple-system-font, BlinkMacSystemFont, 'Helvetica Neue', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif; font-size: 15px; color: rgb(63, 63, 63);",
    'list_item': "margin: 0.5em 0px; padding: 0px; text-align: left; line-height: 1.75; font-family: 'PingFang SC', -apple-system-font, BlinkMacSystemFont, 'Helvetica Neue', 'Hiragino Sans GB', 'Microsoft YaHei UI', 'Microsoft YaHei', Arial, sans-serif; font-size: 15px; color: rgb(63, 63, 63);",
    'pre': 'background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px; margin: 16px 0; line-height: 1.6; font-family: Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace; font-size: 13px; color: #333; white-space: pre-wrap; word-break: break-all; overflow-x: auto;',
    'inline_code': 'background: #f0f0f0; color: #db4c3f; padding: 2px 4px; border-radius: 3px; font-family: Consolas, Monaco, monospace; font-size: 14px; margin: 0 2px;',
}

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
  .callout-icon svg { width: 20px; height: 20px; vertical-align: middle; }
  .footnotes { font-size: 14px; color: #666; margin-top: 40px; padding-top: 20px; border-top: 1px dashed #db4c3f; }
  .footnote-item { margin-bottom: 10px; }
</style>
"""


# ================= 工具函数 =================

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件 {CONFIG_FILE} 不存在")
    with open(CONFIG_FILE, 'r') as f:
        content = f.read()
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    return yaml.safe_load(match.group(1)) if match else {}


def get_access_token(config: dict) -> str:
    if config.get('access_token'):
        return config['access_token']

    resp = requests.get(f"{WECHAT_API_BASE}/token", params={
        "grant_type": "client_credential",
        "appid": config['appid'],
        "secret": config['secret']
    })
    data = resp.json()

    if 'access_token' not in data:
        raise Exception(f"获取 Token 失败: {data}")
    return data['access_token']


def upload_image(token: str, image_path_or_url: str) -> str | None:
    """上传图片到微信，支持本地路径和远程 URL"""
    url = f"{WECHAT_API_BASE}/media/uploadimg?access_token={token}"

    if image_path_or_url.startswith(('http://', 'https://')):
        files = _download_image_for_upload(image_path_or_url)
        if not files:
            return None
    else:
        if not os.path.exists(image_path_or_url):
            print(f"本地图片不存在: {image_path_or_url}")
            return None
        files = {'media': open(image_path_or_url, 'rb')}

    data = requests.post(url, files=files).json()
    if 'url' not in data:
        print(f"上传图片失败: {data}")
        return None
    return data['url']


def _download_image_for_upload(image_url: str) -> dict | None:
    """下载远程图片并准备上传"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    try:
        resp = requests.get(image_url, headers=headers, timeout=30)
        if resp.status_code != 200 or not resp.content:
            print(f"下载图片失败，状态码: {resp.status_code}")
            return None

        content_type = resp.headers.get('Content-Type', 'image/jpeg').lower()
        ext_map = {
            'image/png': '.png', 'image/jpeg': '.jpg', 'image/jpg': '.jpg',
            'image/gif': '.gif', 'image/webp': '.webp'
        }
        ext = ext_map.get(content_type, '.jpg')

        return {'media': (f'image{ext}', resp.content, content_type)}
    except Exception as e:
        print(f"下载图片失败: {e}")
        return None


# ================= 自动封面功能 =================

def translate_to_english(text: str) -> str | None:
    """将中文翻译为英文，使用多层降级策略"""
    # 1. 先查硬编码字典（快速缓存）
    if text in KEYWORD_TRANSLATIONS:
        return KEYWORD_TRANSLATIONS[text]

    # 2. 尝试在线翻译（translators 库，优先 Google）
    try:
        import translators as ts
        result = ts.translate_text(text, from_language='zh', to_language='en', translator='google')
        if result and result != text:
            return result
    except Exception:
        pass

    return None  # 翻译失败


def extract_keywords(title: str, digest: str = "") -> list[str]:
    """从标题和摘要提取关键词，自动翻译为英文"""
    text = f"{title} {digest}"

    # 1. 提取英文单词
    english_words = re.findall(r'[a-zA-Z]{3,}', text)

    # 2. 提取中文并翻译
    chinese_text = re.sub(r'[a-zA-Z0-9\s\W]+', '', text)
    translated = []
    if chinese_text:
        result = translate_to_english(chinese_text[:20])
        if result:
            translated = result.split()[:3]

    # 3. 合并去重
    keywords = []
    seen = set()
    for word in english_words + translated:
        word_lower = word.lower()
        if word_lower not in seen and len(word) >= 2:
            seen.add(word_lower)
            keywords.append(word)
            if len(keywords) >= 5:
                break

    # 4. 如果没有关键词，从通用分类随机选一个
    if not keywords:
        keywords = [random.choice(UNSPLASH_FALLBACK_CATEGORIES)]

    return keywords


def _search_unsplash(access_key: str, query: str) -> str | None:
    """执行单次 Unsplash 搜索"""
    try:
        resp = requests.get(
            f"{UNSPLASH_API_BASE}/search/photos",
            params={
                'query': query,
                'orientation': 'landscape',  # 横向图片适合微信封面
                'per_page': 1
            },
            headers={'Authorization': f'Client-ID {access_key}'},
            timeout=10
        )

        if resp.status_code == 403:
            print("  Unsplash API 限流，跳过自动封面")
            return None

        data = resp.json()
        if data.get('results'):
            # 使用 regular 尺寸（1080px 宽度，适合微信）
            return data['results'][0]['urls'].get('regular')
        return None
    except Exception as e:
        print(f"  Unsplash 搜索失败: {e}")
        return None


def search_unsplash_cover(access_key: str, keywords: list[str]) -> str | None:
    """从 Unsplash 搜索横向封面图片，支持降级到通用分类"""
    if not access_key:
        return None

    # 1. 尝试用关键词搜索
    query = ' '.join(keywords[:3])
    print(f"  搜索 Unsplash: {query}")
    image_url = _search_unsplash(access_key, query)
    if image_url:
        print(f"  ✓ 找到匹配图片")
        return image_url

    # 2. 未找到，降级到通用分类随机搜索
    print(f"  未找到匹配图片，尝试通用分类...")
    fallback_category = random.choice(UNSPLASH_FALLBACK_CATEGORIES)
    print(f"  搜索 Unsplash: {fallback_category}")
    image_url = _search_unsplash(access_key, fallback_category)
    if image_url:
        print(f"  ✓ 从 '{fallback_category}' 分类找到图片")
        return image_url

    print(f"  通用分类也未找到图片")
    return None


def download_image_to_temp(image_url: str) -> str | None:
    """下载图片到临时文件"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        resp = requests.get(image_url, headers=headers, timeout=30)

        if resp.status_code != 200:
            return None

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            f.write(resp.content)
            return f.name
    except Exception as e:
        print(f"  下载图片失败: {e}")
        return None


def upload_cover_material(token: str, image_path: str) -> str | None:
    """上传封面图片为微信永久素材，返回 media_id"""
    url = f"{WECHAT_API_BASE}/material/add_material?access_token={token}&type=image"

    try:
        with open(image_path, 'rb') as f:
            files = {'media': ('cover.jpg', f, 'image/jpeg')}
            resp = requests.post(url, files=files, timeout=30)

        data = resp.json()
        if 'media_id' in data:
            print(f"  ✓ 封面上传成功: {data['media_id'][:20]}...")
            return data['media_id']

        print(f"  封面上传失败: {data}")
        return None
    except Exception as e:
        print(f"  封面上传失败: {e}")
        return None


def get_auto_cover(config: dict, token: str, title: str, digest: str = "") -> str | None:
    """自动获取封面图片的 media_id"""
    if not config.get('enable_auto_cover', False):
        return None

    access_key = config.get('unsplash_access_key', '')
    if not access_key:
        print("  未配置 Unsplash API Key，跳过自动封面")
        return None

    print("\n🎨 自动搜索封面图片...")

    # 1. 提取关键词
    keywords = extract_keywords(title, digest)
    print(f"  关键词: {', '.join(keywords)}")

    # 2. 搜索 Unsplash
    image_url = search_unsplash_cover(access_key, keywords)
    if not image_url:
        return None

    # 3. 下载图片
    temp_path = download_image_to_temp(image_url)
    if not temp_path:
        return None

    # 4. 上传到微信
    media_id = upload_cover_material(token, temp_path)

    # 5. 清理临时文件
    try:
        os.unlink(temp_path)
    except:
        pass

    return media_id


# ================= Mermaid 渲染 =================

def render_mermaid_with_playwright(mermaid_code: str) -> str | None:
    """使用 Playwright 渲染 Mermaid 图表"""
    try:
        import playwright.sync_api as pw
    except ImportError:
        print("警告: playwright 库未安装")
        return None

    html_content = _build_mermaid_html(mermaid_code)

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            html_path = f.name

        output_path = html_path.replace('.html', '.png')

        with pw.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1000, 'height': 800}, device_scale_factor=2)
            page.goto(f'file://{html_path}')
            page.wait_for_timeout(3000)

            element = page.query_selector('.mermaid svg')
            if element:
                element.screenshot(path=output_path, scale='device', omit_background=True)
            else:
                page.screenshot(path=output_path, full_page=True)
            browser.close()

        os.unlink(html_path)
        return output_path
    except Exception as e:
        print(f"Playwright 渲染失败: {e}")
        return None


def _build_mermaid_html(mermaid_code: str) -> str:
    """构建 Mermaid 渲染用的 HTML"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{ margin: 0; padding: 80px; background: white; display: inline-block; }}
        #mermaid-container {{ background: white; }}
        .mermaid text {{ font-size: 16px !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif !important; }}
        .mermaid .edgeLabel {{ font-size: 14px !important; background-color: white !important; padding: 4px !important; }}
        .mermaid text.sequenceNumber, .mermaid .sequenceNumber text {{ fill: #fff !important; stroke: none !important; }}
    </style>
</head>
<body>
    <div id="mermaid-container">
        <pre class="mermaid">{mermaid_code}</pre>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{ fontSize: '16px', fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif' }},
            flowchart: {{ htmlLabels: true, curve: 'basis', padding: 40 }},
            sequence: {{ showSequenceNumbers: true, fontSize: 16 }}
        }});
    </script>
</body>
</html>"""


def render_mermaid_with_kroki(mermaid_code: str) -> str | None:
    """使用 Kroki.io API 渲染 Mermaid（备用方案）"""
    try:
        compressed = zlib.compress(mermaid_code.encode('utf-8'), level=9)
        encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
        kroki_url = f"https://kroki.io/mermaid/png/{encoded}"

        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
        response = requests.get(kroki_url, headers=headers, timeout=15)

        if response.status_code == 200 and response.content:
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
                f.write(response.content)
                return f.name

        print(f"Kroki.io 返回错误: {response.status_code}")
        return None
    except Exception as e:
        print(f"Kroki.io 渲染失败: {e}")
        return None


def render_mermaid_locally(mermaid_code: str) -> str | None:
    """多层降级策略渲染 Mermaid: Kroki.io -> Playwright -> None"""
    print("  [1/2] 尝试使用 Kroki.io 在线渲染...")
    result = render_mermaid_with_kroki(mermaid_code)
    if result:
        print("  ✓ Kroki.io 渲染成功")
        return result

    print("  [2/2] 尝试使用 Playwright 本地渲染...")
    result = render_mermaid_with_playwright(mermaid_code)
    if result:
        print("  ✓ Playwright 渲染成功")
        return result

    print("  所有渲染方案失败，将显示为代码块")
    return None


# ================= Markdown 预处理 =================

def process_mermaid(content: str) -> str:
    """将 Mermaid 代码块转换为图片或降级为代码块"""
    def repl(m):
        code = m.group(1).strip()
        print("\n处理 Mermaid 图表...")

        local_path = render_mermaid_locally(code)
        if local_path:
            return f'![MERMAID_DIAGRAM]({local_path})'

        # 降级为格式化代码块
        escaped = code.replace('<', '&lt;').replace('>', '&gt;')
        return f'''
<section class="mermaid-fallback" style="background: #f5f7fa; padding: 16px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #909399;">
  <p style="color: #606266; font-size: 14px; margin: 0 0 12px; font-weight: 600;">📊 流程图 (Mermaid)</p>
  <pre style="background: #fff; padding: 12px; border-radius: 4px; overflow-x: auto; margin: 0; font-family: Consolas, Monaco, monospace; font-size: 13px; line-height: 1.5; color: #303133;"><code>{escaped}</code></pre>
  <p style="color: #909399; font-size: 12px; margin: 12px 0 0; font-style: italic;">提示: 图表渲染暂时不可用，已显示原始代码</p>
</section>'''

    return re.sub(r'```mermaid\s*\n([\s\S]*?)```', repl, content)


def process_admonitions(content: str) -> str:
    """将 Admonition 代码块转换为 HTML"""
    def repl(m):
        ad_type = ADMONITION_ALIASES.get(m.group(1).lower(), m.group(1).lower())
        title = (m.group(2) or '').strip() or ad_type.capitalize()
        body = m.group(3)

        config = ADMONITION_TYPES.get(ad_type, ADMONITION_TYPES['note'])
        icon_svg = ADMONITION_ICONS.get(config['icon'], ADMONITION_ICONS['pencil'])
        body_html = markdown.markdown(body, extensions=['fenced_code', 'tables'])

        return f'''
<section class="admonition" style="border-radius: 4px; margin: 16px 0; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
  <section class="admonition-title" style="display: flex; align-items: center; padding: 8px 12px; background: {config['bg']};">
    <span style="color: {config['color']}; margin-right: 8px; display: flex; align-items: center;">{icon_svg}</span>
    <span style="font-weight: 600; color: {config['color']};">{title}</span>
  </section>
  <section class="admonition-content" style="padding: 12px 16px; background: {config['bg']}; border-left: 4px solid {config['color']};">
    <div style="font-size: 16px; color: #333; line-height: 1.6;">{body_html}</div>
  </section>
</section>'''

    return re.sub(r'```ad-(\w+)(?:[ \t]+title:[ \t]*(.*))?\n([\s\S]*?)```', repl, content)


def process_footnotes(content: str) -> str:
    """将链接转换为脚注形式"""
    links = []

    def repl(m):
        text, url = m.group(1), m.group(2)
        links.append({'text': text, 'url': url})
        idx = len(links)
        return f'<span style="color: #3370ff;">{text}</span><sup style="color: #3370ff; font-weight: bold;">[{idx}]</sup>'

    content = re.sub(r'(?<!!)\[(.*?)\]\((.*?)\)', repl, content)

    if links:
        content += '\n\n<div class="footnotes">'
        content += '<h4 style="font-size: 14px; color: #999; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 5px;">引用链接</h4>'
        for i, link in enumerate(links):
            content += f'<div class="footnote-item"><span style="color: #3370ff; font-weight: bold;">[{i+1}]</span> {link["text"]}: {link["url"]}</div>'
        content += '</div>'

    return content


def preprocess_markdown(body: str) -> str:
    """Markdown 预处理：清理列表空行、修复代码块等"""
    # 清理列表项间空行
    body = re.sub(r'(\d+\.\s+[^\n]+)\n+(?=\s*\d+\.\s+)', r'\1\n', body)
    body = re.sub(r'([-*+]\s+[^\n]+)\n+(?=\s*[-*+]\s+)', r'\1\n', body)
    body = re.sub(r'\n{3,}', '\n\n', body)

    # 确保列表前有空行
    body = _ensure_list_spacing(body)

    # 修复列表内代码块
    body = _fix_code_blocks_in_lists(body)

    # 移除孤立语言标签
    body = re.sub(
        r'\n\s*(JSON|PYTHON|JAVASCRIPT|JAVA|SHELL|BASH|SQL|XML|HTML|CSS|YAML|TOML)\s*\n\s*\n(\s*```)',
        r'\n\n\2', body, flags=re.IGNORECASE
    )

    # 预处理 JSON 注释
    body = _preprocess_json_comments(body)

    return body


def _ensure_list_spacing(content: str) -> str:
    """确保列表前有空行"""
    lines = content.split('\n')
    result = []

    for i, line in enumerate(lines):
        is_list_start = re.match(r'^(\s*)([-*+]|\d+\.)\s+', line)
        if is_list_start and i > 0:
            prev = lines[i - 1].strip()
            if (prev and
                not re.match(r'^([-*+]|\d+\.)\s+', prev) and
                not prev.startswith('#') and
                not prev.startswith('```') and
                not prev.startswith('>')):
                result.append('')
        result.append(line)

    return '\n'.join(result)


def _fix_code_blocks_in_lists(content: str) -> str:
    """修复列表项内代码块的格式问题"""
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        if re.match(r'^    ```\w*', line):
            code_block = [line.lstrip()]
            i += 1
            while i < len(lines):
                inner = lines[i]
                if re.match(r'^    ```\s*$', inner):
                    code_block.append('```')
                    i += 1
                    break
                code_block.append(re.sub(r'^    {1,2}', '', inner))
                i += 1
            result.extend([''] + code_block + [''])
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)


def _preprocess_json_comments(content: str) -> str:
    """移除 JSON 代码块中的注释"""
    def process_block(match):
        lang, code = match.group(1), match.group(2)
        if lang.lower() == 'json':
            code = '\n'.join(re.sub(r'\s*//[^"]*$', '', line) for line in code.split('\n'))
        return f'```{lang}\n{code}```'

    return re.sub(r'```(\w+)\n([\s\S]*?)```', process_block, content)


# ================= HTML 处理 =================

class WechatHTMLProcessor(HTMLParser):
    """微信兼容的 HTML 处理器"""

    def __init__(self):
        super().__init__()
        self.output = []
        self.list_stack = []
        self.in_pre = False
        self.in_li = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in ('ul', 'ol'):
            marker_type = 'num' if tag == 'ol' else 'bull'
            self.list_stack.append({'tag': tag, 'count': 1, 'marker_type': marker_type})
            self.output.append(self._build_tag(tag, self._inject_style(attrs, STYLES['list_container'])))
            return

        if tag == 'li':
            self.in_li = True
            self.output.append(self._build_tag(tag, self._inject_style(attrs, STYLES['list_item'])))
            if self.list_stack:
                current = self.list_stack[-1]
                level = len(self.list_stack) - 1
                if current['marker_type'] == 'num':
                    marker = f"{current['count']}. "
                    current['count'] += 1
                else:
                    marker = '◦ ' if level % 2 == 1 else '• '
                self.output.append(marker)
            return

        if tag == 'div' and 'highlight' in attrs_dict.get('class', '').split():
            self.output.append(self._build_tag(tag, self._inject_style(attrs, 'margin: 16px 0; padding: 0;')))
            return

        if tag == 'pre':
            self.in_pre = True
            self.output.append(self._build_tag(tag, self._inject_style(attrs, STYLES['pre'])))
            return

        if tag == 'code':
            if not self.in_pre and 'style' not in attrs_dict:
                self.output.append(self._build_tag(tag, self._inject_style(attrs, STYLES['inline_code'])))
            else:
                self.output.append(self._build_tag(tag, attrs))
            return

        if tag == 'p' and self.in_li:
            return

        self.output.append(self._build_tag(tag, attrs))

    def handle_endtag(self, tag):
        if tag in ('ul', 'ol') and self.list_stack:
            self.list_stack.pop()
        if tag == 'li':
            self.in_li = False
        if tag == 'pre':
            self.in_pre = False
        if tag == 'p' and self.in_li:
            self.output.append("<br>")
            return
        self.output.append(f"</{tag}>")

    def handle_data(self, data):
        self.output.append(data)

    def handle_entityref(self, name):
        self.output.append(f'&{name};')

    def handle_charref(self, name):
        self.output.append(f'&#{name};')

    def _build_tag(self, tag, attrs) -> str:
        if not attrs:
            return f"<{tag}>"
        if isinstance(attrs, list):
            attrs_str = " ".join(f'{k}="{v}"' for k, v in attrs)
        else:
            attrs_str = f'style="{attrs}"'
        return f"<{tag} {attrs_str}>"

    def _inject_style(self, attrs, style_to_add):
        new_attrs = dict(attrs)
        if 'style="' in style_to_add:
            match = re.search(r'style="([^"]*)"', style_to_add)
            style_to_add = match.group(1) if match else style_to_add

        current = new_attrs.get('style', '')
        if current and not current.strip().endswith(';'):
            current += ';'
        new_attrs['style'] = current + style_to_add
        return list(new_attrs.items())


def md_to_html(md_content: str) -> str:
    """Markdown 转 HTML"""
    html = markdown.markdown(
        md_content,
        extensions=['fenced_code', 'tables', 'codehilite'],
        extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'guess_lang': True,
                'use_pygments': True,
                'noclasses': True
            }
        }
    )

    final_html = f'''
    <section id="nice" style="background-color: #fffdf9; padding: 20px; border-radius: 8px;">
        {BASIC_STYLE}
        {html}
    </section>
    '''

    # 应用标签样式
    for tag in ['h1', 'h2', 'h3', 'h4', 'strong']:
        final_html = final_html.replace(f'<{tag}>', f'<{tag} style="{STYLES[tag]}">')

    final_html = final_html.replace('<th>', f'<th style="{STYLES["th"]}">')
    final_html = final_html.replace('<td>', f'<td style="{STYLES["td"]}">')
    final_html = re.sub(r'<hr\s*/?>', f'<hr style="{STYLES["hr"]}">', final_html)

    # 使用 HTML 处理器处理列表和代码块
    processor = WechatHTMLProcessor()
    processor.feed(final_html)
    final_html = "".join(processor.output)

    # 后处理
    final_html = _simplify_list_items(final_html)
    final_html = re.sub(r'</strong>\s*(<br\s*/?>)?\s*([：:])', r'\2</strong>', final_html)
    final_html = _convert_whitespace_in_code(final_html)
    final_html = _compress_html_preserve_pre(final_html)

    return final_html


def _simplify_list_items(html: str) -> str:
    """清理空列表项"""
    html = re.sub(r'<li[^>]*>\s*</li>', '', html)
    html = re.sub(r'<li[^>]*>\s*<p[^>]*>\s*</p>\s*</li>', '', html)
    html = re.sub(r'<p[^>]*>\s*</p>', '', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html


def _convert_whitespace_in_code(html: str) -> str:
    """将代码块内空白转换为 HTML 实体"""
    def convert_text(text):
        if not text:
            return ''
        return text.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;').replace(' ', '&nbsp;').replace('\n', '<br>')

    def process_pre_content(content):
        content = re.sub(r'<span style="color: #BBB">([^<]*)</span>', r'\1', content)
        result = []
        last_end = 0
        for m in re.finditer(r'<[^>]+>', content):
            result.append(convert_text(content[last_end:m.start()]))
            result.append(m.group(0))
            last_end = m.end()
        result.append(convert_text(content[last_end:]))
        return ''.join(result)

    return re.sub(
        r'(<pre[^>]*>)([\s\S]*?)</pre>',
        lambda m: f'{m.group(1)}{process_pre_content(m.group(2))}</pre>',
        html
    )


def _compress_html_preserve_pre(html: str) -> str:
    """压缩 HTML 但保留 pre 块内容"""
    pre_blocks = []

    def save_pre(m):
        pre_blocks.append(m.group(0))
        return f'__PRE_PLACEHOLDER_{len(pre_blocks) - 1}__'

    html = re.sub(r'<pre[^>]*>[\s\S]*?</pre>', save_pre, html)
    html = re.sub(r'>\s+<', '><', html)

    for i, block in enumerate(pre_blocks):
        html = html.replace(f'__PRE_PLACEHOLDER_{i}__', block)

    return html


# ================= 工作流 =================

def process_content_workflow(content: str, token: str) -> tuple[dict, str]:
    """完整的 Markdown 处理工作流"""
    frontmatter = {}
    body = content

    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end():]

    body = preprocess_markdown(body)
    body = process_mermaid(body)

    # 上传图片
    def replace_img(m):
        alt, src = m.group(1), m.group(2)
        print(f"正在上传图片: {src}")
        wechat_url = upload_image(token, src)
        if not wechat_url:
            return m.group(0)

        is_mermaid = 'MERMAID_DIAGRAM' in alt or '/tmp' in src
        wrapper_class = 'mermaid-wrapper' if is_mermaid else 'image-wrapper'
        alt_text = '流程图' if is_mermaid else alt
        shadow = '0 2px 8px rgba(0,0,0,0.1)' if is_mermaid else '0 2px 4px rgba(0,0,0,0.1)'

        return f'''
<section class="{wrapper_class}" style="text-align: center; margin: {'24' if is_mermaid else '20'}px 0;">
  <img src="{wechat_url}" alt="{alt_text}" style="max-width: 100%; height: auto; display: inline-block; border-radius: 4px; box-shadow: {shadow};" />
</section>'''

    body = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_img, body)
    body = process_admonitions(body)
    body = process_footnotes(body)

    return frontmatter, body


def publish_draft(token: str, article_data: dict) -> dict:
    """发布草稿到微信"""
    url = f"{WECHAT_API_BASE}/draft/add?access_token={token}"
    json_bytes = json.dumps(article_data, ensure_ascii=False).encode('utf-8')
    resp = requests.post(url, data=json_bytes, headers={'Content-Type': 'application/json; charset=utf-8'})
    return resp.json()


def main(file_path: str) -> None:
    print(f"开始处理文件: {file_path}")

    try:
        config = load_config()
        token = get_access_token(config)
        print("Token 获取成功")
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    with open(file_path, 'r') as f:
        raw_content = f.read()

    print("正在处理 Markdown 内容...")
    frontmatter, processed_body = process_content_workflow(raw_content, token)
    html_content = md_to_html(processed_body)

    thumb_media_id = frontmatter.get('thumb_media_id')

    # 封面获取优先级：
    # 1. frontmatter 中的 thumb_media_id
    # 2. frontmatter 中的 banner/banner_path（用户提供图片）
    # 3. Unsplash 自动搜索
    # 4. 默认封面

    if not thumb_media_id:
        # 尝试用户提供的 banner 图片
        banner = frontmatter.get('banner')  # 网络 URL
        banner_path = frontmatter.get('banner_path')  # 本地路径

        if banner and banner.startswith(('http://', 'https://')):
            # 网络图片：先下载再上传
            print(f"正在下载用户封面: {banner}")
            temp_path = download_image_to_temp(banner)
            if temp_path:
                print(f"正在上传用户封面...")
                thumb_media_id = upload_cover_material(token, temp_path)
                try:
                    os.unlink(temp_path)
                except:
                    pass
                if thumb_media_id:
                    print(f"  ✓ 封面上传成功: {thumb_media_id[:20]}...")
                else:
                    print(f"  封面上传失败")
        elif banner_path:
            # 本地图片：直接上传
            print(f"正在上传用户封面: {banner_path}")
            thumb_media_id = upload_cover_material(token, banner_path)

    if not thumb_media_id:
        # 尝试 Unsplash 自动搜索
        title = frontmatter.get('title', "")
        digest = frontmatter.get('digest', "")
        thumb_media_id = get_auto_cover(config, token, title, digest)

    if not thumb_media_id:
        # 使用默认封面
        thumb_media_id = config.get('default_thumb_media_id')

    if not thumb_media_id:
        print("警告: 未找到封面图 (thumb_media_id)")

    article = {
        "title": frontmatter.get('title', "未命名文章"),
        "author": frontmatter.get('author', config.get('default_author')),
        "digest": frontmatter.get('digest', ""),
        "content": html_content,
        "content_source_url": frontmatter.get('source_url', ""),
        "thumb_media_id": thumb_media_id,
        "need_open_comment": frontmatter.get('open_comment', 0)
    }

    print("正在发布到草稿箱...")
    result = publish_draft(token, {"articles": [article]})
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
