import locale
import sqlite3
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from sqlite3 import Connection

import keyboard
import schedule
from pydantic import BaseModel
from PyQt5.QtCore import QObject, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QIcon, QPalette, QPixmap, QResizeEvent
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

COUNT_FILE = "counters.json"
BG_IMAGE_FILE = "bg_white.png"
BUTTON_TIMEOUT_SECONDS = 3

debug_mode = True  # Set to False to hide mock controls


class UpdateSignal(QObject):
    update_ui_signal = pyqtSignal()


update_signal = UpdateSignal()


class HotkeySignal(QObject):
    # This signal will be emitted when a hotkey is pressed
    hotkey_pressed = pyqtSignal(object)  # The signal carries a callable object


try:
    with open("mock_hours.txt") as file:
        mock_hours_increment = int(file.read())
except (FileNotFoundError, ValueError):
    mock_hours_increment = 0


class VedApp(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.hotkey_signal = HotkeySignal()
        self.initUI()
        update_signal.update_ui_signal.connect(self.update_ui)
        self.hotkey_signal.hotkey_pressed.connect(self.execute_function)
        self.setup_scheduler()

    def initUI(self) -> None:
        main_layout = QHBoxLayout(self)

        # Vertical layout for mock_date_controls and leaderboard
        left_column_layout = QVBoxLayout()

        if debug_mode:
            self.mock_date_controls = MockDateControls()
            left_column_layout.addWidget(self.mock_date_controls)

        self.leaderboard = LeaderboardWidget()
        left_column_layout.addWidget(self.leaderboard)

        # Layout for player boxes
        self.player_boxes: list[PlayerBox] = []
        player_boxes_layout = QHBoxLayout()
        for i in range(0, 6, 2):  # Creating pairs
            pair_layout = QVBoxLayout()

            for j in range(2):  # Two player boxes per pair
                player_box = PlayerBox(i + j + 1, self.hotkey_signal)
                pair_layout.addWidget(player_box)
                self.player_boxes.append(player_box)

            player_boxes_layout.addLayout(pair_layout)

        # Set background image
        palette = QPalette()
        pixmap = QPixmap(BG_IMAGE_FILE).scaled(
            self.width(), self.height(), Qt.AspectRatioMode.IgnoreAspectRatio
        )
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)

        # Add the left column and player boxes layout to the main layout
        main_layout.addLayout(left_column_layout, 1)
        main_layout.addLayout(player_boxes_layout, 2)

        self.setLayout(main_layout)
        self.update_ui()

    def resizeEvent(self, _event: QResizeEvent) -> None:
        palette = QPalette()
        pixmap = QPixmap(BG_IMAGE_FILE).scaled(
            self.width(), self.height(), Qt.AspectRatioMode.IgnoreAspectRatio
        )
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)

    def setup_scheduler(self) -> None:
        schedule.every().minute.do(self.scheduled_update_ui)

        # Run the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()

    def update_ui(self) -> None:
        for player_box in self.player_boxes:
            player_box.update_ui()
        self.leaderboard.update_ui()

    def scheduled_update_ui(self) -> None:
        print("Scheduled update")
        update_signal.update_ui_signal.emit()

    def run_scheduler(self) -> None:
        while True:
            schedule.run_pending()
            time.sleep(1)

    def execute_function(self, func: Callable[[], None]) -> None:
        func()


class LeaderboardWidget(QScrollArea):
    def __init__(self) -> None:
        super().__init__()
        self.setWidgetResizable(True)
        self.initUI()

    def initUI(self) -> None:
        self.table = QTableWidget()
        self.setWidget(self.table)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Dato", "Navn", "Sekker", "Fart"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    def update_ui(self) -> None:
        # Clear the current table content
        self.table.setRowCount(0)

        # Add updated data
        leaderboard = global_repo.get_leaderboard()
        for entry in leaderboard:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            self.table.setItem(row_position, 0, QTableWidgetItem(entry[0]))
            self.table.setItem(row_position, 1, QTableWidgetItem(entry[1]))
            self.table.setItem(row_position, 2, QTableWidgetItem(str(entry[2])))
            self.table.setItem(row_position, 3, QTableWidgetItem(f"{entry[3]:.2f} s"))


class PlayerBox(QGroupBox):
    def __init__(self, button_id: int, hotkey_signal: HotkeySignal) -> None:
        super().__init__()
        self.button_id = button_id
        self.hotkey_signal = hotkey_signal

        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.timer.setInterval(BUTTON_TIMEOUT_SECONDS * 1000)

        # Add keyboard hotkeys for f1 through f6
        keyboard.add_hotkey(f"f{button_id}", self.on_hotkey_pressed)

        self.initUI()

    def initUI(self) -> None:
        self.main_layout = QVBoxLayout()

        topbar = QHBoxLayout()

        self.player_select_combo = QComboBox()
        self.player_select_combo.setEditable(True)
        self.player_select_combo.setInsertPolicy(QComboBox.NoInsert)
        self.player_select_combo.completer().setCompletionMode(
            QCompleter.CompletionMode.PopupCompletion
        )
        self.player_select_combo.currentIndexChanged.connect(self.on_player_changed)

        topbar.addWidget(self.player_select_combo)

        self.edit_player_button = QPushButton()
        self.edit_player_button.setIcon(
            QIcon("cog_icon.svg")
        )  # Replace with path to your cog icon
        self.edit_player_button.setIconSize(QSize(16, 16))  # Adjust icon size as needed

        self.edit_player_button.clicked.connect(self.on_edit_player_clicked)
        topbar.addWidget(self.edit_player_button)

        topbar.setStretch(0, 1)  # Give more space to the combo box
        topbar.setStretch(1, 0)  # Less space for the button

        self.main_layout.addLayout(topbar)

        # Information display area
        self.info_label = QLabel("Select player")
        self.main_layout.addWidget(
            self.info_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Plus button next to combo box
        self.add_player_button = QPushButton("New player")
        self.add_player_button.clicked.connect(self.on_add_player)
        # Logic to enable/disable button based on combo box state
        self.main_layout.addWidget(self.add_player_button)

        # Score and speed display
        self.score_label = QLabel()
        self.score_label.setStyleSheet("font-size: 80px;")
        self.main_layout.addWidget(
            self.score_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.speed_label = QLabel()
        self.main_layout.addWidget(
            self.speed_label, alignment=Qt.AlignmentFlag.AlignCenter
        )

        self.setLayout(self.main_layout)

    def update_ui(self) -> None:
        players = global_repo.get_combobox_players(self.button_id)

        self.player_select_combo.currentIndexChanged.disconnect(self.on_player_changed)
        self.player_select_combo.clear()

        for player in players:
            self.player_select_combo.addItem(player.player_name, player.player_id)

        score_entry = global_repo.get_score_entry(self.button_id)

        if score_entry:
            player_id = score_entry.player_id
            player_index = self.find_combobox_player_index_by_id(player_id)
            self.player_select_combo.setCurrentIndex(player_index)
            self.edit_player_button.show()
            # Check if score is zero for today
            if score_entry.score == 0:
                # Determine if the player is new or existing
                is_new_player = self.check_if_new_player(score_entry.player_id)
                if is_new_player:
                    # New player, no score today
                    self.info_label.setText(f"Press button to start.")
                    self.score_label.setText("")
                    self.add_player_button.hide()
                    self.player_select_combo.setEnabled(True)
                else:
                    # Existing player, no score today
                    self.info_label.setText(f"Press button to start.")
                    self.score_label.setText("")
                    self.add_player_button.show()
                    self.player_select_combo.setEnabled(True)

            else:
                # Player with score today
                self.info_label.setText("")
                self.score_label.setText(f"{score_entry.score}")
                self.speed_label.setText(
                    f"Speed: {score_entry.speed:.2f} sekunder per sekk"
                )
                self.add_player_button.hide()
                self.player_select_combo.setEnabled(False)

        else:
            self.info_label.setText("Select player")
            self.score_label.setText("")
            self.speed_label.setText("")
            self.player_select_combo.setCurrentIndex(-1)  # Reset selection
            self.player_select_combo.show()
            self.add_player_button.show()
            self.edit_player_button.hide()
            self.player_select_combo.setEnabled(True)

        self.player_select_combo.currentIndexChanged.connect(self.on_player_changed)

    def find_combobox_player_index_by_id(self, player_id: int) -> int:
        for index in range(self.player_select_combo.count()):
            if self.player_select_combo.itemData(index) == player_id:
                return index
        return -1  # Return -1 if player_id not found

    def check_if_new_player(self, player_id: int) -> bool:
        # Get the current date

        # Query the database to check for scores before today
        has_previous_scores = global_repo.check_player_scores_before_date(player_id)

        # If the player has no scores before today, they are new
        return not has_previous_scores

    def on_player_changed(self, index: int) -> None:
        selected_player_id = self.player_select_combo.itemData(index)

        if selected_player_id:
            # Update the score entry with the new player id
            global_repo.update_score_entry_player(self.button_id, selected_player_id)

        vedApp.update_ui()

    def on_hotkey_pressed(self) -> None:
        self.hotkey_signal.hotkey_pressed.emit(self.press_button)

    def press_button(self) -> None:
        selected_player_id = global_repo.get_player_score_data(self.button_id)

        if selected_player_id and not self.timer.isActive():
            global_repo.increment_score(self.button_id)
            # Change to a darker color
            self.setStyleSheet("background-color: darkgrey;")

            self.timer.start()
            vedApp.update_ui()
        else:
            print("Ignoring button press because no player selected or timer is active")

    def timeout(self) -> None:
        self.timer.stop()
        self.setStyleSheet("")  # Reset to the original style
        vedApp.update_ui()

    def on_add_player(self) -> None:
        player_name = self.player_select_combo.currentText().strip()
        global_repo.create_player_and_upsert_score(player_name, self.button_id)
        vedApp.update_ui()

    def on_edit_player_clicked(self) -> None:
        selected_player_id = self.player_select_combo.itemData(
            self.player_select_combo.currentIndex()
        )

        if selected_player_id is None:
            raise Exception("No player selected for editing")
            # Logic to edit the player with the selected ID
            # This might involve opening a new dialog/window where you can edit player details
        edit_dialog = EditPlayerDialog(selected_player_id, self)
        edit_dialog.exec_()  # Assuming EditPlayerDialog is a QDialog or similar


class EditPlayerDialog(QDialog):
    def __init__(self, player_id: int, parent: QGroupBox) -> None:
        super().__init__(parent)
        self.player_id = player_id

        self.initUI()
        self.updateUI()

    def initUI(self) -> None:
        self.main_layout = QVBoxLayout(self)

        self.name_edit = QLineEdit()
        self.main_layout.addWidget(self.name_edit)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(
            QIcon("delete_icon.svg")
        )  # Set path to your delete icon
        self.delete_button.clicked.connect(self.onDeleteClicked)
        self.main_layout.addWidget(self.delete_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.onOkClicked)
        self.main_layout.addWidget(self.ok_button)

    def updateUI(self) -> None:
        # Load the player's current name from the database using global_repo
        current_name = global_repo.get_player_name_by_id(self.player_id)

        if current_name is None:
            raise Exception(f"Player ID {self.player_id} not found in the database.")

        self.name_edit.setText(current_name)

        if global_repo.can_player_be_deleted(self.player_id):
            self.delete_button.show()
        else:
            self.delete_button.hide()

    def onDeleteClicked(self) -> None:
        # Confirm deletion
        global_repo.delete_player(self.player_id)
        self.accept()  # Close the dialog
        vedApp.update_ui()  # Update the main application UI

    def onOkClicked(self) -> None:
        new_name = self.name_edit.text().strip()
        try:
            global_repo.update_name(self.player_id, new_name)
            self.accept()  # Close the dialog
            vedApp.update_ui()  # Update the main application UI
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(
                self, "Error", new_name + " er allerede i bruk.", QMessageBox.Ok
            )


class MockDateControls(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.initUI()

    def initUI(self) -> None:
        self.main_layout = QHBoxLayout(self)

        self.mock_time_label = QLabel()
        self.main_layout.addWidget(self.mock_time_label)

        self.increment_hour_button = QPushButton("+")
        self.increment_hour_button.clicked.connect(self.increment_mock_hour)
        self.main_layout.addWidget(self.increment_hour_button)
        self.increment_hour_button.setFixedSize(25, 25)

        self.update_ui()

    def update_ui(self) -> None:
        formatted_time = getNow().strftime("%Y-%m-%d %H:%M")
        self.mock_time_label.setText("Mocked Time: " + formatted_time)

    def increment_mock_hour(self) -> None:
        global mock_hours_increment
        mock_hours_increment += 1
        self.save_mock_hours()
        self.update_ui()

    def save_mock_hours(self) -> None:
        with open("mock_hours.txt", "w") as file:
            file.write(str(mock_hours_increment))


def getNow() -> datetime:
    """Returns the current date and time with hours incremented by mock_hours_increment."""
    return datetime.now() + timedelta(hours=mock_hours_increment)


def getToday() -> str:
    """Returns the current date."""
    return getNow().strftime("%Y-%m-%d")


class ComboBoxPlayer(BaseModel):
    player_id: int
    player_name: str


class ScoreEntry(BaseModel):
    player_id: int
    player_name: str
    score: int
    startedAt: (str) | None
    stoppedAt: str | None
    speed: float


class ScoreRepository:
    def __init__(self) -> None:
        self.db_path = "highscores.db"

    def _get_connection(self) -> Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")  # Enable foreign key constraints
        return conn

    def update_name(self, player_id: int, new_name: str) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE player SET name=? WHERE id=?", (new_name, player_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_player_score_data(
        self, button_id: int
    ) -> tuple[str, int, str, str, float] | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT p.name,
                    ds.score,
                    ds.startedAt,
                    ds.stoppedAt,
                    ds.speed
                FROM daily_scores ds
                LEFT JOIN player p ON ds.player_id = p.id
                WHERE ds.date = ? AND ds.button_id = ?
                """,
                (getToday(), button_id),
            )
            result = cursor.fetchone()
            if result and len(result) == 5:
                name, score, startedAt, stoppedAt, speed = result
                return (name, int(score), startedAt, stoppedAt, float(speed))
            return None
        finally:
            cursor.close()
            conn.close()

    def get_leaderboard(self) -> list[tuple[str, str, int, float]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT strftime('%w %d.%m', ds.date) as formatted_date,
                    p.name,
                    ds.score,
                    ds.speed
                FROM daily_scores ds
                JOIN player p ON ds.player_id = p.id
                ORDER BY ds.score DESC, ds.speed ASC;
            """
            )
            # formatted_date:str, name:str, score:int, speed:float
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def increment_score(self, button_id: int) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            date = getToday()

            # Convert current_time to a string format suitable for your database

            # Check if there's a score entry for today and the given button
            cursor.execute(
                """
                SELECT presses FROM score 
                WHERE button_id = ? AND date = ?
                """,
                (button_id, date),
            )

            result = cursor.fetchone()
            if result:
                # Score exists, increment it and update stoppedAt
                new_score = result[0] + 1
                cursor.execute(
                    """
                    UPDATE score SET presses = ?, stoppedAt = ?
                    WHERE button_id = ? AND date = ?
                    """,
                    (new_score, getNow(), button_id, date),
                )
            else:
                # No score for today, insert a new record with score of 1 and current stoppedAt
                cursor.execute(
                    """
                    INSERT INTO score (button_id, date, presses, stoppedAt)
                    VALUES (?, ?, 1, ?)
                    """,
                    (button_id, date, getNow()),
                )

            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def create_player_and_upsert_score(self, player_name: str, button_id: int) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Step 1: Insert new player
            cursor.execute("INSERT INTO player (name) VALUES (?)", (player_name,))
            new_player_id = cursor.lastrowid

            # Get current date and time
            today_str = getToday()
            now = getNow()

            # Step 2: Upsert into score
            cursor.execute(
                """
                INSERT INTO score (player_id, button_id, date, presses, startedAt, stoppedAt)
                VALUES (?, ?, ?, 0, ?, ?)
                ON CONFLICT(button_id, date) DO UPDATE SET 
                    player_id = excluded.player_id,
                    startedAt = ?
                """,
                (new_player_id, button_id, today_str, now, now, now),
            )

            conn.commit()
        except Exception as e:
            # Handle exceptions if needed
            print("Error:", e)
        finally:
            cursor.close()
            conn.close()

    def get_combobox_players(self, button_id: int) -> list[ComboBoxPlayer]:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            today = getToday()
            cursor.execute(
                """
                SELECT p.id, p.name 
                FROM player p
                LEFT JOIN score s ON p.id = s.player_id AND s.date = ?
                WHERE s.id IS NULL OR (s.button_id = ? AND s.date = ?)
                """,
                (today, button_id, today),
            )
            players = cursor.fetchall()
            return [
                ComboBoxPlayer(player_id=id, player_name=name) for id, name in players
            ]
        finally:
            cursor.close()
            conn.close()

    def update_score_entry_player(self, button_id: int, new_player_id: int) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Get current date and time
            today_str = getToday()
            now = getNow()

            cursor.execute(
                """
                INSERT INTO score (button_id, player_id, date, presses, startedAt, stoppedAt)
                VALUES (?, ?, ?, 0, ?, ?)
                ON CONFLICT(button_id, date) DO UPDATE SET 
                    player_id = excluded.player_id,
                    startedAt = ?
                """,
                (button_id, new_player_id, today_str, now, now, now),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_score_entry(self, button_id: int) -> ScoreEntry | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT ds.player_id, ds.player_name, ds.score, ds.startedAt, 
                    ds.stoppedAt, ds.speed
                FROM daily_scores ds
                WHERE ds.button_id = ? AND ds.date = ?
                """,
                (button_id, getToday()),
            )
            entry = cursor.fetchone()
            if entry:
                return ScoreEntry(
                    player_id=entry[0],
                    player_name=entry[1],
                    score=entry[2],
                    startedAt=entry[3],
                    stoppedAt=entry[4],
                    speed=entry[5],
                )
            else:
                return None
        finally:
            cursor.close()
            conn.close()

    def check_player_scores_before_date(self, player_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM score WHERE player_id = ? AND date < ?",
                (player_id, getToday()),
            )
            result = cursor.fetchone()

            if result is None:
                return False
            if not isinstance(result, tuple):
                raise TypeError("Unexpected result type from the database query.")

            count = result[0]
            if not isinstance(count, int):
                raise ValueError("Expected an integer count from the database")

            return count > 0
        except Exception as e:
            print("Error checking player's previous scores:", e)
            return False
        finally:
            cursor.close()
            conn.close()

    def get_player_name_by_id(self, player_id: int) -> str | None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM player WHERE id = ?", (player_id,))
            result = cursor.fetchone()
            if result is None:
                return None
            if not isinstance(result, tuple):
                raise TypeError("Unexpected result type from the database query.")

            return result[0] if result else None
        finally:
            cursor.close()
            conn.close()

    def can_player_be_deleted(self, player_id: int) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM score WHERE player_id = ? AND presses > 0)",
                (player_id,),
            )
            result = cursor.fetchone()

            if result is None:
                raise ValueError(f"No result returned for player ID {player_id}")

            if (
                not isinstance(result, tuple)
                or not len(result) == 1
                or not isinstance(result[0], int)
            ):
                raise TypeError(f"Unexpected result type: {result}")

            can_delete = result[0] == 0
            return can_delete
        finally:
            cursor.close()
            conn.close()

    def delete_player(self, player_id: int) -> None:
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM player WHERE id = ?", (player_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


global_repo = ScoreRepository()
app = QApplication(sys.argv)
vedApp = VedApp()


def bootstrap() -> None:
    locale.setlocale(locale.LC_ALL, "nb_NO.UTF-8")  # Norwegian Bokmål locale
    global vedApp
    vedApp.show()
    sys.exit(app.exec_())


bootstrap()
