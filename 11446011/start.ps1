# 選課系統啟動腳本:由 start.bat 呼叫(雙擊 start.bat 即可)
# 1. 沒有 uv 就自動安裝  2. 安裝 Python 與套件  3. 建資料庫(第一次載入示範資料)  4. 啟動伺服器並開瀏覽器
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "選課系統"
Set-Location -LiteralPath $PSScriptRoot

$Port = 8000
$Url = "http://127.0.0.1:$Port/"

function Fail($msg) {
    Write-Host ""
    Write-Host "[錯誤] $msg" -ForegroundColor Red
    Write-Host "啟動失敗,請查看上方的訊息。"
    exit 1
}

function Run($exe, [string[]]$argv) {
    & $exe @argv
    if ($LASTEXITCODE -ne 0) { Fail "$exe $($argv -join ' ') 執行失敗(代碼 $LASTEXITCODE)" }
}

Write-Host "============================================" -ForegroundColor DarkRed
Write-Host "  國立示範大學 · 選課系統(Django)"
Write-Host "============================================" -ForegroundColor DarkRed
Write-Host ""

# ---- 0. 已經在執行就直接開瀏覽器 ----
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    Write-Host "伺服器已經在執行中(port $Port),直接開啟瀏覽器。" -ForegroundColor Yellow
    Start-Process $Url
    Start-Sleep -Seconds 2
    exit 0
}

# ---- 1. 確認 uv,沒有就自動安裝 ----
$uvBin = Join-Path $env:USERPROFILE ".local\bin"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    if (-not (Test-Path (Join-Path $uvBin "uv.exe"))) {
        Write-Host "[1/4] 找不到 uv,正在自動安裝(官方安裝程式)..." -ForegroundColor Cyan
        try {
            Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        } catch {
            Fail "uv 安裝失敗:$($_.Exception.Message)`n       可改用 PowerShell 執行:winget install --id=astral-sh.uv -e"
        }
    }
    $env:Path = "$uvBin;$env:Path"
}
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Fail "找不到 uv。請重新開啟此腳本,或手動安裝:https://docs.astral.sh/uv/"
}
Write-Host "[1/4] uv 已就緒:$(uv --version)" -ForegroundColor Green

# ---- 2. 安裝 Python 與套件(依 pyproject.toml / uv.lock;第一次會比較久) ----
Write-Host "[2/4] 安裝 / 同步 Python 與套件..." -ForegroundColor Cyan
Run uv @("sync")

# ---- 3. 資料庫 ----
$firstRun = -not (Test-Path "db.sqlite3")
Write-Host "[3/4] 更新資料庫結構..." -ForegroundColor Cyan
Run uv @("run", "python", "manage.py", "migrate", "--noinput")
if ($firstRun) {
    Write-Host "      第一次執行,載入示範資料..." -ForegroundColor Cyan
    Run uv @("run", "python", "manage.py", "seed_demo")
}

# ---- 4. 啟動伺服器,3 秒後開瀏覽器 ----
Write-Host "[4/4] 啟動伺服器:$Url" -ForegroundColor Green
Write-Host ""
Write-Host "  示範帳號:11446011(學生)、lin(教師)、registrar(教務處)、sysadmin(系統)"
Write-Host "  密碼皆為 1234"
Write-Host "  關閉這個視窗,或按 Ctrl+C,即可停止伺服器。" -ForegroundColor Yellow
Write-Host ""
Start-Job -ScriptBlock { param($u) Start-Sleep -Seconds 3; Start-Process $u } -ArgumentList $Url | Out-Null
& uv run python manage.py runserver $Port
