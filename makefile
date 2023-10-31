.PHONY: install run

activate:
	.\myenv\scripts\activate

install:
	make activate && python.exe -m pip install --upgrade pip && pip install -r requirements.txt

run: 
	make activate && python veddugnad.py

createdb:
	make activate && sqlite3 highscores.db < create_db.sql