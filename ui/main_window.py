import os

from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt

from services.generate_text.TextGenerator import GroqTextGenerator
from services.groq import groq_client

from widgets.chat_panel import ChatPanel
from widgets.quick_answer_panel import QuickAnswerPanel
from widgets.transcription_panel import TranscriptionPanel
from widgets.controls_widget_panel import ControlsPanel

from ui.settings_dialog import SettingsDialog
from ui.themes import Theme, ThemeManager


QUICK_ANSWER_MESSAGE_CONTEXT = 5
QUICK_ANSWER_DEFAULT_PROMPT = "You have a poor transcript of speech below. Provide an answer based on the conversation. Give a straightforward response to help user answer in current situation. Audio recorded from user microphone labeled as [MIC] and audio from user speakers labeled as [SPEAKER]. Imagine that you are the person labeled as [MIC]. DO NOT ask to repeat, and DO NOT ask for clarification. Just direct answer."
QUICK_ANSWER_MODEL = os.environ.get("QUICK_ANSWER_MODEL")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.theme_manager = ThemeManager(Theme.AUTO)
        self.settings_dialog = SettingsDialog(parent=self)
        self.settings_dialog.set_current_theme(Theme.AUTO)
        self.settings_dialog.set_theme_signal.connect(self.update_theme)

        self._setup_ui()

    def _setup_ui(self):
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

        qucik_anwer_text_generator = GroqTextGenerator(groq_client, QUICK_ANSWER_MODEL)

        self.quick_answer_panel = QuickAnswerPanel(
            qucik_anwer_text_generator, QUICK_ANSWER_DEFAULT_PROMPT
        )
        self.quick_answer_panel.forward_signal.connect(
            self.forward_transcription_to_chat
        )
        self.quick_answer_panel.request_quick_answer_context_signal.connect(
            self._handle_request_quick_answer_context
        )

        splitter_vertical.addWidget(self.quick_answer_panel)

        self.transcription_panel = TranscriptionPanel()
        self.transcription_panel.forward_signal.connect(
            self.forward_transcription_to_chat
        )

        splitter_vertical.addWidget(self.transcription_panel)

        right_panel_layout.addWidget(splitter_vertical)

        self.transcription_controls = ControlsPanel()
        self.transcription_controls.mic_toggled.connect(
            self.transcription_panel.set_mic_enabled
        )
        self.transcription_controls.speaker_toggled.connect(
            self.transcription_panel.set_speaker_enabled
        )
        self.transcription_controls.settings_clicked.connect(self.open_settings)

        right_panel_layout.addWidget(self.transcription_controls)
        splitter_horizontal.addWidget(right_panel)

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

    def _handle_request_quick_answer_context(self):
        context = self.transcription_panel.get_messages(QUICK_ANSWER_MESSAGE_CONTEXT)
        self.quick_answer_panel.generate_quick_answer(context)

    def open_settings(self):
        self.settings_dialog.exec()

    def update_theme(self, theme: Theme):
        if self.theme_manager.set_theme(theme):
            self.settings_dialog.set_current_theme(theme)
            self.chat_panel.update_theme_ui()
            self.quick_answer_panel.update_theme_ui()
            self.transcription_panel.update_theme_ui()
            self.transcription_controls.update_theme_ui()
