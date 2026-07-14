---
name: wx-gzh-download
version: 1.0.0
description: 微信公众号文章完整下载 — 正文、图片、视频一站式搞定。当用户给出 mp.weixin.qq.com/s/... 链接要求下载/保存时调用。
---

# wx-gzh-download · 公众号文章下载

公众号文章链接 → 正文+图片+视频，一次搞定。

## 三种模式

AI 根据用户意图自动选择：

| 模式 | 输出 | 命令 |
|------|------|------|
| **全文（默认）** | `.md` + `.html` + 本地图片 + `.mp4` | `python claude-skills/wx-gzh-download/wxdl_full.py "<URL>" -o "<输出目录>"` |
| **仅正文** | `.md`（含图片 URL 引用） | `python claude-skills/wx-gzh-download/fetch_article.py "<URL>" --output "<路径>.md"` |
| **仅视频** | `.mp4` | `python claude-skills/wx-gzh-download/wxdl.py "<URL>" -o "<输出目录>" --format json` |

## 输出目录约定

- 用户指定 → 用指定的
- 全文/视频未指定 → `项目根目录/downloads/`
- 正文未指定 → `项目根目录/downloads/YYYYMMDD-标题.md`

## 工作流程

1. 从用户消息中提取公众号文章 URL
2. 判断用户意图，选对应模式（没说需求则默认全文）
3. 执行对应命令
4. 向用户汇报结果

## 依赖说明

所有脚本均在本目录下（与 SKILL.md 同级）：
- `fetch_article.py` — requests（正文提取）
- `wxdl.py` / `wxdl_full.py` — Playwright + Chromium（视频下载）
- 首次运行自动安装依赖，无需手动操作
