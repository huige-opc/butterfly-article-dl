# butterfly-article-dl · 公众号文章下载工具

一键下载公众号文章（正文 + 图片 + 视频）到本地。

---

> **适用范围**
>
> | 场景 | 支持吗？ |
> |---|---|
> | 公众号文章 link（`mp.weixin.qq.com/s/...`）| ✅ 正文 + 图片 + 视频 |
> | 微信视频号 | ❌ 请使用 wx_video-channel |

---

## 普通用户怎么用

### 环境要求

| 组件 | 要求 |
|---|---|
| Python | 3.9+（[下载地址](https://www.python.org/downloads/)） |
| pip | 安装 Python 时勾选"Add Python to PATH"即自带 |

### 安装

```bash
# 1. 打开终端（CMD 或 PowerShell），进入本目录

# 2. 安装 Playwright
pip install playwright

# 3. 安装 Chromium 浏览器（约 150MB，一次性）
playwright install chromium
```

### 下载全文（正文 + 图片 + 视频）

```powershell
python wxdl_full.py "https://mp.weixin.qq.com/s/文章链接" -o "保存目录"
```

下载完成后：

```
保存目录/
  YYYYMMDD_文章标题/
    YYYYMMDD_文章标题.md      ← 用 Markdown 阅读器打开
    YYYYMMDD_文章标题.html    ← 双击浏览器打开（视频内嵌播放）
    images/                     ← 所有图片已下载到本地
    YYYYMMDD_文章标题.mp4      ← 视频文件
```

### 只下视频

```powershell
python wxdl.py "https://mp.weixin.qq.com/s/文章链接" -o "保存目录"
```

### 只下正文（Markdown，不带视频）

```powershell
python fetch_article.py "https://mp.weixin.qq.com/s/文章链接" --output "文件名.md"
```

### 常见问题

**视频播放不了？**
- Windows 11 原生支持
- Windows 10 装 [HEVC 扩展](https://apps.microsoft.com/detail/9nmzlz57r3t7) 或用 VLC
- 极少数付费视频拿不到直链，会报 `no_video_found`

### 不明白怎么用？

把本工具文件夹拖到 AI 助手（Claude、ChatGPT 等），告诉它"帮我看下这个工具怎么用"，AI 会帮你搞定。

---

## 开发者指引

### 工具原理

微信文章里的视频（`wxv_...`）用普通 HTTP + Referer 会被 403：CDN 强制要求浏览器活跃会话 + 一次性签名（`dis_k` + `dis_t`），yt-dlp 也不认。

**解决方案**：用无头 Chromium 加载文章、拦截真实视频请求、用同一浏览器会话分片下载，绕开所有防盗链。

### 三种模式

| 模式 | 命令 | 输出 |
|------|------|------|
| 全文（默认） | `python wxdl_full.py "<URL>" -o "<目录>"` | MD + HTML + 本地图片 + MP4 |
| 仅视频 | `python wxdl.py "<URL>" -o "<目录>"` | MP4 |
| 仅正文 | `python fetch_article.py "<URL>" --output "<路径>.md"` | MD（图片远程引用） |

### 文件说明

| 文件 | 功能 |
|------|------|
| `wxdl_full.py` | 主程序：下载正文 + 图片 + 视频 |
| `wxdl.py` | 视频下载核心（Playwright 拦截 + 分片下载） |
| `fetch_article.py` | 正文提取（纯 Markdown） |
| `wxdl.ps1` | PowerShell 封装（首次自动装依赖） |
| `wxdl-full.ps1` | 全文下载 PowerShell 封装 |
| `requirements.txt` | Python 依赖列表 |

### 依赖

- Python 3.9+
- playwright
- Chromium（playwright 自动安装，约 150MB）

安装：

```bash
pip install playwright
playwright install chromium
```

### 视频下载原理

1. Playwright 用手机 UA 打开文章页面
2. 反复滚动到底部，触发视频懒加载
3. 拦截所有 `mpvideo.qpic.cn` 的 mp4 请求
4. 同一个视频可能有多个清晰度（f10104 > f10102 > f10004 > f10002）
5. 自动选最高清，用 Range 分片下载（每片 1MB，失败自动重试）
6. 输出文件名：`YYYYMMDD_标题.mp4`，多视频加序号
