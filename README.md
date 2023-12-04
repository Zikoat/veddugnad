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
create wallpaper