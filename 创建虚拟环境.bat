@echo off
chcp 65001

:: 设置安装参数
set USE_MIRROR=true
set INSTALL_TYPE=preview
echo "USE_MIRROR: %USE_MIRROR%"
echo "INSTALL_TYPE: %INSTALL_TYPE%"
setlocal enabledelayedexpansion

cd /D "%~dp0"

set PATH="%PATH%";%SystemRoot%\system32

echo %PATH%

:: 检查当前路径是否包含特殊字符
echo "%CD%"| findstr /R /C:"[!#\$%&()\*+,;<=>?@\[\]\^`{|}~\u4E00-\u9FFF ] " >nul && (
    echo.
    echo 当前路径包含特殊字符，请确保路径中不含特殊字符后再运行。 && (
        goto end
    )
)

:: 更新安装目录
set INSTALL_DIR=%cd%\venv
set CONDA_ROOT_PREFIX=%cd%\venv\conda

:: 让用户选择环境目录
echo 请选择要使用的环境目录：
dir /b /ad "%INSTALL_DIR%\py*"
set /p ENV_CHOICE=请输入选择的目录名（例如：py310）：
set INSTALL_ENV_DIR=%INSTALL_DIR%\%ENV_CHOICE%

:: 从选择的目录名中提取 Python 版本
set PYTHON_VERSION=%ENV_CHOICE:~2%

set PIP_CMD=%INSTALL_ENV_DIR%\python -m pip
set PYTHON_CMD=%INSTALL_ENV_DIR%\python
set TMP=%INSTALL_DIR%\tmp
set TEMP=%INSTALL_DIR%\tmp

:: 设置 Miniconda 下载 URL 和校验和
set MINICONDA_DOWNLOAD_URL=https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py310_23.3.1-0-Windows-x86_64.exe
set MINICONDA_CHECKSUM=307194e1f12bbeb52b083634e89cc67db4f7980bd542254b43d3309eaf7cb358

:: 检查是否已安装 Conda
set conda_exists=F
call "%CONDA_ROOT_PREFIX%\_conda.exe" --version >nul 2>&1
if "%ERRORLEVEL%" EQU "0" set conda_exists=T

:: 如果未安装 Conda，则下载并安装
if "%conda_exists%" == "F" (
    echo 正在下载 Miniconda...
    mkdir "%INSTALL_DIR%" 2>nul
    call curl -Lk "%MINICONDA_DOWNLOAD_URL%" > "%INSTALL_DIR%\miniconda_installer.exe"
    if errorlevel 1 (
        echo 下载 Miniconda 失败。
        goto end
    )
    
    :: 验证下载文件的校验和
    for /f %%a in ('
        certutil -hashfile "%INSTALL_DIR%\miniconda_installer.exe" sha256
        ^| find /i /v " "
        ^| find /i "%MINICONDA_CHECKSUM%"
    ') do (
        set "hash=%%a"
    )
    if not defined hash (
        echo Miniconda 校验和不匹配！
        del "%INSTALL_DIR%\miniconda_installer.exe"
        goto end
    ) else (
        echo Miniconda 校验和验证成功。
    )
    
    :: 安装 Miniconda
    echo 正在安装 Miniconda 到 "%CONDA_ROOT_PREFIX%"
    start /wait "" "%INSTALL_DIR%\miniconda_installer.exe" /InstallationType=JustMe /NoShortcuts=1 /AddToPath=0 /RegisterPython=0 /NoRegistry=1 /S /D=%CONDA_ROOT_PREFIX%

    call "%CONDA_ROOT_PREFIX%\_conda.exe" --version
    if errorlevel 1 (
        echo Miniconda 安装失败。
        goto end
    ) else (
        echo Miniconda 安装成功。
    )

    del "%INSTALL_DIR%\miniconda_installer.exe"
)

:: 创建 Conda 环境（如果不存在）
if not exist "%INSTALL_ENV_DIR%" (
    echo 正在创建 Conda 环境...
    call "%CONDA_ROOT_PREFIX%\_conda.exe" create --no-shortcuts -y -k --prefix "%INSTALL_ENV_DIR%" -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/ python=%PYTHON_VERSION:~0,1%.%PYTHON_VERSION:~1%

    if errorlevel 1 (
        echo 创建环境失败。
        goto end
    )
)

if not exist "%INSTALL_ENV_DIR%\python.exe" (
    echo Conda 环境不存在。
    goto end
)

:: 设置环境变量
set PYTHONNOUSERSITE=1
set PYTHONPATH=
set PYTHONHOME=
set "CUDA_PATH=%INSTALL_ENV_DIR%"
set "CUDA_HOME=%CUDA_PATH%"

:: 激活 Conda 环境
call "%CONDA_ROOT_PREFIX%\condabin\conda.bat" activate "%INSTALL_ENV_DIR%"

if errorlevel 1 (
    echo 激活环境失败。
    goto end
) else (
    echo 环境创建并激活成功。
)

echo 环境检查: 成功。

endlocal
goto :eof

:end
pause