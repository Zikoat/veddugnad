@echo off
cd /d "%~dp0"
echo Pulling latest changes from the main branch...
git checkout main
git pull
echo Creating/Updating the 'prod' tag...
git tag -f prod
git push origin :refs/tags/prod
git push origin prod
echo Update complete.
.\venv\Scripts\python .\veddugnad.py %*
pause
