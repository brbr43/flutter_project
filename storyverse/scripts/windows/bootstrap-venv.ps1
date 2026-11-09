<#
.SYNOPSIS
  StoryVerse Phase 2 — create a Python venv and install LIGHTWEIGHT deps only.

.DESCRIPTION
  Default behavior:
    - Creates venv at -VenvPath
    - Upgrades pip/setuptools/wheel
    - Installs FastAPI stack + sqlite tooling + pytest (no PyTorch, no models)

  Gated optional steps (OFF by default):
    -ApproveTorch       Install torch/vision/audio from a CUDA wheel index (user confirmation unless -Yes)
    -ApproveComfyClone  git clone ComfyUI repo ONLY (no model weights). Confirmation unless -Yes

  This script NEVER downloads model checkpoints / safetensors / GGUF weights.

.PARAMETER VenvPath
  Path for the virtualenv. Default: .\venv

.PARAMETER PythonLauncher
  Prefer "py -3.12" / "py -3.11" / "python". Default: auto-detect.

.PARAMETER ApproveTorch
  Opt-in PyTorch CUDA install.

.PARAMETER TorchIndexUrl
  pip --index-url for CUDA wheels. Default: https://download.pytorch.org/whl/cu124
  Verify against https://pytorch.org/get-started/locally/ before use.

.PARAMETER ApproveComfyClone
  Opt-in git clone of ComfyUI sources only.

.PARAMETER ComfyPath
  Destination for ComfyUI clone. Default: .\apps\comfyui

.PARAMETER ComfyRepoUrl
  Default: https://github.com/comfyanonymous/ComfyUI.git

.PARAMETER Yes
  Skip interactive Confirm- prompts for gated steps (still requires the Approve* switches).
#>
[CmdletBinding()]
param(
    [string]$VenvPath = ".\venv",
    [string]$PythonLauncher = "",
    [switch]$ApproveTorch,
    [string]$TorchIndexUrl = "https://download.pytorch.org/whl/cu124",
    [string]$TorchPackages = "torch torchvision torchaudio",
    [switch]$ApproveComfyClone,
    [string]$ComfyPath = ".\apps\comfyui",
    [string]$ComfyRepoUrl = "https://github.com/comfyanonymous/ComfyUI.git",
    [switch]$Yes
)

$ErrorActionPreference = "Stop"

Write-Host "StoryVerse bootstrap-venv.ps1" -ForegroundColor Cyan
Write-Host "Default = light deps only. Torch/Comfy gated. Models NEVER downloaded." -ForegroundColor DarkCyan

function Resolve-PythonCommand {
    param([string]$Preferred)
    if ($Preferred) {
        return $Preferred
    }
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $list = & py -0p 2>$null | Out-String
        if ($list -match "3\.12") { return "py -3.12" }
        if ($list -match "3\.11") { return "py -3.11" }
        return "py"
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    throw "No Python launcher found. Install Python 3.11 or 3.12 and re-run."
}

function Invoke-Native {
    param([string]$Exe, [string[]]$ArgumentList)
    Write-Host ("+ {0} {1}" -f $Exe, ($ArgumentList -join " ")) -ForegroundColor DarkGray
    & $Exe @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $Exe $($ArgumentList -join ' ')"
    }
}

function Invoke-PythonModule {
    param([string]$PythonExe, [string[]]$ModuleArgs)
    Invoke-Native -Exe $PythonExe -ArgumentList (@("-m") + $ModuleArgs)
}

function Confirm-Gate {
    param(
        [string]$Title,
        [string]$Message,
        [switch]$SkipPrompt
    )
    if ($SkipPrompt) {
        Write-Host "Confirmed via -Yes: $Title" -ForegroundColor Yellow
        return $true
    }
    Write-Host ""
    Write-Host "GATE: $Title" -ForegroundColor Yellow
    Write-Host $Message
    $answer = Read-Host "Type YES to continue (anything else aborts this gated step)"
    return ($answer -eq "YES")
}

# --- Resolve base Python ---
$launcher = Resolve-PythonCommand -Preferred $PythonLauncher
Write-Host "Using Python launcher: $launcher"

# Create venv
if (-not (Test-Path -LiteralPath $VenvPath)) {
    Write-Host "Creating venv at $VenvPath"
    $createArgs = @("-m", "venv", $VenvPath)
    if ($launcher -like "py *") {
        $parts = $launcher.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
        Invoke-Native -Exe $parts[0] -ArgumentList ($parts[1..($parts.Length-1)] + $createArgs)
    }
    else {
        Invoke-Native -Exe $launcher -ArgumentList $createArgs
    }
}
else {
    Write-Host "Venv already exists: $VenvPath"
}

$venvPython = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Expected venv python missing: $venvPython"
}

Write-Host "Upgrading pip/setuptools/wheel..."
Invoke-PythonModule -PythonExe $venvPython -ModuleArgs @("pip", "install", "--upgrade", "pip", "setuptools", "wheel")

# Light dependency set — keep intentionally small for Phase 2
$lightPackages = @(
    "fastapi",
    "uvicorn[standard]",
    "httpx",
    "pydantic",
    "python-multipart",
    "aiosqlite",
    "pytest"
)

Write-Host "Installing LIGHT packages only:"
$lightPackages | ForEach-Object { Write-Host "  - $_" }
Invoke-PythonModule -PythonExe $venvPython -ModuleArgs (@("pip", "install") + $lightPackages)

Write-Host "Light venv ready." -ForegroundColor Green

# --- Optional: PyTorch CUDA ---
if ($ApproveTorch) {
    $torchMsg = @"
This will download PyTorch CUDA wheels from:
  index: $TorchIndexUrl
  packages: $TorchPackages
Size is typically multiple GB. This is NOT a generative model checkpoint, but it is a large download.
Official chooser: https://pytorch.org/get-started/locally/
Verify the CUDA index matches your NVIDIA driver before continuing.
"@
    if (Confirm-Gate -Title "Install PyTorch CUDA wheels" -Message $torchMsg -SkipPrompt:$Yes) {
        Write-Host "Installing PyTorch from $TorchIndexUrl ..." -ForegroundColor Yellow
        $torchArgs = @("pip", "install") + $TorchPackages.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries) + @("--index-url", $TorchIndexUrl)
        Invoke-PythonModule -PythonExe $venvPython -ModuleArgs $torchArgs
        Write-Host "Probing torch.cuda ..."
        & $venvPython -c "import torch; print('torch', torch.__version__); print('cuda_available', torch.cuda.is_available()); print('cuda', torch.version.cuda)"
    }
    else {
        Write-Host "Skipped PyTorch install (gate declined)." -ForegroundColor DarkYellow
    }
}
else {
    Write-Host "PyTorch step skipped (pass -ApproveTorch to enable)." -ForegroundColor DarkGray
}

# --- Optional: ComfyUI clone (code only) ---
if ($ApproveComfyClone) {
    $comfyMsg = @"
This will git clone ComfyUI sources ONLY into:
  $ComfyPath
Repo: $ComfyRepoUrl
No model weights / checkpoints will be downloaded by this script.
You must still avoid placing safetensors/GGUF into models/ until a separate approval.
"@
    if (Confirm-Gate -Title "Clone ComfyUI repository (code only)" -Message $comfyMsg -SkipPrompt:$Yes) {
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            throw "git not found; install Git for Windows first."
        }
        if (Test-Path -LiteralPath $ComfyPath) {
            Write-Host "Comfy path already exists, leaving untouched: $ComfyPath" -ForegroundColor DarkYellow
        }
        else {
            $parent = Split-Path -Parent $ComfyPath
            if ($parent -and -not (Test-Path -LiteralPath $parent)) {
                New-Item -ItemType Directory -Path $parent -Force | Out-Null
            }
            Invoke-Native -Exe "git" -ArgumentList @("clone", "--depth", "1", $ComfyRepoUrl, $ComfyPath)
            Write-Host "ComfyUI cloned. Do NOT download models yet." -ForegroundColor Green
        }
    }
    else {
        Write-Host "Skipped ComfyUI clone (gate declined)." -ForegroundColor DarkYellow
    }
}
else {
    Write-Host "ComfyUI clone skipped (pass -ApproveComfyClone to enable)." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Bootstrap finished." -ForegroundColor Green
Write-Host "Reminder: no generative model downloads were performed by this script." -ForegroundColor Green
Write-Host "Next: run collect-env.ps1 and fill docs/phase-2-live-checklist.md"
