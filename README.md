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

## tasks

fix date display, add year and weekday
dont show zero scores on leaderboard
center leaderboard sekker
add breaks
error on player add when player is selected
make combo not editable
show custom error message when player name is empty when you are oking after edit
when creating a new player, show input field for name, maybe reuse from edit player. default should be content from combobox, if we still want to use editable combobox.
add indexes
load test
dont pass date, but use function to get it. its global.
dedupe _get_connection