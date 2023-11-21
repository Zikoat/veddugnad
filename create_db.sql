CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    team TEXT CHECK(team IN ('Red', 'Orange', 'Green', 'Blue')),
    CHECK (name <> '')
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    button_id INTEGER NOT NULL,
    date DATE NOT NULL,
    presses INTEGER DEFAULT 0 NOT NULL,
    startedAt DATETIME,
    stoppedAt DATETIME,
    FOREIGN KEY (player_id) REFERENCES player(id) ON DELETE CASCADE,
    FOREIGN KEY (button_id) REFERENCES button(button_id),
    UNIQUE (button_id, date),
    UNIQUE (player_id, date)
);
CREATE TABLE IF NOT EXISTS breaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL
);
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
        AND julianday(s.stoppedAt) - julianday(s.startedAt) > 0 THEN s.presses / (
            (
                (
                    (julianday(s.stoppedAt) - julianday(s.startedAt))
                ) - (
                    SELECT COALESCE(
                            SUM(
                                julianday(b.end_time) - julianday(b.start_time)
                            ),
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
    LEFT JOIN player pl ON s.player_id = pl.id
GROUP BY pl.name,
    s.date,
    s.button_id;
    
CREATE INDEX IF NOT EXISTS idx_score_button_id_date ON score(button_id, date);
CREATE INDEX IF NOT EXISTS idx_score_player_id_date ON score(player_id, date);
CREATE INDEX IF NOT EXISTS idx_score_presses ON score(presses);
CREATE INDEX IF NOT EXISTS idx_breaks_start_end ON breaks(start_time, end_time);