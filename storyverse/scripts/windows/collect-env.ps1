<#
.SYNOPSIS
  StoryVerse Phase 2 — gather a live Windows environment report (no installs, no model downloads).

.DESCRIPTION
  Collects OS, GPU/nvidia-smi, Python, Git, FFmpeg, disk free, and optional torch.cuda probes.
  Writes Markdown + JSON under -OutputDir. Safe to run on any machine; does not modify the system.

.PARAMETER OutputDir
  Directory for report files. Created if missing. Default: .\reports

.PARAMETER ReportName
  Base filename without extension. Default: env-report-<timestamp>
#>
[CmdletBinding()]
param(
    [string]$OutputDir = ".\reports",
    [string]$ReportName = ""
)

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

function Invoke-Capture {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][scriptblock]$Script
    )
    $started = Get-Date
    $stdout = $null
    $stderr = $null
    $ok = $false
    $exitCode = $null
    try {
        $stdout = & $Script 2>&1 | Out-String
        if ($null -ne $LASTEXITCODE) { $exitCode = $LASTEXITCODE }
        $ok = $true
    }
    catch {
        $stderr = $_.Exception.Message
        $ok = $false
    }
    [pscustomobject]@{
        name       = $Name
        ok         = $ok
        exitCode   = $exitCode
        durationMs = [int]((Get-Date) - $started).TotalMilliseconds
        stdout     = if ($null -eq $stdout) { "" } else { $stdout.TrimEnd() }
        stderr     = if ($null -eq $stderr) { "" } else { $stderr }
    }
}

function Test-CommandExists {
    param([string]$CommandName)
    return [bool](Get-Command $CommandName -ErrorAction SilentlyContinue)
}

Write-Host "StoryVerse collect-env.ps1 — read-only probe (no installs / no model downloads)" -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
if ([string]::IsNullOrWhiteSpace($ReportName)) {
    $ReportName = "env-report-$timestamp"
}

$checks = @()

$checks += Invoke-Capture -Name "os.computerinfo" -Script {
    Get-ComputerInfo | Select-Object CsName, WindowsProductName, WindowsVersion, OsHardwareAbstractionLayer, OsTotalVisibleMemorySize | Format-List | Out-String
}

$checks += Invoke-Capture -Name "os.systeminfo.filtered" -Script {
    systeminfo | Select-String -Pattern "OS Name","OS Version","Total Physical Memory","System Type","Processor"
}

$checks += Invoke-Capture -Name "gpu.win32" -Script {
    Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, VideoProcessor | Format-List | Out-String
}

$checks += Invoke-Capture -Name "nvidia.smi" -Script {
    if (-not (Test-CommandExists "nvidia-smi")) { throw "nvidia-smi not found in PATH" }
    nvidia-smi
}

$checks += Invoke-Capture -Name "nvidia.smi.query" -Script {
    if (-not (Test-CommandExists "nvidia-smi")) { throw "nvidia-smi not found in PATH" }
    nvidia-smi --query-gpu=name,driver_version,memory.total,memory.free,compute_cap --format=csv
}

$checks += Invoke-Capture -Name "python.version" -Script {
    if (Test-CommandExists "python") { python --version }
    elseif (Test-CommandExists "py") { py --version }
    else { throw "python/py not found" }
}

$checks += Invoke-Capture -Name "python.py.list" -Script {
    if (-not (Test-CommandExists "py")) { throw "py launcher not found" }
    py -0p
}

$checks += Invoke-Capture -Name "python.where" -Script {
    where.exe python
}

$checks += Invoke-Capture -Name "pip.version" -Script {
    if (Test-CommandExists "pip") { pip --version }
    elseif (Test-CommandExists "python") { python -m pip --version }
    else { throw "pip not found" }
}

$checks += Invoke-Capture -Name "git.version" -Script {
    if (-not (Test-CommandExists "git")) { throw "git not found" }
    git --version
}

$checks += Invoke-Capture -Name "ffmpeg.version" -Script {
    if (-not (Test-CommandExists "ffmpeg")) { throw "ffmpeg not found" }
    ffmpeg -version
}

$checks += Invoke-Capture -Name "ffmpeg.where" -Script {
    where.exe ffmpeg
}

$checks += Invoke-Capture -Name "disk.psdrive" -Script {
    Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N="UsedGB";E={[math]::Round(($_.Used/1GB),2)}}, @{N="FreeGB";E={[math]::Round(($_.Free/1GB),2)}} | Format-Table -AutoSize | Out-String
}

$checks += Invoke-Capture -Name "disk.volume" -Script {
    Get-Volume | Select-Object DriveLetter, FileSystemLabel, FileSystem, @{N="SizeGB";E={[math]::Round(($_.Size/1GB),2)}}, @{N="FreeGB";E={[math]::Round(($_.SizeRemaining/1GB),2)}} | Format-Table -AutoSize | Out-String
}

$checks += Invoke-Capture -Name "torch.probe" -Script {
    $py = $null
    if (Test-Path ".\venv\Scripts\python.exe") { $py = ".\venv\Scripts\python.exe" }
    elseif (Test-CommandExists "python") { $py = "python" }
    else { throw "no python for torch probe" }
    & $py -c "import importlib.util,sys
spec=importlib.util.find_spec('torch')
if spec is None:
    print('torch_installed=False')
    sys.exit(0)
import torch
print('torch_installed=True')
print('torch_version=' + torch.__version__)
print('cuda_available=' + str(torch.cuda.is_available()))
print('torch_version_cuda=' + str(torch.version.cuda))
print('device_name=' + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'))
"
}

$checks += Invoke-Capture -Name "paths.comfy_hint" -Script {
    $candidates = @(
        ".\apps\comfyui",
        "$env:USERPROFILE\ComfyUI",
        "C:\ComfyUI"
    )
    foreach ($c in $candidates) {
        $main = Join-Path $c "main.py"
        "{0} => exists={1} main.py={2}" -f $c, (Test-Path $c), (Test-Path $main)
    }
}

$summary = [ordered]@{
    schema           = "storyverse.collect-env.v1"
    generatedAtUtc   = (Get-Date).ToUniversalTime().ToString("o")
    machineName      = $env:COMPUTERNAME
    userName         = $env:USERNAME
    pwshVersion      = $PSVersionTable.PSVersion.ToString()
    note             = "Read-only environment probe. No packages installed. No model weights downloaded."
    checks           = $checks
}

$jsonPath = Join-Path $OutputDir ($ReportName + ".json")
$mdPath   = Join-Path $OutputDir ($ReportName + ".md")

$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$md = @()
$md += "# StoryVerse environment report"
$md += ""
$md += "| Field | Value |"
$md += "|-------|-------|"
$md += "| generatedAtUtc | $($summary.generatedAtUtc) |"
$md += "| machineName | $($summary.machineName) |"
$md += "| userName | $($summary.userName) |"
$md += "| pwshVersion | $($summary.pwshVersion) |"
$md += "| policy | no installs / no model downloads |"
$md += ""

foreach ($c in $checks) {
    $status = if ($c.ok) { "OK" } else { "FAIL" }
    $md += "## $($c.name) — $status"
    $md += ""
    $md += '```text'
    if ($c.stdout) { $md += $c.stdout }
    if ($c.stderr) { $md += "ERROR: $($c.stderr)" }
    if (-not $c.stdout -and -not $c.stderr) { $md += "(empty)" }
    $md += '```'
    $md += ""
}

$md += "## Next steps"
$md += ""
$md += "1. Paste key rows into docs/phase-2-live-checklist.md"
$md += "2. Run bootstrap-venv.ps1 without -ApproveTorch / -ApproveComfyClone unless explicitly approved"
$md += "3. Do not download SD/Wan/LTX/TTS weights until a separate approval names the model"
$md += ""

($md -join "`n") | Set-Content -LiteralPath $mdPath -Encoding UTF8

Write-Host "Wrote $mdPath" -ForegroundColor Green
Write-Host "Wrote $jsonPath" -ForegroundColor Green
Write-Host "Done. No installs performed; no models downloaded." -ForegroundColor Green
