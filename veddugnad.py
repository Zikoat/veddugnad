
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QGridLayout
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea, QGridLayout, QGroupBox
from datetime import datetime
import json
import os
import schedule
import shutil
import sys
import threading
import time
import keyboard


# File paths
COUNT_FILE = 'counters.json'
BG_IMAGE_FILE = 'bg.png'
BACKUP_FOLDER = 'backup'

# Last modified times
counter_last_modified = 0
bg_last_modified = 0

BUTTON_TIMEOUT_SECONDS = 3

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
    schedule.every().day.at("00:00").do(job)  # Schedule the job
    while True:
        schedule.run_pending()
        time.sleep(1)


# Signal class for updating UI
class UpdateSignal(QObject):
    update_ui_signal = pyqtSignal()

update_signal = UpdateSignal()

# Function to save scores to file
def save_scores():
    with open(COUNT_FILE, 'w') as f:
        json.dump(scores, f, indent=4)

# Main application window
class AppDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        update_signal.update_ui_signal.connect(self.update_ui)

    def initUI(self):
        layout = QGridLayout()

        self.leaderboard = LeaderboardWidget()
        layout.addWidget(self.leaderboard, 0, 0)

        self.player_boxes = [PlayerBox(str(i)) for i in range(1, 7)]
        for i, player_box in enumerate(self.player_boxes):
            layout.addWidget(player_box, i, 1)

        self.setLayout(layout)
        self.update_ui()

    def update_ui(self):
        for player_box in self.player_boxes:
            player_box.update_ui()
        self.leaderboard.update_ui()
        save_scores()


# Leaderboard widget
class LeaderboardWidget(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        content = QWidget()
        content.setLayout(self.layout)
        self.setWidget(content)

    def update_ui(self):
        # Clear the current UI
        for i in reversed(range(self.layout.count())): 
            widget = self.layout.itemAt(i).widget()
            widget.setParent(None)

        # Add updated data
        leaderboard = create_leaderboard()
        for entry in leaderboard:
            player_label = QLabel(f"Rank: {entry[0]}, Date: {entry[1]}, Name: {entry[2]}, Score: {entry[3]}, Speed: {entry[4]:.2f}")
            self.layout.addWidget(player_label)


# Player box widget
class PlayerBox(QGroupBox):
    def __init__(self, button_id):
        super().__init__()
        self.button_id = button_id
        self.timer = QTimer()
        self.timer.timeout.connect(self.timeout)
        self.timer.setInterval(BUTTON_TIMEOUT_SECONDS * 1000)  
        keyboard.add_hotkey('f1', self.player_action, args=(1,))

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.score_label = QLabel()
        self.speed_label = QLabel()
        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self.update_name)
        self.increment_button = QPushButton('+')
        self.increment_button.clicked.connect(self.increment_score)
        self.decrement_button = QPushButton('-')
        self.decrement_button.clicked.connect(self.decrement_score)
        
        self.layout.addWidget(self.score_label)
        self.layout.addWidget(self.speed_label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel(f"Button ID: {self.button_id}"))
        self.layout.addWidget(self.increment_button)
        self.layout.addWidget(self.decrement_button)
        self.setLayout(self.layout)

    def update_name(self):
        scores[today][self.button_id]["name"] = self.name_input.text()
        update_signal.update_ui_signal.emit()

    def increment_score(self):
        if not self.timer.isActive():
            scores[today][self.button_id]["score"] += 1
            self.setStyleSheet("background-color: darkgrey;")  # Change to a darker color
            self.timer.start()
            update_signal.update_ui_signal.emit()


    def decrement_score(self):
        if scores[today][self.button_id]["score"] > 0:
            scores[today][self.button_id]["score"] -= 1
        update_signal.update_ui_signal.emit()

    def update_ui(self):
        player_data = scores[today][self.button_id]
        self.score_label.setText(f"Score: {player_data['score']}")
        self.name_input.setText(player_data['name'] if player_data['name'] else '')
        if player_data['score'] > 1 and player_data['createdAt'] and player_data['updatedAt']:
            start_time = datetime.fromisoformat(player_data['createdAt'])
            end_time = datetime.fromisoformat(player_data['updatedAt'])
            duration = (end_time - start_time).total_seconds()
            speed = duration / (player_data['score'] - 1)
            self.speed_label.setText(f"Speed: {speed:.2f} secs/item")
        else:
            self.speed_label.setText("")

    def timeout(self):
        self.timer.stop()
        self.setStyleSheet("")  # Reset to the original style
        self.update_ui()

# Function to create leaderboard
def create_leaderboard():
    leaderboard = []
    for date, buttons in scores.items():
        for button_id, data in buttons.items():
            if data['createdAt'] and data['updatedAt'] and data['score'] > 0:
                start_time = datetime.fromisoformat(data['createdAt'])
                end_time = datetime.fromisoformat(data['updatedAt'])
                duration = (end_time - start_time).total_seconds()

                # Adjusting for the first item
                if data['score'] > 1:
                    speed = duration / (data['score'] - 1)
                else:
                    speed = duration
                
                date_norwegian_format = datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
                rank = len(leaderboard) + 1
                leaderboard.append((rank, date_norwegian_format, data['name'], data['score'], speed))

    # Sorting by score in descending order
    leaderboard.sort(key=lambda x: x[3], reverse=True)
    return leaderboard

# Load scores from file if exists or initialize with today's date and null/0 values
today = datetime.now().strftime('%Y-%m-%d')

if os.path.exists(COUNT_FILE):
    with open(COUNT_FILE, 'r') as f:
        scores = json.load(f)
        if today not in scores:
            scores[today] = {
                str(i): {"name": None, "score": 0, "createdAt": None, "updatedAt": None} for i in range(1, 7)
            }
else:
    scores = {
        today: {
            str(i): {"name": None, "score": 0, "createdAt": None, "updatedAt": None} for i in range(1, 7)
        }
    }

# Start the backup job in a separate thread
backup_thread = threading.Thread(target=start_backup_job)
backup_thread.start()

# Start the GUI in the main thread
app = QApplication(sys.argv)
demo = AppDemo()
demo.show()
sys.exit(app.exec_())
