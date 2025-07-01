@echo off
setlocal enabledelayedexpansion

:: SEMagi API Windows Client - Simplified Version
:: This version uses only 'python' command for better compatibility

:: Set UTF-8 encoding
chcp 65001 >nul 2>&1

set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%scripts\api_client.py"

:: Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    echo [INFO] Please install Python from https://www.python.org/downloads/
    exit /b 1
)

:: Verify it's Python 3
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PY_VER=%%i"
if not "%PY_VER:~0,1%"=="3" (
    echo [ERROR] Python 3 required, but found Python %PY_VER%
    exit /b 1
)

:: Check requests module
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python requests module not found
    echo [INFO] Please run: pip install requests
    exit /b 1
)

:: Parse command
set "OPERATION=%1"
set "TASK_ID="

:: Handle task ID for status/results operations
if "%OPERATION%"=="check-status" set "TASK_ID=%2"
if "%OPERATION%"=="get-results" set "TASK_ID=%2"
if "%1"=="-t" (
    set "TASK_ID=%2"
    set "OPERATION=%3"
)
if "%1"=="--task-id" (
    set "TASK_ID=%2"
    set "OPERATION=%3"
)

:: Show help if no operation
if "%OPERATION%"=="" goto :show_help
if "%OPERATION%"=="-h" goto :show_help
if "%OPERATION%"=="--help" goto :show_help

:: Execute based on operation
if "%OPERATION%"=="create-task" (
    echo [INFO] Creating task using settings.json...
    python "%PYTHON_SCRIPT%"
    exit /b %ERRORLEVEL%
)

if "%OPERATION%"=="check-status" (
    if "%TASK_ID%"=="" (
        echo [ERROR] Task ID required for check-status
        echo [INFO] Usage: %~nx0 check-status TASK_ID
        exit /b 1
    )
    echo [INFO] Checking status for task: %TASK_ID%
    python "%PYTHON_SCRIPT%" --check-status %TASK_ID%
    exit /b %ERRORLEVEL%
)

if "%OPERATION%"=="get-results" (
    if "%TASK_ID%"=="" (
        echo [ERROR] Task ID required for get-results
        echo [INFO] Usage: %~nx0 get-results TASK_ID
        exit /b 1
    )
    echo [INFO] Getting results for task: %TASK_ID%
    python "%PYTHON_SCRIPT%" --get-results %TASK_ID%
    exit /b %ERRORLEVEL%
)

echo [ERROR] Unknown operation: %OPERATION%
echo.

:show_help
echo SEMagi API Windows Client - Simplified Version
echo.
echo Usage:
echo   %~nx0 create-task                Create new task using settings.json
echo   %~nx0 check-status TASK_ID       Check task status
echo   %~nx0 get-results TASK_ID        Get task results
echo   %~nx0 -t TASK_ID check-status    Alternative syntax
echo.
echo Examples:
echo   %~nx0 create-task
echo   %~nx0 check-status abc123
echo   %~nx0 get-results abc123
echo.
exit /b 0