# wxdl.ps1 - 微信公众号视频下载器 (一键入口)
# 用法:
#   .\wxdl.ps1 <文章URL>
#   .\wxdl.ps1 <文章URL> -OutDir D:\videos
#   .\wxdl.ps1 <文章URL> -Format json

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Url,

    [string]$OutDir = ".",

    [ValidateSet("text", "json")]
    [string]$Format = "text"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $scriptDir "wxdl.py"

# --- 1. 检查 Python ---
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "未找到 python, 请先安装 Python 3.9+"
    exit 1
}

# --- 2. 检查 Playwright 依赖 ---
$check = & python -c "import playwright" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[准备] 首次运行, 安装 playwright..." -ForegroundColor Yellow
    & python -m pip install --quiet playwright
    if ($LASTEXITCODE -ne 0) { Write-Error "pip install playwright 失败"; exit 1 }
}

# --- 3. 检查 chromium 浏览器是否装了 ---
$browsersDir = "$env:LOCALAPPDATA\ms-playwright"
$hasChromium = Test-Path $browsersDir -PathType Container
if ($hasChromium) {
    $hasChromium = @(Get-ChildItem $browsersDir -Directory -Filter "chromium-*").Count -gt 0
}
if (-not $hasChromium) {
    Write-Host "[准备] 首次运行, 安装 chromium 浏览器 (~150MB)..." -ForegroundColor Yellow
    & python -m playwright install chromium
}

# --- 4. 跑 ---
& python $py $Url -o $OutDir --format $Format
exit $LASTEXITCODE
