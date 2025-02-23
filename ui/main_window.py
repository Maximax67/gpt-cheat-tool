from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt
from widgets.chat_panel import ChatPanel
from widgets.quick_answer_panel import QuickAnswerPanel
from widgets.transcription_panel import TranscriptionPanel
from widgets.controls_widget_panel import ControlsPanel
from ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Groq Audio Transcription & Chat")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        self.setMinimumWidth(400)
        self.setMinimumHeight(400)

        splitter_horizontal = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter_horizontal)

        # Left panel: Chat UI
        self.chat_panel = ChatPanel()
        splitter_horizontal.addWidget(self.chat_panel)

        # Right panel: Quick Answer (top), Transcription (middle) and Control Buttons (bottom)
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 5)

        splitter_vertical = QSplitter(Qt.Vertical)

        self.quick_answer_panel = QuickAnswerPanel()
        splitter_vertical.addWidget(self.quick_answer_panel)

        self.transcription_panel = TranscriptionPanel()
        splitter_vertical.addWidget(self.transcription_panel)

        right_panel_layout.addWidget(splitter_vertical)

        self.transcription_controls = ControlsPanel()
        right_panel_layout.addWidget(self.transcription_controls)

        splitter_horizontal.addWidget(right_panel)

        # Connect control signals to the transcription panel.
        self.transcription_panel.forward_signal.connect(
            self.forward_transcription_to_chat
        )
        self.quick_answer_panel.forward_signal.connect(
            self.forward_transcription_to_chat
        )
        self.transcription_controls.mic_toggled.connect(
            self.transcription_panel.set_mic_enabled
        )
        self.transcription_controls.speaker_toggled.connect(
            self.transcription_panel.set_speaker_enabled
        )
        self.transcription_controls.settings_clicked.connect(self.open_settings)

    def forward_transcription_to_chat(self, text):
        """
        When transcription blocks are forwarded, if the chat prompt field is nonempty,
        prepend its text to the transcription text.
        """
        prompt_text = self.chat_panel.get_prompt_text()
        if prompt_text:
            full_text = prompt_text + "\n" + text
        else:
            full_text = text

        self.chat_panel.send_message(full_text)
        self.chat_panel.clear_prompt()

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
