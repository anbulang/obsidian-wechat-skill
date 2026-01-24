# Admonition 类型映射

本文档定义了 Obsidian Admonition 插件的 `ad-*` 代码块类型与微信 HTML 的映射关系。

## 类型映射表

| Admonition 类型 | 别名 | CSS 类 | 颜色 | 图标 |
|----------------|------|--------|------|------|
| `ad-note` | - | `note-callout-note` | 蓝色 #448aff | pencil |
| `ad-abstract` | summary, tldr | `note-callout-abstract` | 青色 #00bfa5 | clipboard-list |
| `ad-info` | - | `note-callout-note` | 蓝色 #448aff | info |
| `ad-todo` | - | `note-callout-note` | 蓝色 #448aff | check-circle-2 |
| `ad-tip` | hint, important | `note-callout-abstract` | 青色 #00bfa5 | flame |
| `ad-success` | check, done | `note-callout-success` | 绿色 #00c853 | check |
| `ad-question` | help, faq | `note-callout-question` | 黄色 #ffab00 | help-circle |
| `ad-warning` | caution, attention | `note-callout-question` | 橙色 #ff9100 | alert-triangle |
| `ad-failure` | fail, missing | `note-callout-failure` | 红色 #ff5252 | x |
| `ad-danger` | error | `note-callout-failure` | 红色 #ff5252 | zap |
| `ad-bug` | - | `note-callout-failure` | 红色 #ff5252 | bug |
| `ad-example` | - | `note-callout-example` | 紫色 #7c4dff | list |
| `ad-quote` | cite | `note-callout-quote` | 灰色 #9e9e9e | quote |

## SVG 图标定义

所有图标使用 Lucide 图标集，统一尺寸 24x24，stroke-width=2。

### note (pencil)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path><path d="m15 5 4 4"></path></svg>
```

### abstract (clipboard-list)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><path d="M12 11h4"></path><path d="M12 16h4"></path><path d="M8 11h.01"></path><path d="M8 16h.01"></path></svg>
```

### info
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4"></path><path d="M12 8h.01"></path></svg>
```

### todo (check-circle-2)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>
```

### tip (flame)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"></path></svg>
```

### success (check)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M20 6 9 17l-5-5"></path></svg>
```

### question (help-circle)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><path d="M12 17h.01"></path></svg>
```

### warning (alert-triangle)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><path d="M12 9v4"></path><path d="M12 17h.01"></path></svg>
```

### failure (x)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
```

### danger (zap)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
```

### bug
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="m8 2 1.88 1.88"></path><path d="M14.12 3.88 16 2"></path><path d="M9 7.13v-1a3.003 3.003 0 1 1 6 0v1"></path><path d="M12 20c-3.3 0-6-2.7-6-6v-3a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v3c0 3.3-2.7 6-6 6"></path><path d="M12 20v-9"></path><path d="M6.53 9C4.6 8.8 3 7.1 3 5"></path><path d="M6 13H2"></path><path d="M3 21c0-2.1 1.7-3.9 3.8-4"></path><path d="M20.97 5c0 2.1-1.6 3.8-3.5 4"></path><path d="M22 13h-4"></path><path d="M17.2 17c2.1.1 3.8 1.9 3.8 4"></path></svg>
```

### example (list)
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
```

### quote
```html
<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="callout-icon"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"></path><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"></path></svg>
```

## 颜色变量

```css
:root {
  /* 蓝色系 - note, info, todo */
  --callout-note: #448aff;
  --callout-note-bg: rgba(68, 138, 255, 0.1);

  /* 青色系 - abstract, tip, hint, important */
  --callout-abstract: #00bfa5;
  --callout-abstract-bg: rgba(0, 191, 165, 0.1);

  /* 绿色系 - success, check, done */
  --callout-success: #00c853;
  --callout-success-bg: rgba(0, 200, 83, 0.1);

  /* 黄/橙色系 - question, warning, caution */
  --callout-question: #ffab00;
  --callout-question-bg: rgba(255, 171, 0, 0.1);

  /* 红色系 - failure, danger, bug */
  --callout-failure: #ff5252;
  --callout-failure-bg: rgba(255, 82, 82, 0.1);

  /* 紫色系 - example */
  --callout-example: #7c4dff;
  --callout-example-bg: rgba(124, 77, 255, 0.1);

  /* 灰色系 - quote */
  --callout-quote: #9e9e9e;
  --callout-quote-bg: rgba(158, 158, 158, 0.1);
}
```

## Admonition 代码块解析规则

### 语法格式
````markdown
```ad-{type}
title: 自定义标题（可选）
collapse: open/closed（可选，微信不支持折叠）

正文内容
可以有多行
支持 **Markdown** 格式
```
````

### 解析步骤

1. **识别代码块类型**
   ```regex
   ^```ad-(\w+)
   ```
   提取 type 为 $1

2. **提取标题（可选）**
   ```regex
   ^title:\s*(.+)$
   ```
   如果没有 title 行，使用 type 首字母大写作为标题

3. **跳过元数据行**
   跳过 `collapse:` 等配置行

4. **提取正文**
   剩余内容作为正文，保持 Markdown 格式

### 类型别名处理

转换时需要将别名统一映射到主类型：

```javascript
const aliasMap = {
  'summary': 'abstract',
  'tldr': 'abstract',
  'hint': 'tip',
  'important': 'tip',
  'check': 'success',
  'done': 'success',
  'help': 'question',
  'faq': 'question',
  'caution': 'warning',
  'attention': 'warning',
  'fail': 'failure',
  'missing': 'failure',
  'error': 'danger',
  'cite': 'quote'
};
```

## HTML 输出模板

```html
<section class="note-callout {style_class}" style="border-radius: 4px; margin: 16px 0; overflow: hidden;">
  <section class="note-callout-title-wrap" style="display: flex; align-items: center; padding: 8px 12px; background: {bg_color};">
    <span style="color: {color}; margin-right: 8px; display: flex; align-items: center;">
      {svg_icon}
    </span>
    <span class="note-callout-title" style="font-weight: 600; color: {color};">{title}</span>
  </section>
  <section class="note-callout-content" style="padding: 12px 16px; background: {bg_color}; border-left: 4px solid {color};">
    {content}
  </section>
</section>
```
