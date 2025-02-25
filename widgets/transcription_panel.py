import os
import threading
import time
from queue import Queue

from services.record_audio.AudioSourceTypes import AudioSourceTypes
from services.transcribe.SourceTranscriber import SourceTranscriber
from services.record_audio.AudioRecorder import (
    BaseRecorder,
    MicRecorder,
    SpeakerRecorder,
)
from services.transcribe.Transcriber import GroqTranscriber
from services.groq import GroqClient

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, QMetaObject, Qt, Q_ARG, Slot, QThread, QTimer
from ui.icons import DELETE_ICON, SELECT_ALL_ICON, SEND_ICON
from widgets.transcription_list import SelectionStates, TranscriptionListWidget

TRANSCRIPTION_MODEL = os.environ.get("TRANSCRIPTION_MODEL")
ADJUSTING_FOR_NOISE_MESSAGE = "[ Adjusting for ambient noise ]"


class AdjustForNoiseTask(QThread):
    noise_adjusted = Signal()

    def __init__(self, recorder: BaseRecorder, audio_queue: Queue):
        super().__init__()
        self.recorder = recorder
        self.audio_queue = audio_queue

    def run(self):
        self.recorder.adjust_for_noise()
        self.noise_adjusted.emit()


class TranscriptionPanel(QWidget):
    forward_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()

        self.mic_enabled = True
        self.speaker_enabled = True

        self.audio_queue = Queue()
        self.mic_record_audio = MicRecorder()
        self.speaker_record_audio = SpeakerRecorder()

        self._mic_init_thread = AdjustForNoiseTask(
            self.mic_record_audio, self.audio_queue
        )
        self._speaker_init_thread = AdjustForNoiseTask(
            self.speaker_record_audio, self.audio_queue
        )

        self._mic_init_thread.noise_adjusted.connect(self._on_mic_noise_adjusted)
        self._speaker_init_thread.noise_adjusted.connect(
            self._on_speaker_noise_adjusted
        )

        self._adjusting_noise_audio_block = (
            self.transcription_list.add_transcription_block(
                AudioSourceTypes.MIC, ADJUSTING_FOR_NOISE_MESSAGE
            )
        )
        self._mic_init_thread.start()

        self.model = GroqTranscriber(GroqClient, TRANSCRIPTION_MODEL)
        self.transcriber = SourceTranscriber(
            self.mic_record_audio.source, self.speaker_record_audio.source, self.model
        )
        self.transcribe_thread = threading.Thread(
            target=self.transcriber.transcribe_audio_queue,
            args=(self.audio_queue, self._handle_transcript_update),
        )
        self.transcribe_thread.daemon = True
        self.transcribe_thread.start()

        self.transcription_list.selection_changed.connect(
            self._handle_selection_changed
        )
        self.transcription_list.forward_message_signal.connect(self.forward_signal.emit)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

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

    def _on_mic_noise_adjusted(self):
        if self.mic_enabled:
            self.mic_record_audio.record_into_queue(self.audio_queue)

        try:
            self._adjusting_noise_audio_block.delete_self()
        except RuntimeError:
            pass

        self._adjusting_noise_audio_block = (
            self.transcription_list.add_transcription_block(
                AudioSourceTypes.SPEAKER, ADJUSTING_FOR_NOISE_MESSAGE
            )
        )

        QTimer.singleShot(50, self._speaker_init_thread.start)

    def _on_speaker_noise_adjusted(self):
        if self.speaker_enabled:
            self.speaker_record_audio.record_into_queue(self.audio_queue)

        try:
            self._adjusting_noise_audio_block.delete_self()
        except RuntimeError:
            pass

        self._adjusting_noise_audio_block = None

    @Slot(str, str, bool)
    def update_transcription(self, source_string: str, text: str, is_new_phrase: bool):
        source_type = AudioSourceTypes(source_string)
        if is_new_phrase:
            self.transcription_list.add_transcription_block(source_type, text)
            return

        self.transcription_list.update_last_block_text(source_type, text)

    def _handle_transcript_update(
        self, source: AudioSourceTypes, text: str, is_new_phrase: bool
    ):
        QMetaObject.invokeMethod(
            self,
            "update_transcription",
            Qt.QueuedConnection,
            Q_ARG(str, source.value),
            Q_ARG(str, text),
            Q_ARG(bool, is_new_phrase),
        )

    def _change_stream_enabled(
        self, enabled: bool, stream: MicRecorder | SpeakerRecorder
    ):
        if not enabled:
            stream.stop_recording()
            return

        if not stream.is_recording():
            stream.record_into_queue(self.audio_queue)

    def set_mic_enabled(self, enabled: bool):
        if self.mic_enabled != enabled:
            self.mic_enabled = enabled
            self._change_stream_enabled(enabled, self.mic_record_audio)

    def set_speaker_enabled(self, enabled: bool):
        if self.speaker_enabled != enabled:
            self.speaker_enabled = enabled
            self._change_stream_enabled(enabled, self.speaker_record_audio)

    def _on_select_clicked(self):
        if self.transcription_list.get_is_all_selected():
            self.transcription_list.deselect_all()
        else:
            self.transcription_list.select_all()
            if not self.transcription_list.get_is_all_selected():
                self.select_button.setChecked(False)

    def _handle_selection_changed(self, selection_state: SelectionStates):
        if selection_state == SelectionStates.ALL_SELECTED:
            self.select_button.setChecked(True)
        else:
            self.select_button.setChecked(False)

        if selection_state == SelectionStates.ALL_DESELECTED:
            self.forward_button.setDisabled(True)
            self.delete_selected_button.setDisabled(True)
            return

        self.forward_button.setDisabled(False)
        self.delete_selected_button.setDisabled(False)

    def forward_selected(self):
        selected_blocks = self.transcription_list.selected_items()
        if not selected_blocks:
            return

        combined_text = "".join(
            block.get_text() + "\n" for block in selected_blocks
        ).strip()
        if combined_text:
            self.forward_signal.emit(combined_text)

        self.transcription_list.deselect_all()
        self.select_button.setChecked(False)
