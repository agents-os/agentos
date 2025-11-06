@echo off
REM AgentOS Command Wrapper for Windows
REM This script activates the virtual environment and runs agentos.py

set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

call "%PROJECT_DIR%\.venv\Scripts\activate.bat"
python "%PROJECT_DIR%\agentos.py" %*
