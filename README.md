# veddugnad

## installation
1. download sqlite, extract it to a folder, and add that folder to PATH
2. Open powershell as admin, and run the following commands:
```shell
python3 -m venv myenv
.\myenv\scripts\activate
pip install -r requirements.txt
sqlite3 highscores.db < create_db.sql
python3 veddugnad.py
```

## qs for gpt

---

For an editable QComboBox a QCompleter is created automatically. This completer performs case insensitive inline completion but you can adjust that if needed, for example

```python
from PyQt5 import QtWidgets
from itertools import product

app = QtWidgets.QApplication([])

# wordlist for testing
wordlist = [''.join(combo) for combo in product('abc', repeat = 4)]

combo = QtWidgets.QComboBox()
combo.addItems(wordlist)

# completers only work for editable combo boxes. QComboBox.NoInsert prevents insertion of the search text
combo.setEditable(True)
combo.setInsertPolicy(QtWidgets.QComboBox.NoInsert)

# change completion mode of the default completer from InlineCompletion to PopupCompletion
combo.completer().setCompletionMode(QtWidgets.QCompleter.PopupCompletion)

combo.show()
app.exec()
```
```python
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

    def on_hotkey_pressed(self):
        global_repo.increment_score(self.button_id, today)
        self.update_ui()
```

The first code is an example of how to create a combobox with completions. Then comes the current PlayerBox. 

Create the PlayerBox anew. Use the get_player_info, and run it every time the ui updates. Update the ui after initialisation and every time some data changes. Here are the states, for reference:

1 No player selected
2 Player selected, no score today, and no scores on previous days, means the player is new
3 Player selected, no score today, but scores on previous days, means the player is existing
4 Player selected, score today

Create a new combobox where you can search for player names with completions in the place where the current name_input is. To the right of the combobox there should be a plus button. The plus button should be enabled when there is no player selected, or if the selected player is existing. The content below should be a text which says "Select player" if no player is selected. When the player is selected and there is no score today, there should be an input with the player name and a text which says "press button to start". When there is a player selected and there is a score today, then there should be a text which says the current score and a text which says "speed" and the current speed.
When the index in the combobox changes, then you should run upsert_player_button_date, and call it with the button id of the current playerbox, the selected player id and the current timestamp. Then you should update the ui.
