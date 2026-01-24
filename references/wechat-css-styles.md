# 微信公众号 CSS 样式表

本文档包含微信公众号适配的完整 CSS 样式，基于 `#nice` 选择器体系。

## 完整样式代码

```html
<style>
/* ========== 基础排版 ========== */
#nice {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  font-size: 16px;
  line-height: 1.8;
  color: #333;
  padding: 20px;
}

/* 段落 */
#nice p {
  margin: 16px 0;
  line-height: 1.8;
  color: #333;
  font-size: 16px;
}

/* ========== 标题 ========== */
#nice h1 {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
  margin: 40px 0 30px;
  color: #333;
  border-bottom: 2px solid #3370ff;
  padding-bottom: 10px;
}

#nice h2 {
  font-size: 20px;
  font-weight: bold;
  margin: 50px 0 25px;
  color: #333;
  padding-left: 12px;
  border-left: 4px solid #3370ff;
}

#nice h3 {
  font-size: 18px;
  font-weight: bold;
  margin: 30px 0 15px;
  color: #333;
}

#nice h4 {
  font-size: 16px;
  font-weight: bold;
  margin: 20px 0 10px;
  color: #555;
}

#nice h5, #nice h6 {
  font-size: 15px;
  font-weight: bold;
  margin: 15px 0 10px;
  color: #666;
}

/* ========== 列表 ========== */
#nice ul, #nice ol {
  margin: 16px 0;
  padding-left: 24px;
}

#nice li {
  margin: 8px 0;
  line-height: 1.8;
}

#nice li p {
  margin: 4px 0;
}

/* 任务列表 */
#nice ul.task-list {
  list-style: none;
  padding-left: 0;
}

#nice .task-list-item {
  display: flex;
  align-items: flex-start;
}

#nice .task-list-item input {
  margin-right: 8px;
  margin-top: 6px;
}

/* ========== 引用 ========== */
#nice blockquote {
  margin: 20px 0;
  padding: 15px 20px;
  background: #f7f7f7;
  border-left: 4px solid #ddd;
  border-radius: 0 4px 4px 0;
}

#nice blockquote p {
  margin: 8px 0;
  color: #666;
  font-size: 15px;
}

#nice blockquote blockquote {
  margin: 10px 0;
}

/* ========== 强调样式 ========== */
#nice strong {
  color: #3370ff;
  font-weight: bold;
}

#nice em {
  font-style: italic;
  color: #555;
}

#nice del {
  text-decoration: line-through;
  color: #999;
}

/* 高亮 */
#nice .highlight, #nice mark {
  background: linear-gradient(to bottom, transparent 60%, #ffe066 60%);
  padding: 0 2px;
}

/* ========== 链接 ========== */
#nice a {
  color: #3370ff;
  text-decoration: none;
  border-bottom: 1px solid #3370ff;
}

/* ========== 行内代码 ========== */
#nice code {
  font-family: "SF Mono", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 14px;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  color: #c7254e;
}

/* ========== 代码块 ========== */
#nice pre {
  margin: 20px 0;
  border-radius: 8px;
  overflow: hidden;
}

#nice pre code {
  display: block;
  padding: 16px;
  background: #282c34;
  color: #abb2bf;
  font-size: 14px;
  line-height: 1.6;
  overflow-x: auto;
  border-radius: 0;
}

/* 代码块容器 */
.code-block {
  margin: 20px 0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.code-header {
  background: #21252b;
  padding: 8px 16px;
  display: flex;
  align-items: center;
}

.code-lang {
  color: #9da5b4;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.code-content {
  margin: 0;
  background: #282c34;
  padding: 16px;
}

.code-content code {
  background: transparent;
  padding: 0;
  color: #abb2bf;
}

.code-line {
  display: block;
  min-height: 1.6em;
}

.line-number {
  display: inline-block;
  width: 32px;
  color: #636d83;
  text-align: right;
  margin-right: 16px;
  user-select: none;
}

/* ========== 表格 ========== */
#nice table {
  width: 100%;
  margin: 20px 0;
  border-collapse: collapse;
  font-size: 14px;
}

#nice table th {
  background: #f5f7fa;
  font-weight: bold;
  text-align: left;
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
}

#nice table td {
  padding: 12px 16px;
  border: 1px solid #e4e7ed;
}

#nice table tr:nth-child(even) {
  background: #fafafa;
}

#nice table tr:hover {
  background: #f5f7fa;
}

/* ========== 分隔线 ========== */
#nice hr {
  border: none;
  border-top: 1px solid #e4e7ed;
  margin: 30px 0;
}

/* ========== 图片 ========== */
#nice img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 20px auto;
  border-radius: 4px;
}

.image-wrapper {
  text-align: center;
  margin: 24px 0;
}

.image-caption {
  color: #999;
  font-size: 14px;
  margin-top: 10px;
  text-align: center;
}

/* ========== Callout 样式 ========== */
.note-callout {
  margin: 20px 0;
  border-radius: 8px;
  overflow: hidden;
}

.note-callout-title-wrap {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  font-weight: 600;
}

.note-callout-title-wrap svg {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  flex-shrink: 0;
}

.note-callout-title {
  font-size: 15px;
}

.note-callout-content {
  padding: 12px 16px 16px;
}

.note-callout-content p:first-child {
  margin-top: 0;
}

.note-callout-content p:last-child {
  margin-bottom: 0;
}

/* Callout 颜色变体 */
.note-callout-note {
  background: rgba(68, 138, 255, 0.08);
  border-left: 4px solid #448aff;
}
.note-callout-note .note-callout-title-wrap {
  background: rgba(68, 138, 255, 0.12);
  color: #448aff;
}
.note-callout-note svg { stroke: #448aff; }

.note-callout-abstract {
  background: rgba(0, 191, 165, 0.08);
  border-left: 4px solid #00bfa5;
}
.note-callout-abstract .note-callout-title-wrap {
  background: rgba(0, 191, 165, 0.12);
  color: #00bfa5;
}
.note-callout-abstract svg { stroke: #00bfa5; }

.note-callout-success {
  background: rgba(0, 200, 83, 0.08);
  border-left: 4px solid #00c853;
}
.note-callout-success .note-callout-title-wrap {
  background: rgba(0, 200, 83, 0.12);
  color: #00c853;
}
.note-callout-success svg { stroke: #00c853; }

.note-callout-question {
  background: rgba(255, 171, 0, 0.08);
  border-left: 4px solid #ffab00;
}
.note-callout-question .note-callout-title-wrap {
  background: rgba(255, 171, 0, 0.12);
  color: #e69500;
}
.note-callout-question svg { stroke: #ffab00; }

.note-callout-failure {
  background: rgba(255, 82, 82, 0.08);
  border-left: 4px solid #ff5252;
}
.note-callout-failure .note-callout-title-wrap {
  background: rgba(255, 82, 82, 0.12);
  color: #ff5252;
}
.note-callout-failure svg { stroke: #ff5252; }

.note-callout-example {
  background: rgba(124, 77, 255, 0.08);
  border-left: 4px solid #7c4dff;
}
.note-callout-example .note-callout-title-wrap {
  background: rgba(124, 77, 255, 0.12);
  color: #7c4dff;
}
.note-callout-example svg { stroke: #7c4dff; }

.note-callout-quote {
  background: rgba(158, 158, 158, 0.08);
  border-left: 4px solid #9e9e9e;
}
.note-callout-quote .note-callout-title-wrap {
  background: rgba(158, 158, 158, 0.12);
  color: #757575;
}
.note-callout-quote svg { stroke: #9e9e9e; }

/* ========== Mermaid 图表 ========== */
.mermaid-diagram {
  text-align: center;
  margin: 24px 0;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.mermaid-diagram img {
  max-width: 100%;
  height: auto;
}

/* ========== 脚注 ========== */
.footnotes {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.footnotes-title {
  font-size: 14px;
  color: #999;
  margin-bottom: 12px;
}

.footnote-item {
  font-size: 13px;
  color: #666;
  margin: 8px 0;
  line-height: 1.6;
}

.footnote-num {
  color: #3370ff;
  font-weight: 500;
  margin-right: 4px;
}

.footnote-word {
  color: #3370ff;
  font-weight: 500;
}

.footnote-ref {
  color: #3370ff;
  font-size: 12px;
  vertical-align: super;
}

/* ========== 数学公式 ========== */
.math-block {
  text-align: center;
  margin: 20px 0;
  overflow-x: auto;
}

.math-inline {
  vertical-align: middle;
}
</style>
```

## 内联样式版本

由于微信公众号可能过滤 `<style>` 标签，以下是关键样式的内联版本：

### Callout 内联样式

```html
<!-- Note 类型 -->
<section style="margin: 20px 0; border-radius: 8px; overflow: hidden; background: rgba(68, 138, 255, 0.08); border-left: 4px solid #448aff;">
  <section style="display: flex; align-items: center; padding: 12px 16px; background: rgba(68, 138, 255, 0.12);">
    <span style="color: #448aff; margin-right: 10px; display: flex;">
      <!-- SVG 图标 -->
    </span>
    <span style="font-weight: 600; font-size: 15px; color: #448aff;">标题</span>
  </section>
  <section style="padding: 12px 16px 16px;">
    <p style="margin: 0; line-height: 1.8; color: #333;">内容</p>
  </section>
</section>
```

### 代码块内联样式

```html
<section style="margin: 20px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <section style="background: #21252b; padding: 8px 16px;">
    <span style="color: #9da5b4; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Python</span>
  </section>
  <pre style="margin: 0; background: #282c34; padding: 16px; overflow-x: auto;"><code style="font-family: Consolas, monospace; font-size: 14px; line-height: 1.6; color: #abb2bf;"><span style="display: block;"><span style="display: inline-block; width: 32px; color: #636d83; text-align: right; margin-right: 16px;">1</span>def hello():</span>
<span style="display: block;"><span style="display: inline-block; width: 32px; color: #636d83; text-align: right; margin-right: 16px;">2</span>    print("Hello")</span></code></pre>
</section>
```

### 表格内联样式

```html
<table style="width: 100%; margin: 20px 0; border-collapse: collapse; font-size: 14px;">
  <thead>
    <tr>
      <th style="background: #f5f7fa; font-weight: bold; text-align: left; padding: 12px 16px; border: 1px solid #e4e7ed;">表头</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 12px 16px; border: 1px solid #e4e7ed;">内容</td>
    </tr>
  </tbody>
</table>
```

## 主题色配置

可根据需求调整主题色：

| 元素 | 默认色值 | 说明 |
|------|----------|------|
| 主色调 | `#3370ff` | 用于标题装饰、链接、强调 |
| 正文色 | `#333333` | 主要文字颜色 |
| 次要色 | `#666666` | 引用、次要文字 |
| 边框色 | `#e4e7ed` | 表格、分隔线 |
| 背景色 | `#f5f7fa` | 表头、代码背景 |

## 微信兼容性注意事项

1. **避免使用的属性**：
   - `position: fixed/sticky`
   - `transform` (部分场景)
   - `animation` / `transition`
   - `filter`
   - `clip-path`

2. **推荐做法**：
   - 使用内联样式确保兼容
   - 避免过深的选择器嵌套
   - 图片使用 `max-width: 100%`
   - 字体使用系统字体栈

3. **测试方法**：
   - 在微信公众号后台"新建图文"
   - 切换到 HTML 模式粘贴代码
   - 预览检查样式效果
