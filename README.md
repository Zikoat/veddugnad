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