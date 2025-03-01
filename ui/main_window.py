from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Qt

from services.generate_text.chat_controller import ChatController
from services.generate_text.text_generator import get_text_generator

from settings import AppSettings
from widgets.chat_panel import ChatPanel
from widgets.quick_answer_panel import QuickAnswerPanel
from widgets.transcription_panel import TranscriptionPanel
from widgets.controls_widget_panel import ControlsPanel

from ui.settings_dialog import SettingsDialog
from ui.themes import Theme, ThemeManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings: AppSettings = AppSettings.load()
        self.theme_manager = ThemeManager(self.settings.theme)

        self.settings_dialog = SettingsDialog(self.settings, parent=self)
        self.settings_dialog.set_current_theme(self.settings.theme)
        self.settings_dialog.set_theme_signal.connect(self.update_theme)

        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("GPT Cheat Tool")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.setMinimumWidth(400)
        self.setMinimumHeight(400)

        splitter_horizontal = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter_horizontal)

        chat_text_gen = self.settings.chat.text_generator
        chat_text_generator = get_text_generator(
            chat_text_gen.provider,
            model=chat_text_gen.model,
            temperature=chat_text_gen.temperature,
            max_tokens=chat_text_gen.max_tokens,
            top_p=chat_text_gen.top_p,
            stream=chat_text_gen.stream,
            timeout=chat_text_gen.timeout,
        )
        chat_controller = ChatController(
            chat_text_generator, chat_text_gen.prompt, chat_text_gen.message_context
        )

        # Left panel: Chat UI
        self.chat_panel = ChatPanel(chat_controller)
        splitter_horizontal.addWidget(self.chat_panel)

        # Right panel: Quick Answer (top), Transcription (middle) and Control Buttons (bottom)
        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 5)

        splitter_vertical = QSplitter(Qt.Vertical)

        qa_text_gen = self.settings.quick_answers.text_generator
        quick_answer_text_generator = get_text_generator(
            qa_text_gen.provider,
            model=qa_text_gen.model,
            temperature=qa_text_gen.temperature,
            max_tokens=qa_text_gen.max_tokens,
            top_p=qa_text_gen.top_p,
            stream=qa_text_gen.stream,
            timeout=qa_text_gen.timeout,
        )
        self.quick_answer_panel = QuickAnswerPanel(
            quick_answer_text_generator,
            qa_text_gen.prompt,
            self.settings.quick_answers.default_message,
        )
        self.quick_answer_panel.forward_signal.connect(
            self.forward_transcription_to_chat
        )
        self.quick_answer_panel.request_quick_answer_context_signal.connect(
            self._handle_request_quick_answer_context
        )

        splitter_vertical.addWidget(self.quick_answer_panel)

        self.transcription_controls = ControlsPanel()
        self.transcription_panel = TranscriptionPanel(self.settings.transcription)

        self.transcription_panel.mic_init_signal.connect(self._on_mic_init)
        self.transcription_panel.speaker_init_signal.connect(self._on_speaker_init)
        self.transcription_panel.mic_recorder_error.connect(self._on_mic_error)
        self.transcription_panel.speaker_recorder_error.connect(self._on_speaker_error)
        self.transcription_panel.forward_signal.connect(
            self.forward_transcription_to_chat
        )

        self.settings_dialog.audio_input_changed.connect(
            self.transcription_panel.retry_mic_init
        )
        self.settings_dialog.audio_output_changed.connect(
            self.transcription_panel.retry_speaker_init
        )

        self.transcription_controls.mic_toggled.connect(
            self.transcription_panel.set_mic_enabled
        )
        self.transcription_controls.speaker_toggled.connect(
            self.transcription_panel.set_speaker_enabled
        )
        self.transcription_controls.open_settings_signal.connect(self.open_settings)
        self.transcription_controls.retry_mic_init.connect(self._on_mic_init_retry)
        self.transcription_controls.retry_speaker_init.connect(
            self._on_speaker_init_retry
        )

        self.transcription_panel.setup_audio_transcription()

        splitter_vertical.addWidget(self.transcription_panel)
        right_panel_layout.addWidget(splitter_vertical)
        right_panel_layout.addWidget(self.transcription_controls)
        splitter_horizontal.addWidget(right_panel)

    def forward_transcription_to_chat(self, text):
        prompt_text = self.chat_panel.get_prompt_text()
        if prompt_text:
            full_text = prompt_text + "\n" + text
        else:
            full_text = text

        self.chat_panel.send_message(full_text)
        self.chat_panel.clear_prompt()

    def _handle_request_quick_answer_context(self):
        context = self.transcription_panel.get_messages(
            self.settings.quick_answers.text_generator.message_context
        )
        self.quick_answer_panel.generate_quick_answer(context)

    def open_settings(self):
        self.settings_dialog.populate_audio_devices()
        self.settings_dialog.exec()

    def _on_mic_init(self):
        self.settings_dialog.unlock_audio_input_selection()
        self.transcription_controls.on_mic_init()

    def _on_speaker_init(self):
        self.settings_dialog.unlock_audio_output_selection()
        self.transcription_controls.on_speaker_init()

    def _on_mic_error(self):
        self.settings_dialog.unlock_audio_input_selection()
        self.transcription_controls.on_mic_error()

    def _on_speaker_error(self):
        self.settings_dialog.unlock_audio_output_selection()
        self.transcription_controls.on_speaker_error()

    def _on_mic_init_retry(self):
        self.settings_dialog.lock_audio_input_selection()
        self.transcription_panel.retry_mic_init()

    def _on_speaker_init_retry(self):
        self.settings_dialog.lock_audio_output_selection()
        self.transcription_panel.retry_speaker_init()

    def _on_mic_init_retry_from_settings(self):
        self.settings_dialog.lock_audio_input_selection()
        self.transcription_controls.mic_init_retrying()
        self.transcription_panel.retry_mic_init()

    def _on_speakers_init_retry_from_settings(self):
        self.settings_dialog.lock_audio_output_selection()
        self.transcription_controls.speaker_init_retrying()
        self.transcription_panel.retry_mic_init()

    def update_theme(self, theme: Theme):
        if self.theme_manager.set_theme(theme):
            self.settings_dialog.set_current_theme(theme)
            self.chat_panel.update_theme_ui()
            self.quick_answer_panel.update_theme_ui()
            self.transcription_panel.update_theme_ui()
            self.transcription_controls.update_theme_ui()
