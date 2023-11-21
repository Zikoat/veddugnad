import locale
import sqlite3
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from sqlite3 import Connection, Cursor

import keyboard
import schedule
from pydantic import BaseModel
from PyQt5.QtCore import QObject, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QCloseEvent, QIcon, QPalette, QPixmap, QResizeEvent
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class UpdateSignal(QObject):
    update_ui_signal = pyqtSignal()


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
        self.break_button = QPushButton("Pause")
        self.break_button.setStyleSheet("font-size: 16pt;")  # Increase font size

        self.break_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.break_button.clicked.connect(self.onBreakButtonClicked)

        left_column_layout.addStretch()  # Add stretch above the button
        left_column_layout.addWidget(
            self.break_button, 0, Qt.AlignmentFlag.AlignHCenter
        )  # Align horizontally center
        left_column_layout.addStretch()  # Add stretch below the button

        self.leaderboard = LeaderboardWidget()
        left_column_layout.addWidget(self.leaderboard, 1)

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
        update_signal.update_ui_signal.emit()

    def run_scheduler(self) -> None:
        while True:
            schedule.run_pending()
            time.sleep(1)

    def execute_function(self, func: Callable[[], None]) -> None:
        func()

    def onBreakButtonClicked(self) -> None:
        self.break_dialog = BreakDialog(self)
        self.update_ui()
        self.break_dialog.exec_()


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
            date = datetime.strptime(entry[0], "%Y-%m-%d").strftime("%a %d.%m.%Y")
            date_item = QTableWidgetItem(date)
            date_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            sekker = QTableWidgetItem(str(entry[2]))
            sekker.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_position, 0, date_item)
            self.table.setItem(row_position, 1, QTableWidgetItem(entry[1]))
            self.table.setItem(row_position, 2, sekker)
            self.table.setItem(row_position, 3, QTableWidgetItem(f"{entry[3]:.2f} s/t"))


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
        self.player_select_combo.setEditable(False)
        self.player_select_combo.setStyleSheet("QComboBox { font-size: 16pt;  }")
        self.player_select_combo.currentIndexChanged.connect(self.on_player_changed)

        topbar.addWidget(self.player_select_combo)

        self.edit_player_button = QPushButton()
        self.edit_player_button.setIcon(
            QIcon("cog_icon.svg")
        )  # Replace with path to your cog icon
        self.edit_player_button.setIconSize(QSize(25, 25))  # Adjust icon size as needed

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
        self.add_player_button.clicked.connect(self.open_new_player_dialog)
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
        self.speed_label.setStyleSheet("font-size: 13pt;")

        self.setLayout(self.main_layout)

    def open_new_player_dialog(self) -> None:
        dialog = NewPlayerDialog(self.button_id, self)
        dialog.exec_()  # Show the dialog

    def update_ui(self) -> None:
        players = global_repo.get_combobox_players(self.button_id)

        self.player_select_combo.currentIndexChanged.disconnect(self.on_player_changed)
        self.player_select_combo.clear()

        for player in players:
            self.player_select_combo.addItem(player.player_name, player.player_id)

        score_entry = global_repo.get_score_entry(self.button_id)
        self.setStyleSheet("")

        if score_entry:
            player_id = score_entry.player_id
            player_index = self.find_combobox_player_index_by_id(player_id)
            self.player_select_combo.setCurrentIndex(player_index)
            self.edit_player_button.show()
            # Check if score is zero for today
            if score_entry.score == 0:
                # Determine if the player is new or existing
                is_new_player = self.check_if_new_player(score_entry.player_id)
                self.speed_label.setText("")
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
                if score_entry.score_per_hour < 0.01:
                    self.speed_label.setText("")
                else:
                    self.speed_label.setText(
                        f"Fart: {score_entry.score_per_hour:.2f} sekker i timen"
                    )
                self.add_player_button.hide()
                self.player_select_combo.setEnabled(False)
            if not self.can_press_button():
                self.setStyleSheet("background-color: darkgrey;")
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
        if self.can_press_button():
            global_repo.increment_score(self.button_id)
            self.timer.start()
        else:
            print("Ignoring button press because no player selected or timer is active")
        vedApp.update_ui()

    def can_press_button(self) -> bool:
        selected_player_id = global_repo.get_score_entry(self.button_id)
        global is_break
        if selected_player_id and not self.timer.isActive() and not is_break:
            return True
        else:
            return False

    def timeout(self) -> None:
        self.timer.stop()
        self.setStyleSheet("")  # Reset to the original style
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
        # QApplication::setAttribute(Qt::AA_DisableWindowContextHelpButton);
        # self.setWindowFlags(self.windowFlags().setFlag(Qt.WindowContextHelpButtonHint, false))
        main_layout = QVBoxLayout(self)

        self.name_edit = QLineEdit()
        main_layout.addWidget(self.name_edit)

        self.team_selector = HelmetSelectionWidget()
        main_layout.addWidget(self.team_selector)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(
            QIcon("delete_icon.svg")
        )  # Set path to your delete icon
        self.delete_button.clicked.connect(self.onDeleteClicked)
        main_layout.addWidget(self.delete_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.onOkClicked)
        main_layout.addWidget(self.ok_button)

        self.updateUI()

    def updateUI(self) -> None:
        # Load the player's current name from the database using global_repo
        player = global_repo.get_player_by_id(self.player_id)

        if player is None:
            raise Exception(f"Player ID {self.player_id} not found in the database.")

        self.name_edit.setText(player.name)

        team_combobox = self.team_selector.helmetComboBox
        team_index = team_combobox.findText(player.team, Qt.MatchFlag.MatchFixedString)

        if team_index >= 0:  # Check if the team was found in the combobox
            team_combobox.setCurrentIndex(team_index)

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
        team = self.team_selector.helmetComboBox.currentText()

        try:
            global_repo.update_user(self.player_id, new_name, team)
            self.accept()  # Close the dialog
            vedApp.update_ui()  # Update the main application UI
        except sqlite3.IntegrityError as e:
            QMessageBox.critical(
                self,
                "Error",
                'Kunne ikke sette navnet til "'
                + new_name
                + '"\nSjekk at navnet ikke er tomt, og ikke er i bruk.\n\nError: '
                + str(e),
                QMessageBox.Ok,
            )


class NewPlayerDialog(QDialog):
    def __init__(self, button_id: int, parent: QGroupBox) -> None:
        super().__init__(parent)
        self.button_id = button_id
        layout = QVBoxLayout(self)

        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)

        ok_button = QPushButton("Lagre")
        ok_button.clicked.connect(self.on_ok_clicked)

        self.team_selector = HelmetSelectionWidget()
        layout.addWidget(self.team_selector)

        layout.addWidget(ok_button)

    def on_ok_clicked(self) -> None:
        player_name = self.name_edit.text().strip()
        team = self.team_selector.helmetComboBox.currentText()
        try:
            global_repo.create_player_and_upsert_score(
                player_name, self.button_id, team
            )
            vedApp.update_ui()
            self.accept()  # Close the dialog
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                "Kunne ikke lage ny spiller. \nSjekk at navnet ikke er tomt, og ikke er i bruk.\n\nError: "
                + str(e),
                QMessageBox.StandardButton.Ok,
            )


class HelmetSelectionWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.initUI()

    def initUI(self) -> None:
        layout = QVBoxLayout(self)

        self.helmetComboBox = QComboBox()

        # Add items with icons
        self.helmetComboBox.addItem(QIcon("orange-helmet.png"), "Orange")
        self.helmetComboBox.addItem(QIcon("green-helmet.png"), "Green")
        self.helmetComboBox.addItem(QIcon("red-helmet.png"), "Red")
        self.helmetComboBox.addItem(QIcon("blue-helmet.png"), "Blue")

        layout.addWidget(self.helmetComboBox)
        self.setLayout(layout)


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


class BreakDialog(QDialog):
    def __init__(self, parent: QGroupBox) -> None:
        super().__init__(parent)
        global is_break
        is_break = True
        self.break_start_time = getNow()
        layout = QVBoxLayout(self)

        pause_label = QLabel("Pause")
        pause_label.setStyleSheet("font-size: 24pt;")  # Large text
        layout.addWidget(pause_label)

        info_label = QLabel("No more working now")
        layout.addWidget(info_label)

        continue_button = QPushButton("Continue")
        continue_button.clicked.connect(self.onContinue)
        layout.addWidget(continue_button)

        self.setLayout(layout)

    def onContinue(self) -> None:
        end_break(self.break_start_time, getNow())
        self.accept()
        vedApp.update_ui()

    def closeEvent(self, _event: QCloseEvent) -> None:
        # Ensure break continues even if the dialog is closed without clicking "Continue"
        self.onContinue()
        super().closeEvent(_event)


def end_break(start_time: datetime, end_time: datetime) -> None:
    global is_break
    is_break = False
    global_repo.insert_new_break(start_time, end_time)


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
    score_per_hour: float


class Player(BaseModel):
    id: int
    name: str
    team: str


import sqlite3


class DatabaseContext:
    def __init__(self) -> None:
        self.conn: Connection | None = None
        self.cursor: Cursor | None = None

    def __enter__(self) -> Cursor:
        self.conn = sqlite3.connect("highscores.db")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type: None, exc_value: None, traceback: None) -> None:
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.commit()
            self.conn.close()


class ScoreRepository:
    def update_user(self, player_id: int, new_name: str, team: str) -> None:
        with DatabaseContext() as cursor:
            cursor.execute(
                "UPDATE player SET name=?, team=? WHERE id=?",
                (new_name, team, player_id),
            )

    def get_leaderboard(self) -> list[tuple[str, str, int, float]]:
        with DatabaseContext() as cursor:
            cursor.execute(
                """
                SELECT ds.date as formatted_date,
                    p.name,
                    ds.score,
                    ds.score_per_hour
                FROM daily_scores ds
                JOIN player p ON ds.player_id = p.id
                WHERE ds.score > 0
                ORDER BY ds.score DESC, ds.score_per_hour ASC;
                """
            )
            # formatted_date:str, name:str, score:int, score_per_hour:float
            return cursor.fetchall()

    def increment_score(self, button_id: int) -> None:
        with DatabaseContext() as cursor:
            date = getToday()
            now_str = getNow().strftime("%Y-%m-%d %H:%M:%S.%f")

            # Update score entry with conditional logic in SQL
            cursor.execute(
                """
                UPDATE score
                SET 
                    presses = presses + 1,
                    startedAt = CASE WHEN presses = 0 THEN ? ELSE startedAt END,
                    stoppedAt = ?
                WHERE button_id = ? AND date = ?
                """,
                (now_str, now_str, button_id, date),
            )

    def create_player_and_upsert_score(
        self, player_name: str, button_id: int, team: str
    ) -> None:
        with DatabaseContext() as cursor:
            # Step 1: Insert new player
            cursor.execute(
                "INSERT INTO player (name, team) VALUES (?, ?)", (player_name, team)
            )
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

    def get_combobox_players(self, button_id: int) -> list[ComboBoxPlayer]:
        with DatabaseContext() as cursor:
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

    def update_score_entry_player(self, button_id: int, new_player_id: int) -> None:
        with DatabaseContext() as cursor:
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

    def get_score_entry(self, button_id: int) -> ScoreEntry | None:
        with DatabaseContext() as cursor:
            cursor.execute(
                """
                SELECT ds.player_id, ds.player_name, ds.score, ds.startedAt, 
                    ds.stoppedAt, ds.score_per_hour
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
                    score_per_hour=entry[5],
                )
            else:
                return None

    def check_player_scores_before_date(self, player_id: int) -> bool:
        with DatabaseContext() as cursor:
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

    def get_player_by_id(self, player_id: int) -> Player | None:
        with DatabaseContext() as cursor:
            cursor.execute(
                "SELECT id, name, team FROM player WHERE id = ?", (player_id,)
            )
            result = cursor.fetchone()

            return (
                Player(
                    id=result[0],
                    name=result[1],
                    team=result[2],
                )
                if result
                else None
            )

    def can_player_be_deleted(self, player_id: int) -> bool:
        with DatabaseContext() as cursor:
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

    def delete_player(self, player_id: int) -> None:
        with DatabaseContext() as cursor:
            cursor.execute("DELETE FROM player WHERE id = ?", (player_id,))

    def insert_new_break(self, start_time: datetime, end_time: datetime) -> None:
        with DatabaseContext() as cursor:
            cursor.execute(
                "INSERT INTO breaks (start_time, end_time) VALUES (?, ?)",
                (start_time, end_time),
            )


COUNT_FILE = "counters.json"
BG_IMAGE_FILE = "bg_white.png"
BUTTON_TIMEOUT_SECONDS = 3

update_signal = UpdateSignal()

debug_mode = True  # Set to False to hide mock controls


is_break = False

locale.setlocale(locale.LC_ALL, "nb_NO.UTF-8")  # Norwegian Bokmål locale

global_repo = ScoreRepository()

QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableWindowContextHelpButton)
app = QApplication(sys.argv)
global vedApp
vedApp = VedApp()
vedApp.show()
sys.exit(app.exec_())
