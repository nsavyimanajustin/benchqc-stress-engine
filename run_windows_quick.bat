@echo off
setlocal enabledelayedexpansion

title BenchQC FAST INTAKE AUDIT (10s Hardware & Battery Check)

echo ===============================================================================
echo   BenchQC FAST INTAKE AUDIT (10-Second Hardware & Battery Check)
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

:: 2. Launch BenchQC Quick
echo [i] Starting BenchQC Fast Intake Audit...
%PY_CMD% -m benchqc --quick %*

if %errorlevel% equ 0 (
    echo.
    echo ===============================================================================
    echo [SUCCESS] Fast Intake Audit finished successfully!
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
