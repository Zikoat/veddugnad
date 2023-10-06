from PyQt5.QtCore import QObject, pyqtSignal,QTimer,QTimer,pyqtSignal, QObject,Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QGridLayout,QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QScrollArea, QGridLayout, QGroupBox,QHBoxLayout
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
        self.hotkey_signal = HotkeySignal()
        self.initUI()
        update_signal.update_ui_signal.connect(self.update_ui)
        self.hotkey_signal.hotkey_pressed.connect(self.execute_function)

    def initUI(self):
        main_layout = QHBoxLayout()

        # Adding leaderboard
        self.leaderboard = LeaderboardWidget()
        main_layout.addWidget(self.leaderboard)

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

        main_layout.addLayout(player_boxes_layout)
        self.setLayout(main_layout)

        self.update_ui()

    def update_ui(self):
        for player_box in self.player_boxes:
            player_box.update_ui()
        self.leaderboard.update_ui()
        save_scores()

    def execute_function(self, func):
        func()



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
        score_speed_container = QHBoxLayout()

        # Adding score label
        self.score_label = QLabel()
        self.score_label.setStyleSheet("font-size: 40px;")
        score_speed_container.addWidget(self.score_label, alignment=Qt.AlignCenter)

        # Adding speed label
        self.speed_label = QLabel()
        score_speed_container.addWidget(self.speed_label, alignment=Qt.AlignCenter)

        self.layout.addLayout(score_speed_container)

        # Creating a container for increment/decrement buttons, centered horizontally
        inc_dec_container = QHBoxLayout()

        # Adding decrement button
        self.decrement_button = QPushButton('-')
        self.decrement_button.clicked.connect(self.decrement_score)
        self.decrement_button.setMaximumWidth(30)  # Set the maximum width to 30 pixels
        inc_dec_container.addWidget(self.decrement_button)

        # Adding increment button
        self.increment_button = QPushButton('+')
        self.increment_button.clicked.connect(self.increment_score)
        self.increment_button.setMaximumWidth(30)  # Set the maximum width to 30 pixels
        inc_dec_container.addWidget(self.increment_button)

        inc_dec_container.setAlignment(Qt.AlignCenter)  # Set alignment property here

        self.layout.addLayout(inc_dec_container)

        self.setLayout(self.layout)

    def on_hotkey_pressed(self):
        # Emit the signal with a lambda function as an argument that calls your update method
        self.hotkey_signal.hotkey_pressed.emit(lambda: self.press_button())

    def update_name(self):
        scores[today][self.button_id]["name"] = self.name_input.text()
        update_signal.update_ui_signal.emit()

    def press_button(self):
        if not self.timer.isActive():
            scores[today][self.button_id]["score"] += 1
            self.setStyleSheet("background-color: darkgrey;")  # Change to a darker color
            self.increment_button.setDisabled(True)  
            self.decrement_button.setDisabled(True)  
            self.timer.start()
            update_signal.update_ui_signal.emit()

    def timeout(self):
        self.timer.stop()
        self.setStyleSheet("")  # Reset to the original style
        self.increment_button.setDisabled(False)  
        self.decrement_button.setDisabled(False)  
        self.update_ui()

    def increment_score(self):
        scores[today][self.button_id]["score"] += 1
        update_signal.update_ui_signal.emit()


    def decrement_score(self):
        if scores[today][self.button_id]["score"] > 0:
            scores[today][self.button_id]["score"] -= 1
        update_signal.update_ui_signal.emit()

    def update_ui(self):
        player_data = scores[today][self.button_id]
        self.score_label.setText(f"{player_data['score']}")
        self.name_input.setText(player_data['name'] if player_data['name'] else '')
        if player_data['score'] > 1 and player_data['createdAt'] and player_data['updatedAt']:
            start_time = datetime.fromisoformat(player_data['createdAt'])
            end_time = datetime.fromisoformat(player_data['updatedAt'])
            duration = (end_time - start_time).total_seconds()
            speed = duration / (player_data['score'] - 1)
            self.speed_label.setText(f"Speed: {speed:.2f} secs/item")
        else:
            self.speed_label.setText("")

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
