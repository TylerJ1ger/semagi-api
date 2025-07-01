@echo off
REM SEMagi API Windows 客户端脚本
REM 统一入口，只使用 Python 客户端

setlocal enabledelayedexpansion

REM 脚本信息
set SCRIPT_VERSION=1.0.0
set SCRIPT_DIR=%~dp0
set SCRIPTS_DIR=%SCRIPT_DIR%scripts

REM 颜色输出（Windows 10+）
for /f "tokens=2 delims=[]" %%x in ('ver') do set winver=%%x
for /f "tokens=2,3,4 delims=. " %%x in ("%winver%") do set /a winbuild=%%z
if %winbuild% geq 10586 (
    set "GREEN=[92m"
    set "RED=[91m"
    set "YELLOW=[93m"
    set "BLUE=[94m"
    set "RESET=[0m"
) else (
    set "GREEN="
    set "RED="
    set "YELLOW="
    set "BLUE="
    set "RESET="
)

REM 输出函数模拟
set "log_info=echo %BLUE%i%RESET%"
set "log_success=echo %GREEN%√%RESET%"
set "log_warning=echo %YELLOW%!%RESET%"
set "log_error=echo %RED%×%RESET%"

REM 显示横幅
:show_banner
echo %BLUE%
echo ╔══════════════════════════════════════════╗
echo ║       SEMagi API 跨平台统一客户端        ║
echo ║            版本 %SCRIPT_VERSION%                    ║
echo ╚══════════════════════════════════════════╝
echo %RESET%
goto :eof

REM 显示帮助
:show_help
call :show_banner
echo.
echo %BLUE%用法:%RESET%
echo   %0 [选项] ^<操作^>
echo.
echo %BLUE%系统要求:%RESET%
echo   • Python 3.x
echo   • requests 库 (pip install requests)
echo   • 支持 Windows
echo.
echo %BLUE%操作:%RESET%
echo   create-task       创建新任务
echo   check-status      查询任务状态
echo   get-results       获取任务结果
echo   wait-completion   等待任务完成
echo.
echo %BLUE%基本选项:%RESET%
echo   -u, --base-url URL     API基础URL (默认: 从配置文件读取)
echo.
echo %BLUE%创建任务选项 (可选，优先使用配置文件):%RESET%
echo   -f, --function TYPE    功能类型 (group-only^|scrap-and-group)
echo   -i, --file PATH        输入文件路径
echo   -n, --task-name NAME   任务名称
echo   -w, --wait             创建后等待完成
echo.
echo %BLUE%查询选项:%RESET%
echo   -t, --task-id ID       任务ID
echo.
echo %BLUE%客户端选项:%RESET%
echo   --show-client          显示客户端信息
echo.
echo %BLUE%其他选项:%RESET%
echo   -h, --help             显示此帮助
echo   -v, --verbose          详细输出
echo   --version              显示版本
echo   --check-env            检查环境依赖
echo.
echo %BLUE%使用示例:%RESET%
echo   REM 使用配置文件参数创建任务（推荐）
echo   %0 create-task
echo.
echo   REM 覆盖配置文件参数
echo   %0 -f scrap-and-group -i keywords.csv -n "custom_task" create-task
echo.
echo   REM 查询任务状态
echo   %0 -t "task_id" check-status
echo.
goto :eof

REM 检查环境依赖
:check_environment
set python_available=false

%log_info% 检查环境依赖...
%log_info% 操作系统: Windows

REM 检查Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set python_version=%%i
    %log_success% Python 可用: !python_version!
    
    REM 检查requests库
    python -c "import requests" >nul 2>&1
    if !errorlevel! equ 0 (
        %log_success% Python requests 库可用
        set python_available=true
    ) else (
        %log_warning% Python requests 库不可用
        echo   • Python requests库未安装，运行: pip install requests
    )
) else (
    python3 --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%i in ('python3 --version 2^>^&1') do set python_version=%%i
        %log_success% Python 可用: !python_version!
        
        python3 -c "import requests" >nul 2>&1
        if !errorlevel! equ 0 (
            %log_success% Python requests 库可用
            set python_available=true
        ) else (
            %log_warning% Python requests 库不可用
            echo   • Python requests库未安装，运行: pip install requests
        )
    ) else (
        %log_warning% Python 不可用
        echo   • Python未安装或不在PATH中
    )
)

echo.
%log_info% 环境检查总结:

if "%python_available%"=="true" (
    %log_success% Python客户端: 可用 √
) else (
    %log_warning% Python客户端: 不可用 ×
)

if "%python_available%"=="false" (
    echo.
    %log_error% Python客户端不可用！请安装Python3和requests库
    exit /b 1
)

echo.
%log_success% 将使用Python客户端
goto :eof

REM 检查API密钥
:check_config_api_key
set settings_file=%SCRIPT_DIR%settings.json
if not exist "%settings_file%" (
    exit /b 1
)

REM 使用Python读取API密钥
for /f "tokens=*" %%i in ('python -c "import json; f=open('%settings_file%','r'); s=json.load(f); print(s.get('api_key',''))" 2^>nul') do set api_key=%%i
if "%api_key%"=="" (
    exit /b 1
)
echo %api_key%
goto :eof

REM 主程序
:main
set verbose=false
set show_client=false
set check_env_only=false

REM 如果没有参数，显示帮助
if "%~1"=="" (
    call :show_help
    exit /b 0
)

REM 解析参数
:parse_args
if "%~1"=="" goto :args_done
if "%~1"=="-h" (
    call :show_help
    exit /b 0
)
if "%~1"=="--help" (
    call :show_help
    exit /b 0
)
if "%~1"=="--version" (
    call :show_banner
    echo 跨平台统一客户端版本: %SCRIPT_VERSION%
    echo 脚本位置: %SCRIPT_DIR%
    echo 检测到的操作系统: Windows
    exit /b 0
)
if "%~1"=="--check-env" (
    set check_env_only=true
)
if "%~1"=="--show-client" (
    set show_client=true
)
if "%~1"=="-v" (
    set verbose=true
)
if "%~1"=="--verbose" (
    set verbose=true
)
shift
goto :parse_args

:args_done

REM 如果只是检查环境
if "%check_env_only%"=="true" (
    call :show_banner
    call :check_environment
    exit /b %errorlevel%
)

REM 显示横幅
if "%verbose%"=="true" (
    call :show_banner
) else if "%show_client%"=="true" (
    call :show_banner
)

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    python3 --version >nul 2>&1
    if !errorlevel! neq 0 (
        %log_error% Python客户端不可用！请安装Python3和requests库
        echo.
        %log_info% 运行 '%0 --check-env' 来检查环境依赖
        exit /b 1
    ) else (
        set python_cmd=python3
    )
) else (
    set python_cmd=python
)

REM 检查requests库
%python_cmd% -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    %log_error% Python客户端不可用！请安装Python3和requests库
    echo.
    %log_info% 运行 '%0 --check-env' 来检查环境依赖
    exit /b 1
)

if "%show_client%"=="true" (
    %log_info% 使用客户端: %python_cmd%
)

if "%verbose%"=="true" (
    %log_info% 正在调用Python客户端...
)

REM 检查配置文件中的API密钥
call :check_config_api_key >nul 2>&1
if %errorlevel% neq 0 (
    %log_error% 需要在settings.json中配置API密钥
    %log_info% 请复制 settings.example.json 为 settings.json 并填入你的API密钥
    exit /b 1
)

if "%verbose%"=="true" (
    %log_info% 使用配置文件中的API密钥
)

REM 检查Python客户端脚本
set python_script=%SCRIPTS_DIR%\api_client.py
if not exist "%python_script%" (
    %log_error% Python客户端脚本不存在: %python_script%
    exit /b 1
)

REM 调用Python客户端（传递所有原始参数）
%python_cmd% "%python_script%" %*

goto :eof

REM 检查脚本目录
if not exist "%SCRIPTS_DIR%" (
    %log_error% 脚本目录不存在: %SCRIPTS_DIR%
    %log_info% 请确保在正确的目录中运行此脚本
    exit /b 1
)

REM 执行主函数
call :main %*