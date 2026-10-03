@echo off
setlocal enabledelayedexpansion

title BenchQC Hardware Stress-Testing ^& Battery Sustenance Suite

echo ===============================================================================
echo   BenchQC Hardware Stress-Testing and Battery Sustenance Suite
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

:: 2. Launch BenchQC
echo [i] Starting BenchQC Hardware Audit...
%PY_CMD% -m benchqc %*

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Audit finished successfully.
    echo Audit artifact saved to: benchqc_audit.json
    echo You can now upload benchqc_audit.json to the BenchQC Storefront.
) else (
    echo.
    echo [WARNING] BenchQC exited with status %errorlevel%.
)

echo.
pause
