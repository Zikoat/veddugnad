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
    button_id INTEGER,
    FOREIGN KEY (button_id) REFERENCES buttons(button_id)
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
    COUNT(bp.id) AS score,
    MIN(bp.timestamp) AS startedAt,
    MAX(bp.timestamp) AS stoppedAt,
    pbd.date,
    pbd.button_id,
    CASE
        WHEN COUNT(bp.id) > 1 THEN (
            julianday(MAX(bp.timestamp)) - julianday(MIN(bp.timestamp))
        ) * 86400 / (COUNT(bp.id) - 1)
        ELSE 0
    END as speed
FROM button_presses bp
    JOIN player_button_date pbd ON bp.button_id = pbd.button_id
    JOIN players p ON pbd.player_id = p.id
WHERE bp.timestamp BETWEEN pbd.date AND pbd.date || ' 23:59:59'
GROUP BY p.name,
    pbd.date,
    pbd.button_id;