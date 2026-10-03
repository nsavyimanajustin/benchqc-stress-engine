<#
.SYNOPSIS
    BenchQC Hardware Stress-Testing & Battery Sustenance Suite - PowerShell Launcher
.DESCRIPTION
    Launches BenchQC on Windows with native ANSI color support, telemetry collection,
    and automatic error checking.
#>

param(
    [switch]$Quick,
    [string]$Output = "benchqc_audit.json",
    [switch]$NoBanner,
    [switch]$Help
)

Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "  BenchQC Hardware Stress-Testing & Battery Sustenance Suite (Windows)" -ForegroundColor Green
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# Find Python executable
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
}

if (-not $PythonCmd) {
    Write-Host "[ERROR] Python 3 was not found on your system." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/ or Windows Store." -ForegroundColor Yellow
    Read-Host -Prompt "Press Enter to exit"
    exit 1
}

# Construct arguments
$Arguments = @("-m", "benchqc", "-o", $Output)
if ($Quick) { $Arguments += "--quick" }
if ($NoBanner) { $Arguments += "--no-banner" }
if ($Help) { $Arguments += "--help" }

Write-Host "[i] Executing: $PythonCmd $($Arguments -join ' ')" -ForegroundColor DarkGray
& $PythonCmd $Arguments

$ExitCode = $LASTEXITCODE
if ($ExitCode -eq 0) {
    Write-Host ""
    Write-Host "[+] Audit completed successfully!" -ForegroundColor Green
    Write-Host "[+] JSON artifact ready at: $Output" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "[-] BenchQC finished with return code $ExitCode" -ForegroundColor Yellow
}

exit $ExitCode
