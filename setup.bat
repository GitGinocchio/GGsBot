@echo off
REM Setup script for GGsBot

REM Set variables
set REPO_URL=GitGinocchio/GGsBot
set REPO_DIR=GGsBot
set MAIN_SCRIPT=main.py

REM Create directory if not exists
if not exist "%REPO_DIR%" mkdir "%REPO_DIR%"

REM Check if .git directory exists
if exist "%REPO_DIR%\.git" (
    REM Check if .git-credentials exists
    if not exist "%REPO_DIR%\.git-credentials" (
        REM Prompt for username and password/token
        set /p username=Enter your repository username: 
        set /p password=Enter your repository password/token: 
        
        REM Create .git-credentials file
        echo https://%username%:%password%@github.com> "%REPO_DIR%\.git-credentials"
        echo Created .git-credentials
    )

    REM Set Git config for pull.rebase to false
    git -C "%REPO_DIR%" config pull.rebase false
    echo Git pull rebase strategy set to false
    
    REM Pull updates
    git -C "%REPO_DIR%" pull
    echo Repository updated successfully

) else (
    REM Clone repository with credentials included in URL
    set /p username=Enter your repository username: 
    set /p password=Enter your repository password/token: 

    git clone https://%username%:%password%@github.com/%REPO_URL% "%REPO_DIR%"
    echo Repository cloned successfully
    
    REM Create .git-credentials file
    echo https://%username%:%password%@github.com> "%REPO_DIR%\.git-credentials"
    echo Created .git-credentials
    
    REM Set Git config for pull.rebase to false
    git -C "%REPO_DIR%" config pull.rebase false
    echo Git pull rebase strategy set to false
)

REM Install requirements
if exist "%REPO_DIR%\requirements.txt" (
    echo Installing requirements...
    pip install -r "%REPO_DIR%\requirements.txt"
    echo Requirements installed successfully
) else (
    echo Requirements file requirements.txt not found in %REPO_DIR%
)
