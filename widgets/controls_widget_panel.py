from enum import Enum
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal

from ui.icons import Icon, get_icon
from ui.themes import ThemeManager


class AudioCaptureInitState(Enum):
    INIT = 0
    INITIALIZING = 1
    ERROR = 2


class ControlsPanel(QWidget):
    mic_toggled = Signal(bool)
    speaker_toggled = Signal(bool)
    open_settings_signal = Signal()

    retry_mic_init = Signal()
    retry_speaker_init = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.mic_state = AudioCaptureInitState.INITIALIZING
        self.speaker_state = AudioCaptureInitState.INITIALIZING

        self._setup_ui()
        self.update_theme_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.mic_button = QPushButton()
        self.mic_button.setToolTip("Toggle Mic")
        self.mic_button.clicked.connect(self._on_mic_clicked)

        self.speaker_button = QPushButton()
        self.speaker_button.setToolTip("Toggle Speaker")
        self.speaker_button.clicked.connect(self._on_speaker_clicked)

        self.settings_button = QPushButton()
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(self.open_settings_signal.emit)

        layout.addWidget(self.mic_button)
        layout.addWidget(self.speaker_button)
        layout.addWidget(self.settings_button)

    def _on_mic_clicked(self):
        if self.mic_state == AudioCaptureInitState.INITIALIZING:
            return

        if self.mic_state == AudioCaptureInitState.ERROR:
            self.mic_state = AudioCaptureInitState.INITIALIZING
            self.update_mic_button_ui()
            self.retry_mic_init.emit()
            return

        icon = Icon.MIC_ON if self.mic_button.isChecked() else Icon.MIC_OFF
        self.mic_button.setIcon(get_icon(icon))
        self.mic_toggled.emit(self.mic_button.isChecked())

    def _on_speaker_clicked(self):
        if self.speaker_state == AudioCaptureInitState.INITIALIZING:
            return

        if self.speaker_state == AudioCaptureInitState.ERROR:
            self.speaker_state = AudioCaptureInitState.INITIALIZING
            self.update_speaker_button_ui()
            self.retry_speaker_init.emit()
            return

        icon = Icon.SPEAKER_ON if self.speaker_button.isChecked() else Icon.SPEAKER_OFF
        self.speaker_button.setIcon(get_icon(icon))
        self.speaker_toggled.emit(self.speaker_button.isChecked())

    def on_mic_init(self):
        self.mic_state = AudioCaptureInitState.INIT
        self.update_mic_button_ui()

    def on_speaker_init(self):
        self.speaker_state = AudioCaptureInitState.INIT
        self.update_speaker_button_ui()

    def on_mic_error(self):
        self.mic_state = AudioCaptureInitState.ERROR
        self.update_mic_button_ui()

    def on_speaker_error(self):
        self.speaker_state = AudioCaptureInitState.ERROR
        self.update_speaker_button_ui()

    def mic_init_retrying(self):
        self.mic_state = AudioCaptureInitState.INITIALIZING
        self.update_mic_button_ui()

    def speaker_init_retrying(self):
        self.speaker_state = AudioCaptureInitState.INITIALIZING
        self.update_speaker_button_ui()

    def update_mic_button_ui(self):
        is_white_theme = ThemeManager.is_white_theme()

        if self.mic_state == AudioCaptureInitState.ERROR:
            icon = Icon.REFRESH
            self.mic_button.setCheckable(False)
            background = (
                "#FEC9C8" if is_white_theme else "#8B0000"
            )  # Light Red and Dark Red
            self.mic_button.setStyleSheet(f"background: {background};")
        else:
            icon = Icon.MIC_ON if self.mic_button.isChecked() else Icon.MIC_OFF

            if self.mic_state == AudioCaptureInitState.INITIALIZING:
                background = (
                    "#FFEF92" if is_white_theme else "#716000"
                )  # Light yellow and Yellow
                self.mic_button.setStyleSheet(f"background: {background};")
                self.mic_button.setCheckable(False)
            else:
                self.mic_button.setCheckable(True)
                self.mic_button.setStyleSheet("")

        self.mic_button.setIcon(get_icon(icon))

    def update_speaker_button_ui(self):
        is_white_theme = ThemeManager.is_white_theme()

        if self.speaker_state == AudioCaptureInitState.ERROR:
            icon = Icon.REFRESH
            self.speaker_button.setCheckable(False)
            background = (
                "#FEC9C8" if is_white_theme else "#8B0000"
            )  # Light Red and Dark Red
            self.speaker_button.setStyleSheet(f"background: {background};")
        else:
            icon = (
                Icon.SPEAKER_ON if self.speaker_button.isChecked() else Icon.SPEAKER_OFF
            )

            if self.speaker_state == AudioCaptureInitState.INITIALIZING:
                background = (
                    "#FFEF92" if is_white_theme else "#716000"
                )  # Light yellow and Yellow
                self.speaker_button.setStyleSheet(f"background: {background};")
                self.speaker_button.setCheckable(False)
            else:
                self.speaker_button.setCheckable(True)
                self.speaker_button.setStyleSheet("")

        self.speaker_button.setIcon(get_icon(icon))

    def update_theme_ui(self):
        self.update_mic_button_ui()
        self.update_speaker_button_ui()
        self.settings_button.setIcon(get_icon(Icon.SETTINGS))
