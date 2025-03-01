import subprocess
from typing import List, Tuple

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal

from utils.audio_devices import AudioDevices
from utils.platform import CURRENT_PLATFORM, Platform
from settings import AppSettings
from ui.themes import Theme


class SettingsDialog(QDialog):
    set_theme_signal = Signal(Theme)
    audio_input_changed = Signal()
    audio_output_changed = Signal()

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)

        self.settings = settings
        self.ignore_audio_selection = False

        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Settings")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Theme selection layout
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        theme_layout.addWidget(theme_label)

        self.theme_selector = QComboBox(self)
        self.theme_selector.addItems([theme.value.capitalize() for theme in Theme])
        self.theme_selector.currentTextChanged.connect(self._on_theme_changed)

        theme_layout.addWidget(self.theme_selector)
        main_layout.addLayout(theme_layout)

        # Audio settings group box
        audio_group = QGroupBox("Audio Settings", self)
        audio_layout = QVBoxLayout(audio_group)

        # Audio input device selector
        input_layout = QHBoxLayout()
        input_label = QLabel("Audio Input Device:")
        input_layout.addWidget(input_label)

        self.audio_input_selector = QComboBox(self)
        self.audio_input_selector.setDisabled(True)
        self.audio_input_selector.currentTextChanged.connect(
            self._on_audio_input_changed
        )
        input_layout.addWidget(self.audio_input_selector)
        audio_layout.addLayout(input_layout)

        # Audio output device selector
        output_layout = QHBoxLayout()
        output_label = QLabel("Audio Output Device:")
        output_layout.addWidget(output_label)

        self.audio_output_selector = QComboBox(self)
        self.audio_output_selector.setDisabled(True)
        self.audio_output_selector.currentTextChanged.connect(
            self._on_audio_output_changed
        )
        output_layout.addWidget(self.audio_output_selector)
        audio_layout.addLayout(output_layout)

        main_layout.addWidget(audio_group)

        buttons_layout = QHBoxLayout()

        about_button = QPushButton("About", self)
        about_button.clicked.connect(self._show_about_dialog)
        buttons_layout.addWidget(about_button)

        config_button = QPushButton("Open Config", self)
        config_button.clicked.connect(self._open_config_file)
        buttons_layout.addWidget(config_button)

        reset_button = QPushButton("Reset Settings", self)
        reset_button.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(reset_button)

        self.close_button = QPushButton("Close", self)
        self.close_button.setDefault(True)
        self.close_button.setFocus()
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        main_layout.addLayout(buttons_layout)

    def _show_about_dialog(self):
        about_text = (
            "<h2>About GPT Cheat Tool</h2>"
            "<p><b>Author:</b> Bielikov Maksym</p>"
            "<p><b>Email:</b> <a href='mailto:maximax6767@gmail.com'>maximax6767@gmail.com</a></p>"
            "<p><b>Source code:</b> <a href='https://github.com/Maximax67/gpt-cheat-tool'>https://github.com/Maximax67/gpt-cheat-tool</a></p>"
            "<p>This app is a real-time audio transcription tool that listens to both your microphone and speakers. "
            "It uses the LLM model to generate answers, making it ideal for cheating during interviews or exams. But perhaps you can find a more ethical use for it. "
            "Currently only Groq platform is supported. This application has only been tested on Windows, there may be problems running on other OS. This app is open-source and totally free to use! Licensed under the MIT License.</p>"
            "<p>Feedback is always welcome! Feel free to check out the source code or reach out if you have questions.</p>"
        )
        QMessageBox.about(self, "About", about_text)
        self.close_button.setFocus()

    def _open_config_file(self):
        settings_path = self.settings.default_settings_path
        try:
            if CURRENT_PLATFORM == Platform.WINDOWS:
                subprocess.Popen(["notepad", settings_path], shell=True)
            elif CURRENT_PLATFORM == Platform.MACOS:
                subprocess.Popen(["open", settings_path])
            else:
                subprocess.Popen(["xdg-open", settings_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open config file: {e}")

        self.close_button.setFocus()

    def _reset_settings(self):
        self.settings = self.settings.reset()
        QMessageBox.information(
            self,
            "Settings Reset",
            "Settings have been reset to defaults. Please restart the application for changes to take effect.",
        )
        self.close_button.setFocus()

    @staticmethod
    def _remove_audio_devices_duplicates(
        devices: List[Tuple[int, str]]
    ) -> List[Tuple[int, str]]:
        seen = set()
        unique_devices = []
        for device_index, device_name in devices:
            if device_name not in seen:
                seen.add(device_name)
                unique_devices.append((device_index, device_name))

        return unique_devices

    def populate_audio_devices(self):
        self.ignore_audio_selection = True

        input_devices = AudioDevices.get_audio_input_devices()
        output_devices = AudioDevices.get_audio_output_devices()

        default_input_device = AudioDevices.get_default_audio_input_device()
        default_output_device = AudioDevices.get_default_audio_output_device()

        input_devices = self._remove_audio_devices_duplicates(input_devices)
        output_devices = self._remove_audio_devices_duplicates(output_devices)

        self.audio_input_selector.clear()
        self.audio_output_selector.clear()

        self.audio_input_selector.addItem(f"Default ({default_input_device[1]})")
        self.audio_output_selector.addItem(f"Default ({default_output_device[1]})")

        for device_index, device_name in input_devices:
            self.audio_input_selector.addItem(device_name, userData=device_index)

        for device_index, device_name in output_devices:
            self.audio_output_selector.addItem(device_name, userData=device_index)

        if self.settings.transcription.mic.device_index is not None:
            mic_device_index = self.settings.transcription.mic.device_index
            for index, name in input_devices:
                if index == mic_device_index:
                    self.audio_input_selector.setCurrentText(name)
                    break

        if self.settings.transcription.speaker.device_index is not None:
            speaker_device_index = self.settings.transcription.speaker.device_index
            for index, name in output_devices:
                if index == speaker_device_index:
                    self.audio_output_selector.setCurrentText(name)
                    break

        self.ignore_audio_selection = False

    def _on_theme_changed(self, theme: str):
        theme = Theme(theme.lower())
        self.settings.theme = theme
        self.set_theme_signal.emit(theme)
        self.settings.save()
        self.close_button.setFocus()

    def set_current_theme(self, theme: Theme):
        self.theme_selector.setCurrentText(theme.value.capitalize())

    def lock_audio_input_selection(self):
        self.audio_input_selector.setDisabled(True)

    def lock_audio_output_selection(self):
        self.audio_output_selector.setDisabled(True)

    def unlock_audio_input_selection(self):
        self.audio_input_selector.setDisabled(False)

    def unlock_audio_output_selection(self):
        self.audio_output_selector.setDisabled(False)

    def _on_audio_input_changed(self, device_name: str):
        if self.ignore_audio_selection:
            return

        if device_name.startswith("Default"):
            self.settings.transcription.mic.device_index = None
        else:
            self.settings.transcription.mic.device_index = (
                self.audio_input_selector.currentData()
            )

        self.lock_audio_input_selection()
        self.audio_input_changed.emit()
        self.settings.save()
        self.close_button.setFocus()

    def _on_audio_output_changed(self, device_name: str):
        if self.ignore_audio_selection:
            return

        if device_name.startswith("Default"):
            self.settings.transcription.speaker.device_index = None
        else:
            self.settings.transcription.speaker.device_index = (
                self.audio_output_selector.currentData()
            )

        self.lock_audio_output_selection()
        self.audio_output_changed.emit()
        self.settings.save()
        self.close_button.setFocus()
