# wxdl-full.ps1 - 微信公众号 [正文+图片URL+视频] 一体化下载
# 用法:
#   .\wxdl-full.ps1 <文章URL>
#   .\wxdl-full.ps1 <文章URL> -OutRoot D:\downloads

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Url,

    [string]$OutRoot = "d:\AI_bian_cheng\trae\downloads"
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$py = Join-Path $scriptDir "wxdl_full.py"

# 依赖检查 (与 wxdl.ps1 一致)
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { Write-Error "未找到 python"; exit 1 }

$check = & python -c "import playwright" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[准备] 安装 playwright..." -ForegroundColor Yellow
    & python -m pip install --quiet playwright
    if ($LASTEXITCODE -ne 0) { Write-Error "pip install playwright 失败"; exit 1 }
}

$browsersDir = "$env:LOCALAPPDATA\ms-playwright"
$hasChromium = (Test-Path $browsersDir) -and
    (@(Get-ChildItem $browsersDir -Directory -Filter "chromium-*").Count -gt 0)
if (-not $hasChromium) {
    Write-Host "[准备] 安装 chromium 浏览器 (~150MB)..." -ForegroundColor Yellow
    & python -m playwright install chromium
}

& python $py $Url -o $OutRoot
exit $LASTEXITCODE
