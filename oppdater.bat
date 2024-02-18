@echo off
cd /d "%~dp0"
echo Pulling changes from Git repository...
git pull
echo Pull complete.
pause
