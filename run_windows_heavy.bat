@echo off
setlocal enabledelayedexpansion

title BenchQC MAXIMUM HEAVY STRESS TEST & Battery Sustenance Suite

echo ===============================================================================
echo   BenchQC MAXIMUM HEAVY STRESS TEST (45s 100%% CPU, 4GB RAM, Deep I/O)
echo   Target: Windows 10 / 11 (x64 / ARM64)
echo ===============================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python is not detected on your PATH.
        echo Please install Python 3.8+ from https://www.python.org/ or the Microsoft Store.
        pause
        exit /b 1
    ) else (
        set PY_CMD=py
    )
) else (
    set PY_CMD=python
)

:: 2. Launch BenchQC Heavy
echo [i] Starting BenchQC Heavy Torture & Battery Sustenance Audit...
%PY_CMD% -m benchqc --heavy %*

if %errorlevel% equ 0 (
    echo.
    echo ===============================================================================
    echo [SUCCESS] Heavy Stress Audit finished successfully!
    echo - Visual HTML Certificate : benchqc_report.html
    echo - Machine Audit Artifact  : benchqc_audit.json
    echo ===============================================================================
    echo.
    if exist benchqc_report.html (
        echo [i] Launching visual HTML report in your default browser...
        start benchqc_report.html
    )
) else (
    echo.
    echo [WARNING] BenchQC exited with status %errorlevel%.
)

echo.
pause
