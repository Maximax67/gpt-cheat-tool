import lorem
import queue
import threading
import time

from services.record_audio.AudioSourceTypes import AudioSourceTypes
from services.transcribe.SourceTranscriber import SourceTranscriber
from services.record_audio.AudioRecorder import MicRecorder, SpeakerRecorder
from services.transcribe.Transcriber import TestTranscriber

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
)
from PySide6.QtCore import QTimer, Signal
from ui.icons import DELETE_ICON, SELECT_ALL_ICON, SEND_ICON
from widgets.transcription_list import SelectionStates, TranscriptionListWidget


class TranscriptionPanel(QWidget):
    forward_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._init_timers()

        # Use flags to store the state of mic and speaker.
        self.mic_enabled = True
        self.speaker_enabled = True

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

        self.transcription_list.selection_changed.connect(
            self._handle_selection_changed
        )

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Use a QListWidget to hold transcription blocks.
        self.transcription_list = TranscriptionListWidget()
        main_layout.addWidget(self.transcription_list)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.select_button = QPushButton()
        self.select_button.setCheckable(True)
        self.select_button.setIcon(SELECT_ALL_ICON)
        self.select_button.setToolTip("Select All")
        self.select_button.clicked.connect(self._on_select_clicked)
        button_layout.addWidget(self.select_button)

        self.delete_selected_button = QPushButton()
        self.delete_selected_button.setDisabled(True)
        self.delete_selected_button.setIcon(DELETE_ICON)
        self.delete_selected_button.setToolTip("Delete Selected")
        self.delete_selected_button.clicked.connect(
            self.transcription_list.remove_selected
        )
        button_layout.addWidget(self.delete_selected_button)

        self.forward_button = QPushButton()
        self.forward_button.setDisabled(True)
        self.forward_button.setIcon(SEND_ICON)
        self.forward_button.setToolTip("Forward Selected")
        self.forward_button.clicked.connect(self.forward_selected)
        button_layout.addWidget(self.forward_button)

        main_layout.addLayout(button_layout)

    def _init_timers(self):
        # Simulate transcription updates every 5 seconds.
        self.transcription_timer = QTimer()
        self.transcription_timer.setInterval(5000)
        self.transcription_timer.timeout.connect(self._transcribe_audio)
        self.transcription_timer.start()

    def _transcribe_audio(self):
        if self.mic_enabled:
            mic_text = lorem.sentence()
            self.transcription_list.add_transcription_block(
                mic_text, source=AudioSourceTypes.MIC
            )

        if self.speaker_enabled:
            speaker_text = lorem.text()
            self.transcription_list.add_transcription_block(
                speaker_text, source=AudioSourceTypes.SPEAKERS
            )

    def set_mic_enabled(self, enabled: bool):
        self.mic_enabled = enabled

    def set_speaker_enabled(self, enabled: bool):
        self.speaker_enabled = enabled

    def _on_select_clicked(self):
        if self.transcription_list.get_is_all_selected():
            self.transcription_list.deselect_all()
        else:
            self.transcription_list.select_all()
            if not self.transcription_list.get_is_all_selected():
                self.select_button.setChecked(False)

    def _handle_selection_changed(self, selction_state: SelectionStates):
        if selction_state == SelectionStates.ALL_SELECTED:
            self.select_button.setChecked(True)
        else:
            self.select_button.setChecked(False)

        if selction_state == SelectionStates.ALL_DESELECTED:
            self.forward_button.setDisabled(True)
            self.delete_selected_button.setDisabled(True)
            return

        self.forward_button.setDisabled(False)
        self.delete_selected_button.setDisabled(False)

    def forward_selected(self):
        """
        Gathers the selected transcription blocks and emits them via the forward_signal.
        """
        selected_blocks = self.transcription_list.selected_items()
        if not selected_blocks:
            return

        combined_text = ""
        for block in selected_blocks:
            combined_text += block.get_text() + "\n"
        if combined_text:
            self.forward_signal.emit(combined_text.strip())

        self.transcription_list.deselect_all()
        self.select_button.setChecked(False)
