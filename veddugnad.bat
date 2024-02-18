@echo off
cd /d "%~dp0"

:: Check for internet connection
ping -n 1 google.com >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Internet connection detected. Proceeding with backup and update...

    :: Backup the SQLite database
    copy /Y highscores.db highscores_backup.db
    git add highscores_backup.db
    git commit -m "Backup of highscores.db on %DATE% %TIME%"
    git push origin HEAD:db-backup

    :: Switch back to the main branch to pull the latest changes and update prod tag
    git checkout main
    git pull
    
    echo Updating the 'prod' tag to the current commit...
    git tag -f prod
    git push origin :refs/tags/prod
    git push origin prod
    
) else (
    echo No internet connection detected. Skipping backup and update...
)

echo Starting the application...
.\venv\Scripts\python .\veddugnad.py %*
pause
