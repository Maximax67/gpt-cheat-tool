from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QGroupBox,
)
from PySide6.QtCore import Qt

from ui.icons import update_icon_colors
from ui.switch_theme import switch_theme


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)

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
        self.theme_selector.addItems(["Light", "Dark", "System"])
        self.theme_selector.currentTextChanged.connect(self.on_theme_changed)
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
        self.audio_input_selector.currentTextChanged.connect(
            self.on_audio_input_changed
        )
        input_layout.addWidget(self.audio_input_selector)
        audio_layout.addLayout(input_layout)

        # Audio output device selector
        output_layout = QHBoxLayout()
        output_label = QLabel("Audio Output Device:")
        output_layout.addWidget(output_label)

        self.audio_output_selector = QComboBox(self)
        self.audio_output_selector.currentTextChanged.connect(
            self.on_audio_output_changed
        )
        output_layout.addWidget(self.audio_output_selector)
        audio_layout.addLayout(output_layout)

        main_layout.addWidget(audio_group)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button, alignment=Qt.AlignRight)

    def on_theme_changed(self, theme: str):
        switch_theme(theme.lower())
        update_icon_colors(theme.lower())

    def on_audio_input_changed(self, device_name: str):
        # Event handler for audio input change.
        print("Audio input changed to:", device_name)
        # Add further event handling here, e.g., emitting a signal.

    def on_audio_output_changed(self, device_name: str):
        # Event handler for audio output change.
        print("Audio output changed to:", device_name)
        # Add further event handling here, e.g., emitting a signal.

    def set_audio_input_devices(self, devices: list):
        """Populate the audio input device selector with a list of device names."""
        self.audio_input_selector.clear()
        self.audio_input_selector.addItems(devices)

    def set_audio_output_devices(self, devices: list):
        """Populate the audio output device selector with a list of device names."""
        self.audio_output_selector.clear()
        self.audio_output_selector.addItems(devices)
