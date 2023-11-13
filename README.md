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

be able to delete player with no scores
fix crash on edit non selected player(disable or hide edit button)
fix crash on edit name to be same as other player
    dont save player on name, but on ok. show error if name is taken
    show error when player name is empty
add breaks
test mock time while running
dont show zero scores on leaderboard
move mock time
error on player add when player is selected
fix speed calculation
fix date display, add year and weekday