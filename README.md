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

## tasks

show error or handle when player name is empty
add breaks
dont show zero scores on leaderboard
error on player add when player is selected
fix speed calculation
fix date display, add year and weekday
center leaderboard sekker
make combo not editable
on new player, show input field for name, maybe reuse from edit player