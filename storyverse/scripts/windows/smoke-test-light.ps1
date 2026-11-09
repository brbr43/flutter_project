<#
.SYNOPSIS
  Lightweight smoke test for StoryVerse Phase 2 venv (no GPU weights, no model downloads).

.DESCRIPTION
  Imports light packages installed by bootstrap-venv.ps1 and optionally probes torch if present.
  Fails soft on missing torch (expected until -ApproveTorch).
#>
[CmdletBinding()]
param(
    [string]$VenvPath = ".\venv"
)

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "venv python not found: $venvPython — run bootstrap-venv.ps1 first"
}

Write-Host "Running light smoke test via $venvPython" -ForegroundColor Cyan

$code = @'
import importlib
import sys

required = [
    "fastapi",
    "uvicorn",
    "httpx",
    "pydantic",
    "multipart",
    "aiosqlite",
    "pytest",
]
failed = []
for name in required:
    try:
        importlib.import_module(name)
        print(f"OK import {name}")
    except Exception as exc:  # noqa: BLE001
        failed.append((name, str(exc)))
        print(f"FAIL import {name}: {exc}")

# torch is optional until -ApproveTorch
try:
    import torch
    print(f"OK optional torch {torch.__version__} cuda={torch.cuda.is_available()}")
except Exception as exc:  # noqa: BLE001
    print(f"SKIP optional torch ({exc})")

if failed:
    print("SMOKE FAIL")
    sys.exit(1)
print("SMOKE PASS (light deps)")
'@

& $venvPython -c $code
if ($LASTEXITCODE -ne 0) {
    throw "smoke-test-light failed"
}
Write-Host "No model downloads performed." -ForegroundColor Green
