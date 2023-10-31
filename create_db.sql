CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS buttons (
    button_id INTEGER PRIMARY KEY,
    hex_color TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS button_presses (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    player_id INTEGER,
    FOREIGN KEY (player_id) REFERENCES players(id)
);
CREATE TABLE IF NOT EXISTS player_button_date (
    player_id INTEGER,
    button_id INTEGER,
    date DATE,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (button_id) REFERENCES buttons(button_id)
);
CREATE VIEW IF NOT EXISTS daily_scores AS
SELECT p.name AS player_name,
    count(bp.id) AS score,
    min(bp.timestamp) AS startedAt,
    max(bp.timestamp) AS stoppedAt,
    pbd.date,
    pbd.button_id,
    CASE
        WHEN count(bp.id) > 1 THEN (
            julianday(max(bp.timestamp)) - julianday(min(bp.timestamp))
        ) * 86400 / (count(bp.id) - 1)
        ELSE 0
    END as speed
FROM button_presses bp
    JOIN player_button_date pbd ON bp.player_id = pbd.player_id
    JOIN players p ON bp.player_id = p.id
GROUP BY p.name,
    pbd.date,
    pbd.button_id;