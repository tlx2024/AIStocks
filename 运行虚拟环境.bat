@echo off
chcp 65001

:: 设置代理
set no_proxy="127.0.0.1, 0.0.0.0, localhost"
setlocal enabledelayedexpansion

:: 切换到脚本所在目录
cd /D "%~dp0"

:: 设置系统路径
set PATH=%PATH%;%INSTALL_ENV_DIR%;%INSTALL_ENV_DIR%\Scripts;%INSTALL_ENV_DIR%\Library\bin

:: 检查当前路径是否包含特殊字符
echo "%CD%"| findstr /R /C:"[!#\$%&()\*+,;<=>?@\[\]\^`{|}~\u4E00-\u9FFF ] " >nul && (
    echo.
    echo 当前路径包含特殊字符，请确保路径中不含特殊字符后再运行。 && (
        goto end
    )
)

:: 设置临时目录
set TMP=%CD%\venv\tmp
set TEMP=%CD%\venv\tmp

:: 取消激活可能存在的其他环境
(call conda deactivate && call conda deactivate && call conda deactivate) 2>nul

:: 设置Conda根目录
set CONDA_ROOT_PREFIX=%cd%\venv\conda

:: 让用户选择环境目录
echo 请选择要使用的环境目录：
dir /b /ad "%cd%\venv\py*"
set /p ENV_CHOICE=请输入选择的目录名（例如：py310）：
set INSTALL_ENV_DIR=%cd%\venv\%ENV_CHOICE%

:: 设置Python环境变量
set PYTHONNOUSERSITE=1
set PYTHONPATH=
set PYTHONHOME=

:: 激活选择的Conda环境
call "%CONDA_ROOT_PREFIX%\condabin\conda.bat" activate "%INSTALL_ENV_DIR%"

if errorlevel 1 (
    echo.
    echo 环境激活失败。
    goto end
) else (
    echo.
    echo 环境激活成功。
)

:: 保持命令窗口打开，并允许执行其他命令
cmd /k "%*"

:end
pause