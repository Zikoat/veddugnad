from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QTimer, pyqtSignal, QObject, Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QGroupBox, QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QScrollArea, QGroupBox, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,QStyle
from PyQt5.QtGui import QPalette, QBrush, QPixmap,QIcon
from PyQt5.QtCore import QSize
from datetime import datetime
import sys
import keyboard
import locale
import sqlite3
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout,
                             QPushButton, QComboBox, QCompleter)
from PyQt5.QtCore import QTimer
import keyboard
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox

# File paths
COUNT_FILE = 'counters.json'
BG_IMAGE_FILE = 'bg_white.png'
BUTTON_TIMEOUT_SECONDS = 3


class UpdateSignal(QObject):
    update_ui_signal = pyqtSignal()


update_signal = UpdateSignal()
debug_mode = True  # Set to False to hide mock controls


class VedApp(QWidget):
    def __init__(self):
        super().__init__()
        self.load_mock_hours()
        self.hotkey_signal = HotkeySignal()
        self.initUI()
        update_signal.update_ui_signal.connect(self.update_ui)

        self.hotkey_signal.hotkey_pressed.connect(self.execute_function)

    def initUI(self):
        main_layout = QHBoxLayout()

        # Adding leaderboard
        self.leaderboard = LeaderboardWidget()
        main_layout.addWidget(self.leaderboard, 1)

        # Create an attribute to hold player boxes
        self.player_boxes = []

        player_boxes_layout = QHBoxLayout()
        for i in range(0, 6, 2):  # Creating pairs
            pair_layout = QVBoxLayout()

            for j in range(2):  # Two player boxes per pair
                player_box = PlayerBox(str(i + j + 1), self.hotkey_signal)
                pair_layout.addWidget(player_box)
                # Add player box to the list
                self.player_boxes.append(player_box)

            player_boxes_layout.addLayout(pair_layout)

        main_layout.addLayout(player_boxes_layout, 2)
        # Set background image
        palette = QPalette()
        pixmap = QPixmap(BG_IMAGE_FILE).scaled(
            self.width(), self.height(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)

        self.setLayout(main_layout)

        if debug_mode:
            self.mock_date_controls = MockDateControls()
            main_layout.addWidget(self.mock_date_controls)

        self.update_ui()

    def resizeEvent(self, event):
        # Update the background image to fit the new size of the window
        palette = QPalette()
        pixmap = QPixmap(BG_IMAGE_FILE).scaled(
            self.width(), self.height(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)

    def update_ui(self):
        for player_box in self.player_boxes:
            player_box.update_ui()
        self.leaderboard.update_ui()

    def execute_function(self, func):
        func()

    def load_mock_hours(self):
        global mock_hours_increment
        try:
            with open('mock_hours.txt', 'r') as file:
                mock_hours_increment = int(file.read())
        except (FileNotFoundError, ValueError):
            mock_hours_increment = 0


# Leaderboard widget


class LeaderboardWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.initUI()

    def initUI(self):
        self.table = QTableWidget()
        self.setWidget(self.table)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Dato", "Navn", "Sekker", "Fart"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

    def update_ui(self):
        # Clear the current table content
        self.table.setRowCount(0)

        # Add updated data
        leaderboard = create_leaderboard()
        for entry in leaderboard:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            self.table.setItem(row_position, 0, QTableWidgetItem(entry[0]))
            self.table.setItem(row_position, 1, QTableWidgetItem(entry[1]))
            self.table.setItem(
                row_position, 2, QTableWidgetItem(str(entry[2])))
            self.table.setItem(
                row_position, 3, QTableWidgetItem(f"{entry[3]:.2f} s"))


class HotkeySignal(QObject):
    # This signal will be emitted when a hotkey is pressed
    hotkey_pressed = pyqtSignal(object)  # The signal carries a callable object

# Player box widget


class PlayerBox(QGroupBox):
    def __init__(self, button_id, hotkey_signal):
        super().__init__()
        self.button_id = button_id
        self.hotkey_signal = hotkey_signal

        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.timer.setInterval(BUTTON_TIMEOUT_SECONDS * 1000)

        # Add keyboard hotkeys for f1 through f6
        keyboard.add_hotkey(f'f{button_id}', self.on_hotkey_pressed)

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        topbar = QHBoxLayout()

        self.player_select_combo = QComboBox()
        self.player_select_combo.setEditable(True)
        self.player_select_combo.setInsertPolicy(QComboBox.NoInsert)
        self.player_select_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.player_select_combo.currentIndexChanged.connect(self.on_player_changed)

        topbar.addWidget(self.player_select_combo)

        self.edit_player_button = QPushButton()
        self.edit_player_button.setIcon(QIcon("cog_icon.svg"))  # Replace with path to your cog icon
        self.edit_player_button.setIconSize(QSize(16, 16))  # Adjust icon size as needed


        self.edit_player_button.clicked.connect(self.on_edit_player_clicked)
        topbar.addWidget(self.edit_player_button)

        topbar.setStretch(0, 1)  # Give more space to the combo box
        topbar.setStretch(1, 0)  # Less space for the button

        self.layout.addLayout(topbar)

        # Information display area
        self.info_label = QLabel("Select player")
        self.layout.addWidget(self.info_label, alignment=Qt.AlignCenter)

        # Plus button next to combo box
        self.add_player_button = QPushButton("Add player")
        self.add_player_button.clicked.connect(self.on_add_player)
        # Logic to enable/disable button based on combo box state
        self.layout.addWidget(self.add_player_button)

        # Score and speed display
        self.score_label = QLabel()
        self.score_label.setStyleSheet("font-size: 80px;")
        self.layout.addWidget(self.score_label, alignment=Qt.AlignCenter)

        self.speed_label = QLabel()
        self.layout.addWidget(self.speed_label, alignment=Qt.AlignCenter)

        self.setLayout(self.layout)

    def update_ui(self):
        today = getToday()
        players = global_repo.get_combobox_players(today, self.button_id)
        
        self.player_select_combo.currentIndexChanged.disconnect(self.on_player_changed)
        self.player_select_combo.clear()

        for player_id, player_name in players:
            self.player_select_combo.addItem(player_name, player_id)

        score_entry = global_repo.get_score_entry(self.button_id, today)

        if score_entry:
            player_id = score_entry['player_id']
            player_index = self.find_combobox_player_index_by_id(player_id)
            self.player_select_combo.setCurrentIndex(player_index)
            # Check if score is zero for today
            if score_entry['score'] == 0:
                # Determine if the player is new or existing
                is_new_player = self.check_if_new_player(score_entry['player_id'])
                if is_new_player:
                    # New player, no score today
                    self.info_label.setText(
                        f"Press button to start.")
                    self.score_label.setText("")
                    self.add_player_button.hide()
                    self.player_select_combo.setEnabled(True)
                else:
                    # Existing player, no score today
                    self.info_label.setText(
                        f"Press button to start.")
                    self.score_label.setText("")
                    self.add_player_button.show()
                    self.player_select_combo.setEnabled(True)

            else:
                # Player with score today
                self.info_label.setText("")
                self.score_label.setText(
                    f"{score_entry['score']}")
                self.speed_label.setText(
                    f"Speed: {score_entry['speed']:.2f} sekunder per sekk")
                self.add_player_button.hide()
                self.player_select_combo.setEnabled(False)

        else:
            self.info_label.setText("Select player")
            self.score_label.setText("")
            self.speed_label.setText("")
            self.player_select_combo.setCurrentIndex(-1)  # Reset selection
            self.player_select_combo.show()
            
        self.player_select_combo.currentIndexChanged.connect(self.on_player_changed)

    def find_combobox_player_index_by_id(self, player_id):
        for index in range(self.player_select_combo.count()):
            if self.player_select_combo.itemData(index) == player_id:
                return index
        return -1  # Return -1 if player_id not found

    def check_if_new_player(self, player_id):
        # Get the current date
        today = getToday()

        # Query the database to check for scores before today
        has_previous_scores = global_repo.check_player_scores_before_date(
            player_id, today)

        # If the player has no scores before today, they are new
        return not has_previous_scores

    def on_player_changed(self, index):
        selected_player_id = self.player_select_combo.itemData(index)

        today = getToday()

        if selected_player_id:
            # Update the score entry with the new player id
            global_repo.update_score_entry_player(
                self.button_id, selected_player_id, today)

        vedApp.update_ui()

    def get_player_id_by_name(self, name):
        # Retrieve player ID based on name. Implementation depends on how you store player IDs.
        pass

    def on_hotkey_pressed(self):
        self.hotkey_signal.hotkey_pressed.emit(lambda: self.press_button())

    def timeout(self):
        # Handle timeout events
        pass

    def press_button(self):
        today = getToday()
        selected_player_id = global_repo.get_player_score_data(
            today, self.button_id)

        if selected_player_id and not self.timer.isActive():
            today = getToday()
            global_repo.increment_score(self.button_id, today)
            # Change to a darker color
            self.setStyleSheet("background-color: darkgrey;")

            self.timer.start()
            vedApp.update_ui()
        else:
            print("Ignoring button press because no player selected or timer is active")


    def timeout(self):
        self.timer.stop()
        self.setStyleSheet("")  # Reset to the original style
        vedApp.update_ui()

    def on_add_player(self):
        player_name = self.player_select_combo.currentText().strip()
        global_repo.create_player_and_upsert_score(
            player_name, self.button_id, getToday())
        vedApp.update_ui()

    def on_edit_player_clicked(self):
        selected_player_id = self.player_select_combo.itemData(self.player_select_combo.currentIndex())

        if selected_player_id is None:
            raise Exception("No player selected for editing")
            # Logic to edit the player with the selected ID
            # This might involve opening a new dialog/window where you can edit player details
        edit_dialog = EditPlayerDialog(selected_player_id, self)
        edit_dialog.exec_()  # Assuming EditPlayerDialog is a QDialog or similar

class EditPlayerDialog(QDialog):
    def __init__(self, player_id, vedApp, parent=None):
        super().__init__(parent)
        self.player_id = player_id
        self.vedApp = vedApp

        self.initUI()
        self.updateUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.onNameChanged)
        self.layout.addWidget(self.name_edit)

        self.delete_button = QPushButton()
        self.delete_button.setIcon(QIcon("delete_icon.svg"))  # Set path to your delete icon
        self.delete_button.clicked.connect(self.onDeleteClicked)
        self.layout.addWidget(self.delete_button)

        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.onOkClicked)
        self.layout.addWidget(self.ok_button)

    def updateUI(self):
        # Load the player's current name from the database using global_repo
        current_name = global_repo.get_player_name_by_id(self.player_id)
        self.name_edit.textChanged.disconnect(self.onNameChanged)
        self.name_edit.setText(current_name)
        self.name_edit.textChanged.connect(self.onNameChanged)
    
        if global_repo.can_player_be_deleted(self.player_id):
            self.delete_button.show()
        else:
            self.delete_button.hide()

    def onDeleteClicked(self):
        # Confirm deletion
        reply = QMessageBox.question(self, 'Confirm Delete', 'Are you sure you want to delete this player?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            global_repo.delete_player(self.player_id)
            self.accept()  # Close the dialog
            vedApp.update_ui()  # Update the main application UI

    def onNameChanged(self, new_name):
        # Update the player's name in the database on each key press
        global_repo.update_name(self.player_id, new_name)

    def onOkClicked(self):
        self.accept()  # Close the dialog
        vedApp.update_ui()  # Update the main application UI


class MockDateControls(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout(self)

        self.mock_time_label = QLabel()
        self.layout.addWidget(self.mock_time_label)

        self.increment_hour_button = QPushButton("Increment Hour")
        self.increment_hour_button.clicked.connect(self.increment_mock_hour)
        self.layout.addWidget(self.increment_hour_button)
        self.update_ui()

    def update_ui(self):
        formatted_time = getNow().strftime("%Y-%m-%d %H:%M")
        self.mock_time_label.setText("Mocked Time: " + formatted_time)

    def increment_mock_hour(self):
        global mock_hours_increment
        mock_hours_increment += 1
        self.save_mock_hours()
        self.update_ui()

    def save_mock_hours(self):
        global mock_hours_increment
        with open('mock_hours.txt', 'w') as file:
            file.write(str(mock_hours_increment))


def create_leaderboard():
    leaderboard_data = global_repo.get_leaderboard()
    leaderboard = []
    for entry in leaderboard_data:
        formatted_date, name, score, speed = entry
        leaderboard.append((formatted_date, name, score, speed))
    return leaderboard


def getNow():
    """Returns the current date and time with hours incremented by mock_hours_increment."""
    global mock_hours_increment
    return datetime.now() + timedelta(hours=mock_hours_increment)

def getToday():
    """Returns the current date."""
    return getNow().strftime('%Y-%m-%d')

class ScoreRepository:
    def __init__(self):
        self.db_path = 'highscores.db'

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def update_name(self, player_id, new_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE player SET name=? WHERE id=?", (new_name, player_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_player_score_data(self, date, button_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.name,
                    ds.score,
                    ds.startedAt,
                    ds.stoppedAt,
                    ds.speed
                FROM daily_scores ds
                LEFT JOIN player p ON ds.player_id = p.id
                WHERE ds.date = ? AND ds.button_id = ?
            """, (date, button_id))
            result = cursor.fetchone()
            return result
        finally:
            cursor.close()
            conn.close()

    def get_leaderboard(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT strftime('%w %d.%m', ds.date) as formatted_date,
                    p.name,
                    ds.score,
                    ds.speed
                FROM daily_scores ds
                JOIN player p ON ds.player_id = p.id
                ORDER BY ds.score DESC, ds.speed ASC;
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def increment_score(self, button_id, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Check if there's a score entry for today and the given button
            cursor.execute("""
                SELECT presses FROM score 
                WHERE button_id = ? AND date = ?
            """, (button_id, date))

            result = cursor.fetchone()
            if result:
                # Score exists, increment it
                new_score = result[0] + 1
                cursor.execute("""
                    UPDATE score SET presses = ?
                    WHERE button_id = ? AND date = ?
                """, (new_score, button_id, date))
            else:
                # No score for today, insert a new record with score of 1
                cursor.execute("""
                    INSERT INTO score (button_id, date, presses)
                    VALUES (?, ?, 1)
                """, (button_id, date))

            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_player_info(self, button_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            SELECT 
                p.id AS player_id,
                p.name AS player_name,
                (SELECT COUNT(*) FROM score WHERE player_id = p.id) = 0 AS is_new,
                COALESCE((SELECT SUM(presses) FROM score WHERE button_id = ? AND date = CURRENT_DATE), 0) AS today_presses
            FROM 
                player p
            JOIN 
                score s ON p.id = s.player_id
            WHERE 
                s.button_id = ? AND s.date = CURRENT_DATE
            """, (button_id, button_id))
            result = cursor.fetchone()
            return {
                "player_id": result[0] if result else None,
                "player_name": result[1] if result else None,
                "is_new": bool(result[2]) if result else None,
                "today_presses": result[3] if result else 0
            }
        finally:
            cursor.close()
            conn.close()

    def upsert_score(self, button_id, player_id, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO score (player_id, button_id, date, presses, startedAt, stoppedAt)
            VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(button_id, date) DO UPDATE SET 
                player_id = excluded.player_id,
                startedAt = CURRENT_TIMESTAMP
            """, (player_id, button_id, date))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def create_player_and_upsert_score(self, player_name, button_id, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Step 1: Insert new player
            cursor.execute(
                "INSERT INTO player (name) VALUES (?)", (player_name,))
            new_player_id = cursor.lastrowid

            # Step 2: Upsert into score
            cursor.execute("""
                INSERT INTO score (player_id, button_id, date, presses, startedAt, stoppedAt)
                VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(button_id, date) DO UPDATE SET 
                    player_id = excluded.player_id,
                    startedAt = CURRENT_TIMESTAMP
            """, (new_player_id, button_id, date))

            conn.commit()
        except Exception as e:
            # Handle exceptions if needed
            print("Error:", e)
        finally:
            cursor.close()
            conn.close()

    def get_combobox_players(self, today,button_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.id, p.name 
                FROM player p
                LEFT JOIN score s ON p.id = s.player_id AND s.date = ?
                WHERE s.id IS NULL OR (s.button_id = ? AND s.date = ?)
            """, (today, button_id, today))
            players = cursor.fetchall()
            return players  # Returns list of tuples (player_id, player_name)
        finally:
            cursor.close()
            conn.close()

    def update_score_entry_player(self, button_id, new_player_id, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO score (button_id, player_id, date, presses, startedAt, stoppedAt)
                VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(button_id, date) DO UPDATE SET 
                    player_id = excluded.player_id,
                    startedAt = CURRENT_TIMESTAMP
            """, (button_id, new_player_id, date))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_score_entry(self, button_id, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT ds.player_id, ds.player_name, ds.score, ds.startedAt, 
                    ds.stoppedAt, ds.speed
                FROM daily_scores ds
                WHERE ds.button_id = ? AND ds.date = ?
            """, (button_id, date))
            entry = cursor.fetchone()
            if entry:
                return {
                    'player_id': entry[0],
                    'player_name': entry[1],
                    'score': entry[2],
                    'startedAt': entry[3],
                    'stoppedAt': entry[4],
                    'speed': entry[5]
                }
            else:
                return None
        finally:
            cursor.close()
            conn.close()

    def check_player_scores_before_date(self, player_id, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM score WHERE player_id = ? AND date < ?", (player_id, date))
            result = cursor.fetchone()
            return result[0] > 0
        except Exception as e:
            print("Error checking player's previous scores:", e)
            return False
        finally:
            cursor.close()
            conn.close()
    def get_player_name_by_id(self, player_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM player WHERE id = ?", (player_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        finally:
            cursor.close()
            conn.close()

    def can_player_be_deleted(self, player_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Check if the player has any scores greater than 0
            cursor.execute("SELECT EXISTS(SELECT 1 FROM score WHERE player_id = ? AND presses > 0)", (player_id,))
            result = cursor.fetchone()
            can_delete = result[0] == 0  # True if no scores > 0, False otherwise
            return can_delete
        finally:
            cursor.close()
            conn.close()

    def delete_player(self, player_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM player WHERE id = ?", (player_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


def bootstrap():
    global global_repo
    global_repo = ScoreRepository()

    locale.setlocale(locale.LC_ALL, 'nb_NO.UTF-8')  # Norwegian Bokmål locale

    app = QApplication(sys.argv)
    global vedApp
    vedApp = VedApp()
    vedApp.show()
    sys.exit(app.exec_())


bootstrap()
