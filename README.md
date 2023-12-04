# veddugnad

## installation
1. download sqlite, extract it to a folder, and add that folder to PATH
2. Open powershell as admin, and run the following commands:
```shell
python -m venv venv
.\venv\scripts\activate
pip install -r requirements.txt
Get-Content create_db.sql | sqlite3 highscores.db
python veddugnad.py
```

## update requirements.txt
```shell
pip freeze > requirements.txt
```

## run linter
```shell
shed --refactor --py311-plus
```

## run typechecker
```shell
mypy .\veddugnad.py --strict
```

### TODO
create background
quotes

delete previous windows versions

find and or create wallpaper
start program on startup

install teamviewer, and test it works

edit veddugnad readme
winget install SQLite.SQLite --source winget
winget install Python.Python.3.12 --source winget

code:
move images and other files to its own folder

like stackoverflow:
https://stackoverflow.com/questions/4571244/creating-a-bat-file-for-python-script
https://stackoverflow.com/a/64262038
https://stackoverflow.com/questions/289498/running-batch-file-in-background-when-windows-boots-up?noredirect=1&lq=1