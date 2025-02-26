from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtCore import Signal

from ui.icons import Icon, get_icon


class ControlsPanel(QWidget):
    mic_toggled = Signal(bool)
    speaker_toggled = Signal(bool)
    settings_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.update_theme_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.mic_button = QPushButton()
        self.mic_button.setCheckable(True)
        self.mic_button.setChecked(True)
        self.mic_button.setToolTip("Toggle Mic")
        self.mic_button.clicked.connect(self._on_mic_clicked)

        self.speaker_button = QPushButton()
        self.speaker_button.setCheckable(True)
        self.speaker_button.setChecked(True)
        self.speaker_button.setToolTip("Toggle Speaker")
        self.speaker_button.clicked.connect(self._on_speaker_clicked)

        self.settings_button = QPushButton()
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(self._on_settings_clicked)

        layout.addWidget(self.mic_button)
        layout.addWidget(self.speaker_button)
        layout.addWidget(self.settings_button)

    def _on_mic_clicked(self):
        icon = Icon.MIC_ON if self.mic_button.isChecked() else Icon.MIC_OFF
        self.mic_button.setIcon(get_icon(icon))
        self.mic_toggled.emit(self.mic_button.isChecked())

    def _on_speaker_clicked(self):
        icon = Icon.SPEAKER_ON if self.speaker_button.isChecked() else Icon.SPEAKER_OFF
        self.speaker_button.setIcon(get_icon(icon))
        self.speaker_toggled.emit(self.speaker_button.isChecked())

    def _on_settings_clicked(self):
        self.settings_clicked.emit()

    def update_theme_ui(self):
        mic_icon = Icon.MIC_ON if self.mic_button.isChecked() else Icon.MIC_OFF
        speaker_icon = (
            Icon.SPEAKER_ON if self.speaker_button.isChecked() else Icon.SPEAKER_OFF
        )

        self.mic_button.setIcon(get_icon(mic_icon))
        self.speaker_button.setIcon(get_icon(speaker_icon))
        self.settings_button.setIcon(get_icon(Icon.SETTINGS))
