# veddugnad

## installation
1. download sqlite, extract it to a folder, and add that folder to PATH
2. Open powershell as admin, and run the following commands:
```shell
python3 -m venv myenv
.\myenv\scripts\activate
pip install -r requirements.txt
Get-Content create_db.sql | sqlite3 highscores.db
python3 veddugnad.py
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
