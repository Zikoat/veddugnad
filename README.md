# veddugnad

## installation
1. Open powershell as admin, and run the following commands:
```shell
winget install SQLite.SQLite --source winget
winget install Python.Python.3.12 --source winget
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

find and or create wallpaper

like stackoverflow:
https://stackoverflow.com/questions/4571244/creating-a-bat-file-for-python-script
https://stackoverflow.com/a/64262038
https://stackoverflow.com/questions/289498/running-batch-file-in-background-when-windows-boots-up?noredirect=1&lq=1