CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS button (
    button_id INTEGER PRIMARY KEY,
    hex_color TEXT NOT NULL
);
INSERT
    OR IGNORE INTO button (button_id, hex_color)
VALUES (1, '#FF0000'),
    (2, '#00FF00'),
    (3, '#0000FF'),
    (4, '#FFFF00'),
    (5, '#FF00FF'),
    (6, '#00FFFF');
CREATE TABLE IF NOT EXISTS score (
    player_id INTEGER,
    button_id INTEGER,
    date DATE,
    presses INTEGER DEFAULT 0,
    startedAt DATETIME,
    stoppedAt DATETIME,
    FOREIGN KEY (player_id) REFERENCES player(id),
    FOREIGN KEY (button_id) REFERENCES button(button_id)
);
CREATE VIEW IF NOT EXISTS daily_scores AS
SELECT pl.name AS player_name,
    s.presses AS score,
    s.startedAt,
    s.stoppedAt,
    s.date,
    s.button_id,
    CASE
        WHEN s.presses > 1 THEN (
            julianday(s.stoppedAt) - julianday(s.startedAt)
        ) * 86400 / (s.presses - 1)
        ELSE 0
    END as speed
FROM score s
    JOIN player pl ON s.player_id = pl.id
GROUP BY pl.name,
    s.date,
    s.button_id;