#!/usr/bin/env python3
"""
微信公众号文章下载器 — 提取正文并保存为 Markdown 格式

用法:
    python fetch_article.py <url>
    python fetch_article.py <url> --output 文章.md

依赖: pip install requests lxml
"""

import re
import sys
import argparse
import os
from datetime import datetime

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)


def extract_article(url: str) -> dict:
    """抓取并解析公众号文章，返回 {title, content_html, author, create_time}"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.encoding = "utf-8"
    html = resp.text

    # --- 提取标题 ---
    title = "无标题"
    title_match = re.search(r'var msg_title = "([^"]+)"', html)
    if title_match:
        title = title_match.group(1)
    else:
        title_match = re.search(
            r'class="rich_media_title[^>]*>.*?<span[^>]*class="js_title_inner"[^>]*>([^<]+)',
            html,
            re.DOTALL,
        )
        if title_match:
            title = title_match.group(1).strip()

    # --- 提取作者 ---
    author = ""
    author_match = re.search(r'var author_name = "([^"]+)"', html)
    if author_match:
        author = author_match.group(1)

    # --- 提取创建时间 ---
    create_time = ""
    time_match = re.search(r'var create_time = "(\d+)"', html)
    if time_match:
        ts = int(time_match.group(1))
        create_time = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

    # --- 提取正文 HTML (id="js_content") ---
    content_match = re.search(
        r'id="js_content"[^>]*>(.*?)</div>\s*<(?:script|div)', html, re.DOTALL
    )
    if not content_match:
        # 尝试另一种闭合模式
        content_match = re.search(r'id="js_content"[^>]*>(.*)', html, re.DOTALL)
    if not content_match:
        raise RuntimeError("未找到文章正文 (js_content)")

    content_html = content_match.group(1)

    # --- 提取封面图 ---
    cover = ""
    cover_match = re.search(r'var msg_cdn_url = "([^"]+)"', html)
    if cover_match:
        cover = cover_match.group(1)

    return {
        "title": title,
        "author": author,
        "create_time": create_time,
        "cover": cover,
        "content_html": content_html,
        "source_url": url,
    }


def html_to_markdown(html: str) -> str:
    """将 WeChat 文章 HTML 转换为 Markdown 文本"""
    # 移除 script / style
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)

    # 提取所有图片 (处理 data-src)
    def extract_img(m):
        src = ""
        for attr in ["data-src", "src", "data-croporisrc"]:
            v = re.search(rf'{attr}="([^"]+)"', m.group(0))
            if v:
                src = v.group(1)
                break
        alt = ""
        alt_m = re.search(r'alt="([^"]*)"', m.group(0))
        if alt_m:
            alt = alt_m.group(1)
        return f"![{alt}]({src})" if src else ""

    html = re.sub(r"<img[^>]+>", extract_img, html)

    # 处理 section / div / p / span → 标记换行
    # 先给块级标签前后加换行标记
    for tag in ["section", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "blockquote"]:
        html = re.sub(rf"<{tag}[^>]*>", "\n", html)
        html = re.sub(rf"</{tag}>", "\n", html)

    # 处理 br
    html = re.sub(r"<br\s*/?>", "\n", html)

    # 处理有序列表 <ol><li>
    html = re.sub(r"<ol[^>]*>", "\n", html)
    html = re.sub(r"</ol>", "\n", html)
    html = re.sub(r"<ul[^>]*>", "\n", html)
    html = re.sub(r"</ul>", "\n", html)

    # 处理 <strong>/<b> → **
    html = re.sub(r"<(?:strong|b)[^>]*>", "**", html)
    html = re.sub(r"</(?:strong|b)>", "**", html)

    # 处理 <em>/<i> → *
    html = re.sub(r"<(?:em|i)[^>]*>", "*", html)
    html = re.sub(r"</(?:em|i)>", "*", html)

    # 处理 <a> → 保留文本和链接
    def extract_link(m):
        text = m.group(2) or m.group(1) or ""
        href = m.group(1) or ""
        if href and text:
            return f"[{text}]({href})"
        return text or href

    # 先提取不带链接的文本
    html = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', extract_link, html, flags=re.DOTALL)
    html = re.sub(r"<a[^>]*>(.*?)</a>", r"\1", html)

    # 处理 <span> — 保留内容去标签
    html = re.sub(r"<span[^>]*>", "", html)
    html = re.sub(r"</span>", "", html)

    # 移除剩余所有 HTML 标签
    html = re.sub(r"<[^>]+>", "", html)

    # 解码 HTML 实体
    html = (
        html.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&nbsp;", " ")
    )

    # 清理多余空行
    lines = [line.strip() for line in html.split("\n")]
    lines = [l for l in lines if l]  # 去掉空行

    # 合并连续空行不超过2个
    result = []
    prev_empty = False
    for line in lines:
        if line == "":
            if not prev_empty:
                result.append("")
                prev_empty = True
        else:
            result.append(line)
            prev_empty = False

    return "\n".join(result)


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = name.strip()
    name = name[:80]  # 限制长度
    return name or "文章"


def main():
    parser = argparse.ArgumentParser(description="公众号文章下载为 Markdown")
    parser.add_argument("url", help="文章链接 (https://mp.weixin.qq.com/s/...)")
    parser.add_argument("--output", "-o", help="输出路径")
    args = parser.parse_args()

    # 1. 提取
    print("正在抓取文章...")
    try:
        article = extract_article(args.url)
    except Exception as e:
        print(f"抓取失败: {e}")
        sys.exit(1)

    print(f"标题: {article['title']}")
    if article["author"]:
        print(f"作者: {article['author']}")

    # 2. 转换为 Markdown
    print("正在转换为 Markdown...")
    md_body = html_to_markdown(article["content_html"])

    # 3. 组装
    lines = [f"# {article['title']}", ""]
    if article["author"]:
        lines.append(f"> 作者：{article['author']}")
    if article["create_time"]:
        lines.append(f"> 时间：{article['create_time']}")
    if article["cover"]:
        lines.append(f"> 封面：![封面]({article['cover']})")
    lines.append(f"> 来源：[原文链接]({article['source_url']})")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(md_body)
    lines.append("")
    lines.append("---")
    lines.append(f"*原文链接：{article['source_url']}*")

    md_content = "\n".join(lines)

    # 4. 确定输出路径
    if args.output:
        output_path = args.output
    else:
        today = datetime.now().strftime("%Y%m%d")
        safe_title = sanitize_filename(article["title"])
        # 尝试保存到常用目录
        candidates = [
            os.path.expanduser(f"~\\Desktop\\{today}-{safe_title}.md"),
            os.path.join(os.getcwd(), f"{today}-{safe_title}.md"),
        ]
        # 扫描工作目录
        work_dirs = ["d:/AI_bian_cheng/trae", os.getcwd()]
        for base in work_dirs:
            if os.path.isdir(base):
                candidates.insert(0, os.path.join(base, f"{today}-{safe_title}.md"))
                break
        output_path = candidates[0]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n已保存: {output_path}")
    print(f"共 {len(md_content)} 字符")


if __name__ == "__main__":
    main()
