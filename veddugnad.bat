@echo off
cd /d "%~dp0"

:: Check for internet connection
ping -n 1 google.com >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Internet connection detected. Proceeding with backup and update...

    :: Ensure we are on the main branch
    git checkout main
    git pull

    :: Backup the SQLite database by copying it and adding it to the staging area
    copy /Y highscores.db highscores_backup.db
    git add highscores_backup.db

    :: Commit the backup and push it directly to the db-backup branch on the remote
    git commit -m "Backup of highscores.db on %DATE% %TIME%"
    git push origin HEAD:refs/heads/db-backup

    :: Update the 'prod' tag to the current commit on main branch
    git tag -f prod
    git push origin :refs/tags/prod
    git push origin prod

) else (
    echo No internet connection detected. Skipping backup and update...
)

echo Starting the application...
.\venv\Scripts\python c:\veddugnad\veddugnad.py %*
pause
