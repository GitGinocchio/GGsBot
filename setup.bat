@echo off
setlocal

REM Constants
set "REPO_URL=GitGinocchio/GGsBot"
set "MAIN_SCRIPT=main.py"

REM Function to prompt for input
:prompt
set /p %1=%2
goto :eof

REM Function to prompt for password
:prompt_password
<nul set /p=%2
setlocal enabledelayedexpansion
for /f "delims=" %%P in ('powershell -Command "$pword = Read-Host -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pword))"') do set "password=%%P"
endlocal & set %1=%password%
goto :eof

REM Function to clone or update repo
:clone_or_update_repo
if exist ".git" (
    if not exist ".git-credentials" (
        call :prompt username "Enter your repository username: "
        call :prompt_password password "Enter your repository password/token: "

        set "credentials=https://%username%:%password%@github.com"
        echo %credentials% > ".git-credentials"
        echo Created .git-credentials
    )

    REM Set Git config for pull.rebase to false
    git config pull.rebase false
    if errorlevel 1 (
        echo Error setting git config
        exit /b 1
    ) else (
        echo Git pull rebase strategy set to false
    )

    REM Pull updates
    git pull
    if errorlevel 1 (
        echo Error updating repository
        exit /b 1
    ) else (
        echo Repository updated successfully
    )
) else (
    call :prompt username "Enter your repository username: "
    call :prompt_password password "Enter your repository password/token: "

    set "clone_url=https://%username%:%password%@github.com/%REPO_URL%"
    git clone %clone_url% .
    if errorlevel 1 (
        echo Error cloning repository
        exit /b 1
    ) else (
        echo Repository cloned successfully
        echo https://%username%:%password%@github.com > ".git-credentials"
        echo Created .git-credentials

        REM Set Git config for pull.rebase to false
        git config pull.rebase false
        if errorlevel 1 (
            echo Error setting git config
            exit /b 1
        ) else (
            echo Git pull rebase strategy set to false
        )
    )
)
exit /b

REM Function to install requirements
:install_requirements
if exist "requirements.txt" (
    echo Installing requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error installing requirements
        exit /b 1
    ) else (
        echo Requirements installed successfully
    )
) else (
    echo Requirements file requirements.txt not found
)
exit /b

REM Main function
:main
echo Starting setup...
call :clone_or_update_repo
call :install_requirements
echo Setup completed successfully
exit /b

REM Call main function
call :main
