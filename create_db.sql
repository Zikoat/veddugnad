CREATE TABLE if not exists players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE if not exists buttons (
    button_id INTEGER PRIMARY KEY,
    hex_color TEXT NOT NULL
);
CREATE TABLE if not exists button_presses (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    player_id INTEGER,
    FOREIGN KEY (player_id) REFERENCES players(id)
);
CREATE TABLE if not exists player_button_date (
    player_id INTEGER,
    button_id INTEGER,
    date DATE,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (button_id) REFERENCES buttons(button_id)
);
CREATE VIEW if not exists daily_scores AS
SELECT p.name AS player_name,
    count(bp.id) AS score,
    min(bp.timestamp) AS startedAt,
    max(bp.timestamp) AS stoppedAt,
    pbd.date,
    pbd.button_id
FROM button_presses bp
    JOIN player_button_date pbd ON bp.player_id = pbd.player_id
    JOIN players p ON bp.player_id = p.id
GROUP BY p.name,
    pbd.date,
    pbd.button_id;