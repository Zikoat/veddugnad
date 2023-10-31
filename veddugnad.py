from PyQt5.QtCore import QObject, pyqtSignal,QTimer,QTimer,pyqtSignal, QObject,Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QGridLayout,QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea, QGridLayout, QGroupBox,QHBoxLayout
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from datetime import datetime
import json
import os
import schedule
import shutil
import sys
import threading
import time
import keyboard
import locale
from PyQt5.QtGui import QPalette, QBrush, QPixmap
import sqlite3

# File paths
COUNT_FILE = 'counters.json'
BG_IMAGE_FILE = 'bg.png'
BACKUP_FOLDER = 'backup'

# Last modified times
counter_last_modified = 0
bg_last_modified = 0

BUTTON_TIMEOUT_SECONDS = 3

TEST_MODE = True

def backup_file(file_path, backup_folder):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename, file_extension = os.path.splitext(os.path.basename(file_path))
    backup_filename = f"{filename}_{timestamp}{file_extension}"
    backup_path = os.path.join(backup_folder, backup_filename)
    shutil.copy2(file_path, backup_path)
    print(f"File {file_path} backed up to {backup_path}")

def job():
    global counter_last_modified, bg_last_modified

    # Create backup folder if it doesn't exist
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    # Check if the counter file has been modified
    if os.path.getmtime(COUNT_FILE) > counter_last_modified:
        backup_file(COUNT_FILE, BACKUP_FOLDER)
        counter_last_modified = os.path.getmtime(COUNT_FILE)

    # Check if the bg image file has been modified
    if os.path.getmtime(BG_IMAGE_FILE) > bg_last_modified:
        backup_file(BG_IMAGE_FILE, BACKUP_FOLDER)
        bg_last_modified = os.path.getmtime(BG_IMAGE_FILE)

# This function will contain the infinite loop to run scheduled jobs
def start_backup_job():
    if TEST_MODE:
        schedule.every(10).seconds.do(job)
    else:
        schedule.every().day.at("00:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)


# Signal class for updating UI
class UpdateSignal(QObject):
    update_ui_signal = pyqtSignal()

update_signal = UpdateSignal()

# Main application window
class AppDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.hotkey_signal = HotkeySignal()
        self.initUI()
        update_signal.update_ui_signal.connect(self.update_ui)
        
        self.hotkey_signal.hotkey_pressed.connect(self.execute_function)

    def initUI(self):
        main_layout = QHBoxLayout()

        # Adding leaderboard
        self.leaderboard = LeaderboardWidget()
        main_layout.addWidget(self.leaderboard,1)

        # Create an attribute to hold player boxes
        self.player_boxes = [] 

        player_boxes_layout = QHBoxLayout()
        for i in range(0, 6, 2):  # Creating pairs
            pair_layout = QVBoxLayout()

            for j in range(2):  # Two player boxes per pair
                player_box = PlayerBox(str(i + j + 1), self.hotkey_signal)
                pair_layout.addWidget(player_box)
                self.player_boxes.append(player_box)  # Add player box to the list

            player_boxes_layout.addLayout(pair_layout)

        main_layout.addLayout(player_boxes_layout,2)
        # Set background image
        palette = QPalette()
        pixmap = QPixmap("bg.png").scaled(self.width(), self.height(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)

        self.setLayout(main_layout)

        self.update_ui()
    def resizeEvent(self, event):
        # Update the background image to fit the new size of the window
        palette = QPalette()
        pixmap = QPixmap("bg.png").scaled(self.width(), self.height(), Qt.IgnoreAspectRatio)
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.setPalette(palette)

    def update_ui(self):
        for player_box in self.player_boxes:
            player_box.update_ui()
        self.leaderboard.update_ui()

    def execute_function(self, func):
        func()

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
        self.table.setHorizontalHeaderLabels([ "Dato", "Navn", "Sekker", "Fart"])
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
            self.table.setItem(row_position, 2, QTableWidgetItem(str(entry[2])))
            self.table.setItem(row_position, 3, QTableWidgetItem(f"{entry[3]:.2f} s"))

class HotkeySignal(QObject):
    # This signal will be emitted when a hotkey is pressed
    hotkey_pressed = pyqtSignal(object)  # The signal carries a callable object


# Player box widget
class PlayerBox(QGroupBox):
    def __init__(self, button_id,hotkey_signal):
        super().__init__()
        self.button_id = button_id
        self.hotkey_signal = hotkey_signal

        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.timer.setInterval(BUTTON_TIMEOUT_SECONDS * 1000)  

        # add keyboard hotkeys for f1 through f6
        keyboard.add_hotkey(f'f{button_id}', self.on_hotkey_pressed)

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        # Adding name input
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.update_name)
        self.name_input.setStyleSheet("""
            font-size: 20px;
            height: 40px;
            padding: 5px 10px;
        """)
        self.layout.addWidget(self.name_input)

        # Creating a container for score and speed, centered horizontally
        score_speed_container = QVBoxLayout()

        # Adding score label with increased font size
        self.score_label = QLabel()
        self.score_label.setStyleSheet("font-size: 80px;")  
        score_speed_container.addWidget(self.score_label, alignment=Qt.AlignCenter)

        # Adding speed label below score label
        self.speed_label = QLabel()
        score_speed_container.addWidget(self.speed_label, alignment=Qt.AlignCenter)

        self.layout.addLayout(score_speed_container)
        self.setLayout(self.layout)

    def on_hotkey_pressed(self):
        # Emit the signal with a lambda function as an argument that calls your update method
        self.hotkey_signal.hotkey_pressed.emit(lambda: self.press_button())

    def update_name(self):
        today = getToday()
        global_repo.update_name(self.button_id, self.name_input.text(), today)
        update_signal.update_ui_signal.emit()

    def press_button(self):
        if not self.timer.isActive():
            today = getToday()
            global_repo.increment_score(self.button_id, today)
            self.setStyleSheet("background-color: darkgrey;")  # Change to a darker color

            self.timer.start()
            update_signal.update_ui_signal.emit()

    def timeout(self):
        self.timer.stop()
        self.setStyleSheet("")  # Reset to the original style
        self.update_ui()

    def update_ui(self):
        today = getToday()
        player_data = global_repo.get_player_score_data(today, self.button_id)

        if player_data:
            name, score, startedAt, stoppedAt, speed = player_data
            self.score_label.setText(str(score))
            self.name_input.setText(name if name else '')
            
            if score > 1 and startedAt and stoppedAt:
                self.speed_label.setText(f"{speed:.2f} sekunder per sekk")
            else:
                self.speed_label.setText("")
        else:
            # Handle the case where no data is returned
            self.score_label.setText("0")
            self.name_input.setText("")
            self.speed_label.setText("")

def create_leaderboard():
    leaderboard_data = global_repo.get_leaderboard()
    leaderboard = []
    for entry in leaderboard_data:
        formatted_date, name, score, speed = entry
        leaderboard.append((formatted_date, name, score, speed))
    return leaderboard

def getToday():
    return  datetime.now().strftime('%Y-%m-%d')


class ScoreRepository:
    def __init__(self):
        self.db_path = 'highscores.db'

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def update_name(self, button_id, new_name, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT player_id FROM player_button_date WHERE button_id=? AND date=?", (button_id, date))
            player_id_record = cursor.fetchone()
            if player_id_record:
                player_id = player_id_record[0]
                cursor.execute("UPDATE players SET name=? WHERE id=?", (new_name, player_id))
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
                JOIN players p ON ds.player_name = p.name
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
                JOIN players p ON ds.player_name = p.name
                ORDER BY ds.score DESC, speed ASC;
            """)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def increment_score(self, player_id, button_id, date):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Ensure there is a record in player_button_date
            cursor.execute("""
                INSERT INTO player_button_date (player_id, button_id, date)
                VALUES (?, ?, ?)
                ON CONFLICT(player_id, button_id, date) DO NOTHING
            """, (player_id, button_id, date))

            # Insert a new button press
            cursor.execute("""
                INSERT INTO button_presses (player_id, timestamp)
                VALUES (?, CURRENT_TIMESTAMP)
            """, (player_id,))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


def bootstrap():
    global global_repo
    locale.setlocale(locale.LC_ALL, 'nb_NO.UTF-8')  # Norwegian Bokmål locale

    global_repo = ScoreRepository()

    backup_thread = threading.Thread(target=start_backup_job)
    backup_thread.start()

    app = QApplication(sys.argv)
    demo = AppDemo()
    demo.show()
    sys.exit(app.exec_())

bootstrap()
