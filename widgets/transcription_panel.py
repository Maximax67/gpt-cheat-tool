import lorem
import queue
import threading
import time

from services.transcribe.SourceTranscriber import SourceTranscriber
from services.record_audio.AudioRecorder import MicRecorder, SpeakerRecorder
from services.transcribe.Transcriber import TestTranscriber

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import QTimer, Signal
from widgets.transcription_block import TranscriptionBlockWidget
from ui.settings_dialog import SettingsDialog
from ui.icons import (
    MIC_ON_ICON,
    MIC_OFF_ICON,
    SPEAKER_ON_ICON,
    SPEAKER_OFF_ICON,
    PAUSE_ICON,
    SETTINGS_ICON,
    SEND_ICON,
    PLAY_ICON
)


class TranscriptionPanel(QWidget):
    # Signal emitted when the user chooses to forward selected transcription blocks.
    forwardSignal = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._init_timers()

        self.audio_queue = queue.Queue()
        user_record_audio = MicRecorder()
        user_record_audio.record_into_queue(self.audio_queue)

        time.sleep(2)

        speaker_record_audio = SpeakerRecorder()
        speaker_record_audio.record_into_queue(self.audio_queue)

        self.model = TestTranscriber()
        self.transcriber = SourceTranscriber(
            user_record_audio.source, speaker_record_audio.source, self.model
        )
        self.transcribe_thread = threading.Thread(
            target=self.transcriber.transcribe_audio_queue, args=(self.audio_queue,)
        )
        self.transcribe_thread.daemon = True
        self.transcribe_thread.start()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Use a QListWidget to hold transcription blocks.
        self.transcription_list = QListWidget()
        self.transcription_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self.transcription_list)

        # Control buttons row.
        controls_layout = QHBoxLayout()

        self.mic_button = QPushButton()
        self.mic_button.setCheckable(True)
        self.mic_button.setChecked(True)
        self.mic_button.setIcon(MIC_ON_ICON)
        self.mic_button.setToolTip("Toggle Mic")
        self.mic_button.clicked.connect(self._toggle_mic)

        self.speaker_button = QPushButton()
        self.speaker_button.setCheckable(True)
        self.speaker_button.setChecked(True)
        self.speaker_button.setIcon(SPEAKER_ON_ICON)
        self.speaker_button.setToolTip("Toggle Speaker")
        self.speaker_button.clicked.connect(self._toggle_speaker)

        self.pause_button = QPushButton()
        self.pause_button.setCheckable(True)
        self.pause_button.setIcon(PAUSE_ICON)
        self.pause_button.setToolTip("Pause Transcription")
        self.pause_button.clicked.connect(self._toggle_pause)

        self.settings_button = QPushButton()
        self.settings_button.setIcon(SETTINGS_ICON)
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(self._open_settings)

        self.forward_button = QPushButton()
        self.forward_button.setIcon(SEND_ICON)
        self.forward_button.setToolTip("Forward Selected")
        self.forward_button.clicked.connect(self._forward_selected)

        controls_layout.addWidget(self.mic_button)
        controls_layout.addWidget(self.speaker_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.settings_button)
        controls_layout.addWidget(self.forward_button)
        layout.addLayout(controls_layout)

    def _init_timers(self):
        # Simulate transcription updates every 5 seconds.
        self.transcription_timer = QTimer()
        self.transcription_timer.setInterval(5000)
        self.transcription_timer.timeout.connect(self._transcribe_audio)
        self.transcription_timer.start()

    def _transcribe_audio(self):
        if self.pause_button.isChecked():
            return

        if self.mic_button.isChecked():
            mic_text = lorem.text()
            self._add_transcription_block(mic_text, source="mic")

        if self.speaker_button.isChecked():
            speaker_text = lorem.text()
            self._add_transcription_block(speaker_text, source="speaker")

    def _add_transcription_block(self, text, source="mic"):
        block = TranscriptionBlockWidget(text, source)
        block.deleteRequested.connect(self._remove_block)
        item = QListWidgetItem()
        # Use the widget's sizeHint; height adjusts to its content.
        item.setSizeHint(block.sizeHint())
        self.transcription_list.addItem(item)
        self.transcription_list.setItemWidget(item, block)

    def _remove_block(self, widget):
        # Safely remove the widget from the list.
        for i in range(self.transcription_list.count()):
            item = self.transcription_list.item(i)
            if self.transcription_list.itemWidget(item) is widget:
                self.transcription_list.takeItem(i)
                widget.deleteLater()
                break

    def _toggle_mic(self):
        if self.mic_button.isChecked():
            self.mic_button.setIcon(MIC_ON_ICON)
        else:
            self.mic_button.setIcon(MIC_OFF_ICON)

    def _toggle_speaker(self):
        if self.speaker_button.isChecked():
            self.speaker_button.setIcon(SPEAKER_ON_ICON)
        else:
            self.speaker_button.setIcon(SPEAKER_OFF_ICON)

    def _toggle_pause(self):
        if self.pause_button.isChecked():
            self.pause_button.setIcon(PLAY_ICON)
        else:
            self.pause_button.setIcon(PAUSE_ICON)

    def _open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _forward_selected(self):
        selected_items = self.transcription_list.selectedItems()
        if not selected_items:
            return
        combined_text = ""
        for item in selected_items:
            block = self.transcription_list.itemWidget(item)
            if block:
                combined_text += block.get_text() + "\n"
        if combined_text:
            self.forwardSignal.emit(combined_text.strip())
