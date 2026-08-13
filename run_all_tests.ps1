# B 模块一键测试脚本
# 用法：在项目根目录 powershell 中执行 .\run_all_tests.ps1
#
# 兼容说明：
# 1) 优先用系统 PATH 里的 python / py；
# 2) 找不到时再尝试作者本机的内嵌解释器（仅开发用）；
# 3) 队友 clone 仓库后只需要：
#      a) 安装 Python 3.10+ 并加入 PATH
#      b) pip install -r requirements.txt
#      c) .\run_all_tests.ps1
# 即可。

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# ---------- 智能选择 Python 解释器 ----------
$python = $null

# 1) 优先：PATH 里的 python / py
if (Get-Command python -ErrorAction SilentlyContinue) { $python = "python" }
elseif (Get-Command py -ErrorAction SilentlyContinue) { $python = "py -3" }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $python = "python3" }

# 2) fallback：作者本机的内嵌解释器（仅在作者电脑上有效）
if (-not $python) {
    $fallback = "C:\Users\MECHREVO\.trae-cn\work\6a7ca9e53f6ae5ba3fdccaa6\python312\python.exe"
    if (Test-Path $fallback) {
        Write-Host "WARN: 系统中找不到 python/PATH，使用作者本机内嵌解释器（仅本地有效）" -ForegroundColor Yellow
        $python = $fallback
    } else {
        Write-Host "ERROR: 找不到 python，请先安装 Python 3.10+ 并加入 PATH" -ForegroundColor Red
        exit 1
    }
}

# 把项目根目录加到 PYTHONPATH
$env:PYTHONPATH = $root

# 自动定位 backend 下的 b_* 目录
$backendDir = Join-Path $root "backend"
$bDirName = (Get-ChildItem -Path $backendDir -Directory | Where-Object { $_.Name -like 'b_*' } | Select-Object -First 1 -ExpandProperty Name)
if (-not $bDirName) {
    Write-Host "ERROR: backend/ 下找不到 b_* 目录" -ForegroundColor Red
    exit 1
}
$bDir = Join-Path $backendDir $bDirName

Write-Host "[*] Using Python: $python" -ForegroundColor DarkGray

Write-Host "=== 1) 全部单测 + 覆盖率 ===" -ForegroundColor Cyan
Set-Location $root
& $python -m pytest (Join-Path $bDir "tests") --cov=$bDir --cov-report=term-missing
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: single test failed" -ForegroundColor Red; exit 1 }

Write-Host "`n=== 2) B-08 coverage self-check ===" -ForegroundColor Cyan
& $python -c "import sys, asyncio; sys.path.insert(0, r'$root'); from backend.${bDirName}.scripts.coverage_check import main; asyncio.run(main())"

Write-Host "`n=== 3) B-08 hallucination self-check ===" -ForegroundColor Cyan
& $python -c "import sys, asyncio; sys.path.insert(0, r'$root'); from backend.${bDirName}.scripts.hallucination_check import main; asyncio.run(main())"

Write-Host "`n=== 4) B-09 end-to-end test ===" -ForegroundColor Cyan
& $python -m pytest (Join-Path $bDir "tests/test_e2e_quality.py") -v

Write-Host "`nALL TESTS PASSED" -ForegroundColor Green
