@echo off
chcp 65001 > nul 2>&1

:: Check if in repo root
if not exist ".git" (
    echo [ERROR] Please run this script in the repo root directory!
    pause
    exit /b 1
)

:: Check hook files exist
set "ERR=0"
if not exist "git-hooks\pre-commit" (echo [ERROR] git-hooks\pre-commit not found! & set "ERR=1")
if not exist "git-hooks\post-push" (echo [ERROR] git-hooks\post-push not found! & set "ERR=1")
if %ERR% equ 1 (pause & exit /b 1)

:: Copy hooks to .git/hooks
echo [INFO] Copying git hooks...
copy /y "git-hooks\pre-commit" ".git\hooks\pre-commit" > nul 2>&1 || (echo [ERROR] Failed to copy pre-commit! & pause & exit /b 1)
copy /y "git-hooks\post-push" ".git\hooks\post-push" > nul 2>&1 || (echo [ERROR] Failed to copy post-push! & pause & exit /b 1)

:: Init pre-commit
echo [INFO] Initializing pre-commit...
pre-commit install > nul 2>&1
if errorlevel 1 (echo [WARNING] pre-commit init failed! Run: pre-commit install ^|^| pip install pre-commit) else (echo [INFO] pre-commit init success!)

:: Finish
echo.
echo [OK] Git hooks configured successfully!
echo [INFO] 1. git commit: Auto install dependencies and check code style
echo [INFO] 2. git push: Auto restore git hooks config
echo.
pause
exit /b 0