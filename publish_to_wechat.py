#!/usr/bin/env python3
import os
import re
import json
import base64
import tempfile
import zlib
import html as html_lib
import ipaddress
import mimetypes
import shutil
import time
from datetime import datetime
import socket
from urllib.parse import unquote, urljoin, urlparse
from html.parser import HTMLParser

import requests
import yaml
import markdown

# ================= 配置 =================

CONFIG_FILE = "config/wechat-credentials.local.md"
WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin"
DEFAULT_HTTP_TIMEOUT = 30
TOKEN_REFRESH_MARGIN_SECONDS = 300
TOKEN_INVALID_ERRCODES = {40001, 42001}
SENSITIVE_KEYS = {"secret", "access_token", "token", "appid"}
MAX_REMOTE_IMAGE_BYTES = 10 * 1024 * 1024
REMOTE_IMAGE_CHUNK_SIZE = 64 * 1024
WECHAT_IMAGE_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
}
COVER_SOURCE_FIELDS = ('banner', 'banner_path', 'cover', 'cover_image', 'thumbnail', 'image', 'featured_image')
AI_COVER_CACHE_DIRNAME = '.wechat-cover-cache'
AI_COVER_DEFAULT_PROMPT = """根据下面的微信公众号文章内容生成一张横版封面图。
要求：画面适合微信公众号封面，现代、清晰、有主题感，不要生成可读文字、Logo、水印或二维码。

标题：{title}
摘要：{digest}
正文：{content}
"""
AI_COVER_DEFAULTS = {
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'endpoint': '/images/generations',
        'size': '1536x640',
    },
    'gemini': {
        'base_url': 'https://generativelanguage.googleapis.com/v1beta',
        'aspect_ratio': '16:9',
    },
    'doubao': {
        'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
        'endpoint': '/images/generations',
        'model': 'doubao-seedream-5-0-260128',
        'size': '2K',
        'output_format': 'png',
    },
}
AI_COVER_PROVIDER_ALIASES = {
    'nanobanana': 'gemini',
    'nano-banana': 'gemini',
}
LEGACY_AUTO_COVER_HOSTS = {'images.unsplash.com', 'plus.unsplash.com', 'source.unsplash.com'}

GENERATED_MERMAID_IMAGES = set()
OBSIDIAN_SEARCH_SKIP_DIRS = {'.git', '.obsidian', '.trash', '.venv', '__pycache__', 'node_modules'}

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

def is_remote_url(value: str) -> bool:
    return urlparse(value.strip()).scheme in ('http', 'https')


def _is_disallowed_ip(ip_text: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return True

    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _validate_remote_image_url(image_url: str) -> tuple[str | None, str | None]:
    """校验远程图片 URL，避免 SSRF 到内网或本机地址。"""
    source = image_url.strip()
    parsed = urlparse(source)

    if parsed.scheme != 'https':
        return None, "远程图片仅允许 https URL"
    if not parsed.hostname:
        return None, "远程图片 URL 缺少主机名"
    if parsed.username or parsed.password:
        return None, "远程图片 URL 不允许包含认证信息"

    host = parsed.hostname.rstrip('.').lower()
    if host in {'localhost', 'localhost.localdomain'} or host.endswith('.localhost'):
        return None, "远程图片不允许使用 localhost"

    try:
        ipaddress.ip_address(host)
        resolved_ips = [host]
    except ValueError:
        try:
            resolved_ips = [item[4][0] for item in socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)]
        except socket.gaierror as e:
            return None, f"远程图片主机解析失败: {e}"

    if not resolved_ips:
        return None, "远程图片主机解析为空"
    for ip_text in set(resolved_ips):
        if _is_disallowed_ip(ip_text):
            return None, f"远程图片主机解析到不安全地址: {ip_text}"

    return source, None


def _is_legacy_auto_cover_url(cover_source: str) -> bool:
    """识别旧版自动封面留下的 Unsplash URL。"""
    if not is_remote_url(cover_source):
        return False
    host = (urlparse(cover_source).hostname or '').rstrip('.').lower()
    return host in LEGACY_AUTO_COVER_HOSTS


def _safe_get_remote_image(image_url: str, *, timeout: int = 30, max_redirects: int = 5) -> requests.Response:
    """下载远程图片，禁用自动重定向并逐跳校验目标。"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    current_url = image_url

    for _ in range(max_redirects + 1):
        safe_url, error = _validate_remote_image_url(current_url)
        if error:
            raise ValueError(error)

        resp = request_response(
            "GET",
            safe_url,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
            stream=True,
        )
        if resp.is_redirect or resp.is_permanent_redirect:
            location = resp.headers.get('Location')
            resp.close()
            if not location:
                raise ValueError("远程图片重定向缺少 Location")
            current_url = urljoin(safe_url, location)
            continue

        return resp

    raise ValueError("远程图片重定向次数过多")


def safe_unlink(path: str | None) -> None:
    if not path:
        return
    try:
        os.unlink(path)
    except OSError:
        pass


def find_obsidian_vault_root(article_dir: str) -> str:
    """向上查找 Obsidian vault 根目录；找不到时退回文章目录。"""
    current = os.path.realpath(os.path.abspath(article_dir))
    while True:
        if os.path.isdir(os.path.join(current, '.obsidian')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return os.path.realpath(os.path.abspath(article_dir))
        current = parent


def _is_within_dir(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([root, path]) == root
    except ValueError:
        return False


def _find_unique_vault_file(filename: str, vault_root: str) -> tuple[str | None, str | None]:
    """在 vault 内按文件名查找唯一附件，避免恢复不安全的 cwd 兜底。"""
    matches = []
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in OBSIDIAN_SEARCH_SKIP_DIRS and not d.startswith('.git')]
        if filename in files:
            matches.append(os.path.realpath(os.path.join(root, filename)))
            if len(matches) > 1:
                return None, f"Vault 中存在多个同名图片，请在引用中写相对路径: {filename}"

    if matches:
        return matches[0], None
    return None, None


def resolve_image_source(image_path_or_url: str, article_dir: str, vault_root: str | None = None) -> tuple[str | None, str | None]:
    """解析图片路径：URL 原样返回，本地相对路径基于文章目录/vault 根目录解析。"""
    source = unquote(image_path_or_url.strip())
    if not source:
        return None, "图片路径为空"

    if is_remote_url(source):
        return _validate_remote_image_url(source)

    parsed = urlparse(source)
    if parsed.scheme:
        return None, "本地图片不允许使用 URL scheme"
    if os.path.isabs(source):
        return None, "本地图片必须使用文章目录内的相对路径"
    if any(part == '..' for part in source.replace('\\', '/').split('/')):
        return None, "本地图片路径不允许包含 .."

    article_root = os.path.realpath(os.path.abspath(article_dir))
    vault_root = os.path.realpath(os.path.abspath(vault_root or find_obsidian_vault_root(article_root)))
    search_roots = []
    for root in [article_root, vault_root]:
        if root not in search_roots:
            search_roots.append(root)

    for root in search_roots:
        candidate = os.path.realpath(os.path.abspath(os.path.join(root, source)))
        if not _is_within_dir(candidate, root):
            continue
        if os.path.exists(candidate):
            return candidate, None

    if os.path.basename(source) == source and vault_root:
        found, error = _find_unique_vault_file(source, vault_root)
        if error:
            return None, error
        if found:
            return found, None

    return None, f"本地图片不存在: {source} (已查找文章目录和 vault 根目录)"


def parse_obsidian_image_embed(target: str) -> tuple[str, str]:
    """解析 Obsidian 图片嵌入语法中的路径和说明。"""
    src, _, option = target.partition('|')
    src = src.strip()
    option = option.strip()

    # ![[image.png|300]] 中的数字通常是显示宽度，发布时忽略。
    if option and not re.fullmatch(r'\d+(?:px)?', option):
        return src, option

    basename = os.path.basename(src)
    alt = os.path.splitext(basename)[0] if basename else ""
    return src, alt


def build_wechat_image_html(wechat_url: str, alt: str, source: str) -> str:
    is_mermaid = 'MERMAID_DIAGRAM' in alt
    wrapper_class = 'mermaid-wrapper' if is_mermaid else 'image-wrapper'
    alt_text = '流程图' if is_mermaid else alt
    shadow = '0 2px 8px rgba(0,0,0,0.1)' if is_mermaid else '0 2px 4px rgba(0,0,0,0.1)'

    return f'''
<section class="{wrapper_class}" style="text-align: center; margin: {'24' if is_mermaid else '20'}px 0;">
  <img src="{html_lib.escape(wechat_url, quote=True)}" alt="{html_lib.escape(alt_text, quote=True)}" style="max-width: 100%; height: auto; display: inline-block; border-radius: 4px; box-shadow: {shadow};" />
</section>'''


class WechatRequestError(RuntimeError):
    """HTTP/JSON 层错误，消息中不包含完整 token/secret。"""


def _redact_value(value):
    if isinstance(value, dict):
        return {
            key: ("<redacted>" if key in SENSITIVE_KEYS else _redact_value(val))
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_value(item) for item in value)
    return value


def _redact_text(value: str) -> str:
    value = re.sub(r'((?:access_token|secret|token|appid)=)[^&\s]+', r'\1<redacted>', value)
    value = re.sub(r'("?(?:access_token|secret|token|appid)"?\s*[:=]\s*)["\']?[^,"\'\s}]+', r'\1<redacted>', value)
    return value


def _safe_error_detail(data) -> str:
    try:
        return _redact_text(json.dumps(_redact_value(data), ensure_ascii=False))
    except Exception:
        return _redact_text(str(data))


def request_response(method: str, url: str, *, timeout: int = DEFAULT_HTTP_TIMEOUT, **kwargs) -> requests.Response:
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        response = getattr(e, 'response', None)
        detail = ""
        if response is not None:
            try:
                detail = response.text[:1000]
            except Exception:
                detail = ""
        suffix = f"; 响应: {_redact_text(detail)}" if detail else ""
        raise WechatRequestError(f"HTTP 请求失败: {_redact_text(str(e))}{suffix}") from e


def request_json(method: str, url: str, *, timeout: int = DEFAULT_HTTP_TIMEOUT, **kwargs) -> dict:
    response = request_response(method, url, timeout=timeout, **kwargs)
    try:
        return response.json()
    except ValueError as e:
        raise WechatRequestError(f"响应不是合法 JSON: {_redact_text(response.text[:300])}") from e


def _parse_token_expires(value) -> float:
    if value in (None, ""):
        return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):
        normalized = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).timestamp()
        except ValueError:
            return 0

    return 0


def _token_is_valid(config: dict) -> bool:
    token = config.get('access_token')
    expires_at = _parse_token_expires(config.get('token_expires'))
    return bool(token and expires_at > time.time() + TOKEN_REFRESH_MARGIN_SECONDS)

def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件 {CONFIG_FILE} 不存在")
    with open(CONFIG_FILE, 'r') as f:
        content = f.read()
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    return yaml.safe_load(match.group(1)) if match else {}


def get_access_token(config: dict, *, force_refresh: bool = False) -> str:
    if not force_refresh and _token_is_valid(config):
        return config['access_token']

    data = request_json("GET", f"{WECHAT_API_BASE}/token", params={
        "grant_type": "client_credential",
        "appid": config['appid'],
        "secret": config['secret']
    })

    if 'access_token' not in data:
        raise WechatRequestError(f"获取 Token 失败: {_safe_error_detail(data)}")

    config['access_token'] = data['access_token']
    config['token_expires'] = int(time.time()) + int(data.get('expires_in', 7200))
    return config['access_token']


def _convert_raster_to_png(image_path: str) -> str:
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("需要安装 Pillow 才能转换 WebP/非微信格式图片: pip install Pillow") from e

    with Image.open(image_path) as img:
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            output_path = f.name
        img.save(output_path, format='PNG')
        return output_path


def _convert_svg_to_png(image_path: str) -> str:
    try:
        import cairosvg
    except ImportError as e:
        raise RuntimeError("需要安装 CairoSVG 才能转换 SVG 图片: pip install cairosvg") from e

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
        output_path = f.name
    try:
        cairosvg.svg2png(url=image_path, write_to=output_path)
        return output_path
    except Exception:
        safe_unlink(output_path)
        raise


def prepare_wechat_image_for_upload(image_path: str) -> tuple[str, str, str, str | None]:
    """返回可被微信 uploadimg 接受的 path/filename/content_type/temp_path。"""
    ext = os.path.splitext(image_path)[1].lower()
    if ext in WECHAT_IMAGE_TYPES:
        return image_path, os.path.basename(image_path) or f'image{ext}', WECHAT_IMAGE_TYPES[ext], None

    if ext == '.svg':
        converted_path = _convert_svg_to_png(image_path)
    else:
        converted_path = _convert_raster_to_png(image_path)

    original_name = os.path.splitext(os.path.basename(image_path))[0] or 'image'
    print(f"  图片格式 {ext or 'unknown'} 不被微信支持，已转换为 PNG")
    return converted_path, f"{original_name}.png", 'image/png', converted_path


def upload_image(token: str, image_path_or_url: str) -> str | None:
    """上传图片到微信，支持本地路径和远程 URL"""
    url = f"{WECHAT_API_BASE}/media/uploadimg?access_token={token}"
    temp_path = None
    converted_path = None

    if is_remote_url(image_path_or_url):
        temp_path = download_image_to_temp(image_path_or_url)
        if not temp_path:
            return None
        upload_path = temp_path
    else:
        if not os.path.exists(image_path_or_url):
            print(f"本地图片不存在: {image_path_or_url}")
            return None
        upload_path = image_path_or_url

    try:
        upload_path, filename, content_type, converted_path = prepare_wechat_image_for_upload(upload_path)
        with open(upload_path, 'rb') as f:
            data = request_json("POST", url, files={'media': (filename, f, content_type)})
        if 'url' not in data:
            print(f"上传图片失败: {_safe_error_detail(data)}")
            return None
        return data['url']
    except Exception as e:
        print(f"上传图片失败: {e}")
        return None
    finally:
        safe_unlink(converted_path)
        safe_unlink(temp_path)


# ================= AI 封面功能 =================

def _strip_markdown_for_prompt(body: str, limit: int = 1200) -> str:
    """提取一段适合放入生图提示词的正文摘要。"""
    text = re.sub(r'```[\s\S]*?```', ' ', body)
    text = re.sub(r'!\[\[([^\]]+)\]\]', ' ', text)
    text = re.sub(r'!\[(.*?)\]\((.*?)\)', ' ', text)
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[#>*_`~\-\|]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:limit]


def _format_ai_cover_prompt(ai_config: dict, frontmatter: dict, body: str) -> str:
    template = ai_config.get('prompt_template') or AI_COVER_DEFAULT_PROMPT
    values = {
        'title': frontmatter.get('title', ''),
        'digest': frontmatter.get('digest', ''),
        'content': _strip_markdown_for_prompt(body),
    }
    try:
        return template.format(**values)
    except KeyError as e:
        raise ValueError(f"AI 封面 prompt_template 包含未知占位符: {e}") from e


def _extract_generated_image(data: dict) -> tuple[str | None, str | None]:
    """兼容常见生图响应，返回 (b64_json, url)。"""
    candidates = []
    for key in ('data', 'images', 'output'):
        value = data.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    candidates.append(item)
                elif isinstance(item, str):
                    if item.startswith('http://') or item.startswith('https://'):
                        return None, item
                    return item, None
        elif isinstance(value, dict):
            candidates.append(value)
        elif isinstance(value, str):
            if value.startswith('http://') or value.startswith('https://'):
                return None, value
            return value, None
    candidates.append(data)

    for candidate in data.get('candidates', []):
        if not isinstance(candidate, dict):
            continue
        content = candidate.get('content') or {}
        parts = content.get('parts') or []
        candidates.extend(part for part in parts if isinstance(part, dict))

    for item in candidates:
        b64_value = item.get('b64_json') or item.get('base64') or item.get('image_base64')
        url_value = item.get('url') or item.get('image_url')
        inline_data = item.get('inlineData') or item.get('inline_data')
        if isinstance(inline_data, dict):
            b64_value = b64_value or inline_data.get('data')
        if b64_value:
            if isinstance(b64_value, str) and b64_value.startswith('data:image'):
                b64_value = b64_value.split(',', 1)[-1]
            return b64_value, None
        if url_value:
            return None, url_value

    return None, None


def _write_base64_image_to_temp(b64_value: str, suffix: str = '.png') -> str:
    image_bytes = base64.b64decode(b64_value)
    with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
        f.write(image_bytes)
        return f.name


def _copy_image_to_temp(image_path: str, suffix: str = '.png') -> str:
    with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
        temp_path = f.name
    try:
        shutil.copyfile(image_path, temp_path)
        return temp_path
    except Exception:
        safe_unlink(temp_path)
        raise


def _ai_cover_cache_enabled(provider: str, ai_config: dict) -> bool:
    return provider == 'doubao' and ai_config.get('cache_enabled', True)


def _ai_cover_cache_path(article_dir: str, provider: str, ai_config: dict, frontmatter: dict, prompt: str) -> str:
    cache_payload = {
        'provider': provider,
        'model': ai_config.get('model') or AI_COVER_DEFAULTS.get(provider, {}).get('model'),
        'size': ai_config.get('size') or AI_COVER_DEFAULTS.get(provider, {}).get('size'),
        'output_format': ai_config.get('output_format') or AI_COVER_DEFAULTS.get(provider, {}).get('output_format'),
        'response_format': ai_config.get('response_format') or '',
        'watermark': ai_config.get('watermark', False),
        'title': frontmatter.get('title', ''),
        'digest': frontmatter.get('digest', ''),
        'prompt': prompt,
    }
    key = zlib.crc32(json.dumps(cache_payload, ensure_ascii=False, sort_keys=True).encode('utf-8'))
    cache_dir = os.path.join(os.path.realpath(article_dir), AI_COVER_CACHE_DIRNAME)
    return os.path.join(cache_dir, f'{key:08x}.png')


def _store_ai_cover_cache(source_path: str, cache_path: str) -> None:
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    temp_cache_path = f"{cache_path}.tmp"
    try:
        shutil.copyfile(source_path, temp_cache_path)
        os.replace(temp_cache_path, cache_path)
    finally:
        safe_unlink(temp_cache_path)


def _ai_cover_endpoint(provider: str, ai_config: dict) -> str:
    defaults = AI_COVER_DEFAULTS[provider]
    base_url = (ai_config.get('base_url') or defaults['base_url']).rstrip('/')
    if provider == 'gemini':
        endpoint = ai_config.get('endpoint')
        if endpoint:
            endpoint = endpoint.format(model=ai_config.get('model', ''))
            if endpoint.startswith('http://') or endpoint.startswith('https://'):
                return endpoint
            return f"{base_url}/{endpoint.lstrip('/')}"
        model = ai_config.get('model')
        return f"{base_url}/models/{model}:generateContent"

    endpoint = ai_config.get('endpoint') or defaults['endpoint']
    if endpoint.startswith('http://') or endpoint.startswith('https://'):
        return endpoint
    return f"{base_url}/{endpoint.lstrip('/')}"


def _normalize_ai_cover_provider(provider: str) -> str:
    normalized = provider.lower()
    return AI_COVER_PROVIDER_ALIASES.get(normalized, normalized)


def _request_ai_cover(provider: str, ai_config: dict, prompt: str) -> dict:
    if provider not in AI_COVER_DEFAULTS:
        raise ValueError(f"不支持的 AI 封面 provider: {provider}")

    api_key = ai_config.get('api_key')
    if not api_key:
        raise ValueError("AI 封面未配置 api_key")

    model = ai_config.get('model')
    if not model:
        raise ValueError("AI 封面未配置 model")

    if provider == 'gemini':
        image_config = {
            'aspectRatio': ai_config.get('aspect_ratio') or ai_config.get('aspectRatio') or AI_COVER_DEFAULTS[provider]['aspect_ratio']
        }
        image_size = ai_config.get('image_size') or ai_config.get('imageSize')
        if image_size:
            image_config['imageSize'] = image_size

        payload = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'responseModalities': ['TEXT', 'IMAGE'],
                'imageConfig': image_config,
            },
        }
        headers = {'x-goog-api-key': api_key, 'Content-Type': 'application/json'}
        return request_json(
            "POST",
            _ai_cover_endpoint(provider, ai_config),
            headers=headers,
            json=payload,
            timeout=ai_config.get('timeout', DEFAULT_HTTP_TIMEOUT),
        )

    if provider == 'doubao':
        defaults = AI_COVER_DEFAULTS[provider]
        payload = {
            'model': model,
            'prompt': prompt,
            'size': ai_config.get('size') or defaults['size'],
            'output_format': ai_config.get('output_format') or defaults['output_format'],
            'watermark': ai_config.get('watermark', False),
        }
        response_format = ai_config.get('response_format')
        if response_format:
            payload['response_format'] = response_format
        stream = ai_config.get('stream')
        if stream is not None:
            payload['stream'] = bool(stream)
        image = ai_config.get('image')
        if image:
            payload['image'] = image
        sequential = ai_config.get('sequential_image_generation')
        if sequential:
            payload['sequential_image_generation'] = sequential
        sequential_options = ai_config.get('sequential_image_generation_options')
        if sequential_options:
            payload['sequential_image_generation_options'] = sequential_options
        tools = ai_config.get('tools')
        if tools:
            payload['tools'] = tools
        seedream_options = ai_config.get('optimize_prompt_options')
        if seedream_options:
            payload['optimize_prompt_options'] = seedream_options

        headers = {'Authorization': f"Bearer {api_key}", 'Content-Type': 'application/json'}
        return request_json(
            "POST",
            _ai_cover_endpoint(provider, ai_config),
            headers=headers,
            json=payload,
            timeout=ai_config.get('timeout', DEFAULT_HTTP_TIMEOUT),
        )

    payload = {
        'model': model,
        'prompt': prompt,
        'size': ai_config.get('size') or AI_COVER_DEFAULTS[provider]['size'],
        'n': ai_config.get('n', 1),
    }
    response_format = ai_config.get('response_format')
    if response_format:
        payload['response_format'] = response_format

    headers = {'Authorization': f"Bearer {api_key}", 'Content-Type': 'application/json'}
    return request_json(
        "POST",
        _ai_cover_endpoint(provider, ai_config),
        headers=headers,
        json=payload,
        timeout=ai_config.get('timeout', DEFAULT_HTTP_TIMEOUT),
    )


def generate_ai_cover_image(config: dict, frontmatter: dict, body: str, article_dir: str | None = None) -> str | None:
    """生成 AI 封面图片到临时文件，返回本地路径；失败时抛错给调用方降级处理。"""
    ai_config = config.get('ai_cover') or {}
    if not ai_config.get('enabled', False):
        return None

    provider = _normalize_ai_cover_provider(ai_config.get('provider') or 'openai')
    prompt = _format_ai_cover_prompt(ai_config, frontmatter, body)
    cache_path = None
    if article_dir and _ai_cover_cache_enabled(provider, ai_config):
        cache_path = _ai_cover_cache_path(article_dir, provider, ai_config, frontmatter, prompt)
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            print(f"  ✓ 使用已缓存的豆包封面: {cache_path}")
            return _copy_image_to_temp(cache_path, ai_config.get('output_suffix') or '.png')

    data = _request_ai_cover(provider, ai_config, prompt)
    b64_value, image_url = _extract_generated_image(data)

    result_path = None
    if b64_value:
        result_path = _write_base64_image_to_temp(b64_value)
    elif image_url:
        safe_image_url, error = _validate_remote_image_url(image_url)
        if error:
            raise ValueError(f"AI 封面返回了不安全的图片 URL: {error}")
        temp_path = download_image_to_temp(safe_image_url)
        if not temp_path:
            raise RuntimeError("AI 封面图片下载失败")
        result_path = temp_path
    else:
        raise RuntimeError(f"AI 封面响应中未找到图片: {_safe_error_detail(data)}")

    if cache_path:
        _store_ai_cover_cache(result_path, cache_path)
        print(f"  ✓ 豆包封面已缓存: {cache_path}")

    return result_path


def download_image_to_temp(image_url: str, max_bytes: int = MAX_REMOTE_IMAGE_BYTES) -> str | None:
    """流式下载远程图片到临时文件，超过 max_bytes 时拒绝。"""
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    resp = None
    temp_path = None
    keep_temp = False
    try:
        resp = _safe_get_remote_image(image_url, timeout=30)

        if resp.status_code != 200:
            print(f"  下载图片失败，状态码: {resp.status_code}")
            return None

        content_length = resp.headers.get('Content-Length')
        if content_length and int(content_length) > max_bytes:
            print(f"  图片超过大小限制: {int(content_length)} > {max_bytes}")
            return None

        content_type = resp.headers.get('Content-Type', 'image/jpeg').split(';', 1)[0].lower()
        ext_map = {
            'image/png': '.png', 'image/jpeg': '.jpg', 'image/jpg': '.jpg',
            'image/gif': '.gif', 'image/webp': '.webp', 'image/svg+xml': '.svg'
        }
        ext = ext_map.get(content_type) or os.path.splitext(urlparse(image_url).path)[1] or '.jpg'

        total = 0
        with tempfile.NamedTemporaryFile(mode='wb', suffix=ext, delete=False) as f:
            temp_path = f.name
            for chunk in resp.iter_content(chunk_size=REMOTE_IMAGE_CHUNK_SIZE):
                if not chunk:
                    continue
                total += len(chunk)
                if total > max_bytes:
                    print(f"  图片超过大小限制: {total} > {max_bytes}")
                    return None
                f.write(chunk)

            if total == 0:
                print("  下载图片失败: 响应内容为空")
                return None

            keep_temp = True
            return f.name
    except Exception as e:
        print(f"  下载图片失败: {e}")
        return None
    finally:
        if resp is not None:
            close = getattr(resp, 'close', None)
            if close:
                close()
        if temp_path and not keep_temp:
            safe_unlink(temp_path)


def upload_cover_material(token: str, image_path: str) -> str | None:
    """上传封面图片为微信永久素材，返回 media_id"""
    url = f"{WECHAT_API_BASE}/material/add_material?access_token={token}&type=image"
    converted_path = None

    try:
        upload_path, filename, content_type, converted_path = prepare_wechat_image_for_upload(image_path)
        with open(upload_path, 'rb') as f:
            files = {'media': (filename, f, content_type)}
            data = request_json("POST", url, files=files)

        if 'media_id' in data:
            print(f"  ✓ 封面上传成功: {data['media_id'][:20]}...")
            return data['media_id']

        print(f"  封面上传失败: {_safe_error_detail(data)}")
        return None
    except Exception as e:
        print(f"  封面上传失败: {e}")
        return None
    finally:
        safe_unlink(converted_path)


def upload_explicit_cover(token: str, cover_source: str, article_dir: str, label: str) -> str:
    """上传用户显式配置的封面，失败时中止，避免静默落到默认封面。"""
    if is_remote_url(cover_source):
        safe_cover_source, error = _validate_remote_image_url(cover_source)
        if error:
            raise RuntimeError(f"{label} 封面处理失败: {error}")

        print(f"正在下载用户封面: {cover_source}")
        temp_path = download_image_to_temp(safe_cover_source)
        if not temp_path:
            raise RuntimeError(f"{label} 封面下载失败: {cover_source}")

        try:
            print("正在上传用户封面...")
            media_id = upload_cover_material(token, temp_path)
        finally:
            safe_unlink(temp_path)

        if not media_id:
            raise RuntimeError(f"{label} 封面上传失败: {cover_source}")
        return media_id

    resolved_cover_path, error = resolve_image_source(cover_source, article_dir)
    if error:
        raise RuntimeError(f"{label} 封面处理失败: {error}")

    print(f"正在上传用户封面: {cover_source}")
    if resolved_cover_path != cover_source:
        print(f"  解析路径: {resolved_cover_path}")

    media_id = upload_cover_material(token, resolved_cover_path)
    if not media_id:
        raise RuntimeError(f"{label} 封面上传失败: {cover_source}")
    return media_id


def resolve_thumb_media_id(frontmatter: dict, config: dict, token: str, article_dir: str, body: str = "") -> str | None:
    """按优先级获取草稿封面 media_id。"""
    thumb_media_id = frontmatter.get('thumb_media_id')
    if thumb_media_id:
        print("使用 frontmatter 中的 thumb_media_id")
        return thumb_media_id

    # 兼容常见 frontmatter 封面字段，值可为网络 URL 或本地/vault 相对路径。
    for field in COVER_SOURCE_FIELDS:
        cover_source = frontmatter.get(field)
        if cover_source:
            if (config.get('ai_cover') or {}).get('enabled', False) and _is_legacy_auto_cover_url(str(cover_source)):
                print(f"跳过旧版 Unsplash 自动封面字段 {field}，改用 AI 封面")
                continue
            return upload_explicit_cover(token, cover_source, article_dir, field)

    ai_cover = get_ai_cover(config, token, frontmatter, body, article_dir)
    if ai_cover:
        return ai_cover

    default_cover = config.get('default_thumb_media_id')
    if default_cover:
        print("使用配置中的默认封面 default_thumb_media_id")
    return default_cover


def get_ai_cover(config: dict, token: str, frontmatter: dict, body: str = "", article_dir: str | None = None) -> str | None:
    """生成并上传 AI 封面；失败时按配置策略退回默认封面。"""
    ai_config = config.get('ai_cover') or {}
    if not ai_config.get('enabled', False):
        return None

    print("\n🎨 正在生成 AI 封面图片...")
    temp_path = None
    try:
        temp_path = generate_ai_cover_image(config, frontmatter, body, article_dir)
        if not temp_path:
            return None
        media_id = upload_cover_material(token, temp_path)
        if media_id:
            return media_id
        print("警告: AI 封面上传失败，将退回默认封面")
    except Exception as e:
        print(f"警告: AI 封面生成失败，将退回默认封面: {_redact_text(str(e))}")
    finally:
        safe_unlink(temp_path)

    return None


# ================= Mermaid 渲染 =================

def render_mermaid_with_playwright(mermaid_code: str) -> str | None:
    """使用 Playwright 渲染 Mermaid 图表"""
    try:
        import playwright.sync_api as pw
    except ImportError:
        print("警告: playwright 库未安装")
        return None

    html_content = _build_mermaid_html(mermaid_code)
    html_path = None
    output_path = None
    browser = None
    context = None

    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            html_path = f.name

        output_path = html_path.replace('.html', '.png')

        with pw.sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1000, 'height': 800}, device_scale_factor=2)
            page = context.new_page()
            page.goto(f'file://{html_path}')
            page.wait_for_timeout(3000)

            element = page.query_selector('.mermaid svg')
            if element:
                element.screenshot(path=output_path, scale='device', omit_background=True)
            else:
                page.screenshot(path=output_path, full_page=True)

        return output_path
    except Exception as e:
        print(f"Playwright 渲染失败: {e}")
        safe_unlink(output_path)
        return None
    finally:
        if context is not None:
            try:
                context.close()
            except Exception:
                pass
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        safe_unlink(html_path)


def _build_mermaid_html(mermaid_code: str) -> str:
    """构建 Mermaid 渲染用的 HTML"""
    escaped_mermaid_code = html_lib.escape(mermaid_code)
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
        <pre class="mermaid">{escaped_mermaid_code}</pre>
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
        response = request_response("GET", kroki_url, headers=headers, timeout=15)

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
            GENERATED_MERMAID_IMAGES.add(os.path.realpath(local_path))
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

def process_content_workflow(content: str, token: str, article_dir: str | None = None) -> tuple[dict, str]:
    """完整的 Markdown 处理工作流"""
    frontmatter = {}
    body = content
    article_dir = article_dir or os.getcwd()
    image_failures = []

    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        body = content[match.end():]

    body = preprocess_markdown(body)
    body = process_mermaid(body)

    def upload_body_image(src: str, alt: str, original_markup: str) -> str:
        candidate_src = os.path.realpath(src) if os.path.isabs(src) else src
        if 'MERMAID_DIAGRAM' in alt and candidate_src in GENERATED_MERMAID_IMAGES:
            resolved_src, error = (candidate_src, None) if os.path.exists(candidate_src) else (None, f"本地图片不存在: {src}")
            GENERATED_MERMAID_IMAGES.discard(candidate_src)
        else:
            resolved_src, error = resolve_image_source(src, article_dir)
        if error:
            image_failures.append(f"{src} - {error}")
            return original_markup

        print(f"正在上传图片: {src}")
        if resolved_src != src:
            print(f"  解析路径: {resolved_src}")

        is_generated_mermaid = 'MERMAID_DIAGRAM' in alt and not is_remote_url(resolved_src)
        try:
            wechat_url = upload_image(token, resolved_src)
        finally:
            if is_generated_mermaid:
                safe_unlink(resolved_src)

        if not wechat_url:
            image_failures.append(f"{src} - 上传到微信失败")
            return original_markup

        return build_wechat_image_html(wechat_url, alt, resolved_src)

    def replace_obsidian_img(m):
        src, alt = parse_obsidian_image_embed(m.group(1))
        return upload_body_image(src, alt, m.group(0))

    def replace_markdown_img(m):
        alt, src = m.group(1), m.group(2).strip()
        return upload_body_image(src, alt, m.group(0))

    body = re.sub(r'!\[\[([^\]]+)\]\]', replace_obsidian_img, body)
    body = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_markdown_img, body)

    if image_failures:
        details = "\n".join(f"- {failure}" for failure in image_failures)
        raise RuntimeError(f"图片处理失败，已中止发布：\n{details}")

    body = process_admonitions(body)
    body = process_footnotes(body)

    return frontmatter, body


def publish_draft(token: str, article_data: dict, config: dict | None = None) -> dict:
    """发布草稿到微信"""
    json_bytes = json.dumps(article_data, ensure_ascii=False).encode('utf-8')
    headers = {'Content-Type': 'application/json; charset=utf-8'}

    def send(current_token: str) -> dict:
        url = f"{WECHAT_API_BASE}/draft/add?access_token={current_token}"
        return request_json("POST", url, data=json_bytes, headers=headers)

    data = send(token)
    if data.get('errcode') in TOKEN_INVALID_ERRCODES and config is not None:
        print("Token 已失效，正在刷新后重试发布草稿...")
        refreshed_token = get_access_token(config, force_refresh=True)
        data = send(refreshed_token)

    return data


def main(file_path: str) -> None:
    print(f"开始处理文件: {file_path}")
    article_path = os.path.abspath(file_path)
    article_dir = os.path.dirname(article_path)

    try:
        config = load_config()
        token = get_access_token(config)
        print("Token 获取成功")
    except Exception as e:
        print(f"初始化失败: {e}")
        return

    with open(article_path, 'r') as f:
        raw_content = f.read()

    print("正在处理 Markdown 内容...")
    try:
        frontmatter, processed_body = process_content_workflow(raw_content, token, article_dir)
        html_content = md_to_html(processed_body)
    except RuntimeError as e:
        print(e)
        return

    # 封面获取优先级：thumb_media_id -> 显式封面字段 -> AI 生成封面 -> 默认封面。
    try:
        thumb_media_id = resolve_thumb_media_id(
            frontmatter,
            config,
            token,
            article_dir,
            processed_body,
        )
    except RuntimeError as e:
        print(e)
        return

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
    result = publish_draft(token, {"articles": [article]}, config)
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
