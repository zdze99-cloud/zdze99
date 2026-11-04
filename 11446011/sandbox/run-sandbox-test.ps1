# 在 Windows Sandbox(全新、空白的 Windows)裡測試 start.bat
# 用法:在專案資料夾執行  powershell -ExecutionPolicy Bypass -File sandbox\run-sandbox-test.ps1
# 每次關閉 Sandbox 視窗後,裡面的一切(uv、Python、套件、資料庫)都會被丟掉。
$ErrorActionPreference = "Stop"
$root  = Split-Path -Parent $PSScriptRoot
$clean = Join-Path $PSScriptRoot "clean"
$wsb   = Join-Path $PSScriptRoot "test.wsb"

if (-not (Test-Path "$env:windir\System32\WindowsSandbox.exe")) {
    Write-Host "尚未啟用 Windows Sandbox。請用系統管理員 PowerShell 執行:" -ForegroundColor Red
    Write-Host "  Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -All"
    Write-Host "然後重新開機。"
    exit 1
}

# 1. 做一份乾淨的專案副本(不含 .venv、資料庫、快取、PDF)
if (Test-Path $clean) { Remove-Item $clean -Recurse -Force }
robocopy $root $clean /E /NFL /NDL /NJH /NJS /NP `
    /XD .venv __pycache__ .git sandbox `
    /XF db.sqlite3 *.pyc *.pdf | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy 失敗($LASTEXITCODE)" }

# 2. 產生 Sandbox 設定:唯讀掛載副本 → 登入後複製到 C:\app 再執行 start.bat
@"
<Configuration>
  <Networking>Enable</Networking>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>$clean</HostFolder>
      <SandboxFolder>C:\src</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>powershell -NoProfile -ExecutionPolicy Bypass -Command "Copy-Item C:\src C:\app -Recurse; Start-Process C:\app\start.bat -WorkingDirectory C:\app"</Command>
  </LogonCommand>
</Configuration>
"@ | Set-Content -Path $wsb -Encoding UTF8

# 3. 啟動
Write-Host "啟動 Windows Sandbox..." -ForegroundColor Green
Start-Process $wsb
