-- Player table
CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    team TEXT CHECK(team IN ('Red', 'Orange', 'Green', 'Blue')),
    CHECK (name <> '')
);
-- Button table
CREATE TABLE IF NOT EXISTS button (
    button_id INTEGER PRIMARY KEY,
    hex_color TEXT NOT NULL
);
-- Insert buttons
REPLACE INTO button (button_id, hex_color)
VALUES (1, '#FF0000'),
    (2, '#00FF00'),
    (3, '#0000FF'),
    (4, '#FFFF00'),
    (5, '#FF00FF'),
    (6, '#00FFFF');
-- Selected player table
CREATE TABLE IF NOT EXISTS selected_player (
    id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL,
    button_id INTEGER NOT NULL,
    date DATE NOT NULL,
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE,
    FOREIGN KEY (button_id) REFERENCES button(button_id),
    UNIQUE (player_id, date),
    UNIQUE (button_id, date)
);
-- Presses table
CREATE TABLE IF NOT EXISTS presses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE
);
-- Breaks table
CREATE TABLE IF NOT EXISTS breaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL
);
-- Score view
DROP VIEW IF EXISTS [score];
CREATE VIEW IF NOT EXISTS score AS
SELECT sp.player_id,
    sp.button_id,
    sp.date,
    COALESCE(COUNT(p.id), 0) AS presses,
    MIN(p.timestamp) AS startedAt,
    MAX(p.timestamp) AS stoppedAt
FROM selected_player sp
    LEFT JOIN presses p ON sp.player_id = p.player_id
    AND p.timestamp BETWEEN sp.date AND sp.date || ' 23:59:59'
GROUP BY sp.player_id,
    sp.button_id,
    sp.date;
-- Daily scores view
DROP VIEW IF EXISTS [daily_scores];
CREATE VIEW daily_scores AS
SELECT pl.name AS player_name,
    s.presses AS score,
    s.startedAt,
    s.stoppedAt,
    s.date,
    s.button_id,
    s.player_id,
    CASE
        WHEN s.startedAt IS NOT NULL
        AND s.stoppedAt IS NOT NULL
        AND (julianday(s.stoppedAt) - julianday(s.startedAt)) > 0 THEN s.presses / (
            (
                (julianday(s.stoppedAt) - julianday(s.startedAt)) - (
                    SELECT COALESCE(
                            SUM(julianday(b.end_time) - julianday(b.start_time)),
                            0
                        )
                    FROM breaks b
                    WHERE b.start_time >= s.startedAt
                        AND b.end_time <= s.stoppedAt
                )
            ) * 24
        )
        ELSE 0
    END as score_per_hour
FROM score s
    LEFT JOIN player pl ON s.player_id = pl.id;
-- Indexes
CREATE INDEX IF NOT EXISTS idx_selected_player_player_id_date ON selected_player(player_id, date);
CREATE INDEX IF NOT EXISTS idx_selected_player_button_id_date ON selected_player(button_id, date);
CREATE INDEX IF NOT EXISTS idx_presses_player_id_timestamp ON presses(player_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_breaks_start_end ON breaks(start_time, end_time);