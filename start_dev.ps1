# 一键启动开发环境（交接用）
# 用法：项目根目录执行 .\start_dev.ps1（或右键"使用 PowerShell 运行"）
# 行为：校验依赖 → 拉起后端(:8000)/前端(:5173) 两个独立控制台窗口，关窗即停对应服务
#
# ⚠️ 实现要点（改脚本前必读，2026-08-19 排坑结论）：
#   必须用 Start-Process 直启 npm.cmd / python.exe，不要包 powershell/cmd 窗口——
#   包装窗口里 vite 的 stdin 异常，启动后数秒内自动退出。
#
# 种子数据缺失时页面为空态，先执行（幂等）：
#   py -m backend.a_用户与聊天.seed_data / b_学情数据.seed_data / c_学习内容.seed_data

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

# --- 0. 环境自检 ---
if (-not (Test-Path "$root\frontend\node_modules")) {
    Write-Host '[!] frontend/node_modules 缺失，先安装依赖...' -ForegroundColor Yellow
    Push-Location "$root\frontend"; npm install; Pop-Location
}

# 后端解释器：优先 venv，回退全局 py
$py = "$root\venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = 'py' }

Write-Host '[1/3] 后端依赖检查（fastapi）...' -ForegroundColor Cyan
& $py -m pip show fastapi *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host '    缺失，安装 backend/requirements.txt ...' -ForegroundColor Yellow
    & $py -m pip install -r "$root\backend\requirements.txt" --quiet
}

# 前端命令：解析 npm.cmd 绝对路径（批处理，不受 PowerShell 执行策略影响）
$npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) {
    # 某些环境 npm.cmd 不在 PATH：从 npm.ps1 同目录兜底找（node 标准安装三者并存）
    $npmPs1 = (Get-Command npm -ErrorAction SilentlyContinue).Source
    if ($npmPs1) { $npmCmd = Join-Path (Split-Path $npmPs1) 'npm.cmd' }
}
if (-not $npmCmd -or -not (Test-Path $npmCmd)) {
    Write-Host '[x] 未找到 npm.cmd，请确认 Node.js 已安装并在 PATH' -ForegroundColor Red
    exit 1
}

# --- 1. 启动后端（独立控制台窗口） ---
Write-Host '[2/3] 启动后端 :8000（新窗口）...' -ForegroundColor Cyan
Start-Process -FilePath $py -ArgumentList '-m', 'backend.main' -WorkingDirectory $root

# --- 2. 启动前端（独立控制台窗口） ---
Write-Host '[3/3] 启动前端 :5173（新窗口）...' -ForegroundColor Cyan
Start-Process -FilePath $npmCmd -ArgumentList 'run', 'dev' -WorkingDirectory "$root\frontend"

# --- 3. 就绪探测（最多等 40s，起来即提前结束） ---
Write-Host '等待服务就绪' -ForegroundColor Cyan
$ok = $false
foreach ($i in 1..20) {
    Start-Sleep -Seconds 2
    $be = Test-NetConnection 127.0.0.1 -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
    $fe = Test-NetConnection 127.0.0.1 -Port 5173 -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($be -and $fe) { $ok = $true; break }
    Write-Host "  [$($i*2)s] 后端:$($be -and '就绪' -or '等待中') 前端:$($fe -and '就绪' -or '等待中')"
}

Write-Host @"

=========================================================
$(if ($ok) { '  ✔ 两个服务均已就绪（窗口全程别关，关了=服务停止）' } else { '  ⚠ 40s 内未全部就绪：看两个服务窗口里的报错信息' })

  前端    http://127.0.0.1:5173
  后端    http://127.0.0.1:8000/docs
  健康检查 http://127.0.0.1:8000/health

  测试账号（密码统一 Test@1234）：
    student001 → 仪表盘   teacher001 → 学生列表   admin001 → 质量看板

  页面全空态？→ 种子数据未灌，见 frontend/prompts/18 号文档 §四
=========================================================
"@ -ForegroundColor $(if ($ok) { 'Green' } else { 'Yellow' })
