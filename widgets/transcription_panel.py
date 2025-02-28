import os
import threading

from collections import deque
from datetime import datetime
from typing import List, Optional, Tuple

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, QMetaObject, Qt, Q_ARG, Slot, QThread, QTimer

from services.record_audio.AudioSourceType import AudioSourceType
from services.transcribe.SourceTranscriber import SourceTranscriber
from services.record_audio.AudioRecorder import (
    BaseRecorder,
    MicRecorder,
    SpeakerRecorder,
)
from services.transcribe.Transcriber import GroqTranscriber
from services.groq import groq_client

from widgets.transcription_list import SelectionStates, TranscriptionListWidget
from ui.icons import Icon, get_icon

TRANSCRIPTION_MODEL = os.environ.get("TRANSCRIPTION_MODEL")
INIT_MESSAGE = "[ Initializing ]"
ADJUSTING_FOR_NOISE_MESSAGE = "[ Adjusting for ambient noise ]"


class MicInitTask(QThread):
    initialized = Signal(MicRecorder)
    error = Signal(str)

    def run(self):
        try:
            mic = MicRecorder()
            self.initialized.emit(mic)
        except Exception as e:
            print(e)
            self.error.emit(str(e))


class SpeakerInitTask(QThread):
    initialized = Signal(SpeakerRecorder)
    error = Signal(str)

    def run(self):
        try:
            speaker = SpeakerRecorder()
            self.initialized.emit(speaker)
        except Exception as e:
            print(e)
            self.error.emit(str(e))


class AdjustForNoiseTask(QThread):
    noise_adjusted = Signal()
    error = Signal(str)

    def __init__(self, recorder: BaseRecorder):
        super().__init__()
        self.recorder = recorder

    def run(self):
        try:
            self.recorder.adjust_for_noise()
            self.noise_adjusted.emit()
        except Exception as e:
            self.error.emit(str(e))


class TranscriptionPanel(QWidget):
    forward_signal = Signal(str)

    mic_init_signal = Signal()
    speaker_init_signal = Signal()

    mic_recorder_error = Signal()
    speaker_recorder_error = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.update_theme_ui()

        self.mic_enabled = False
        self.speaker_enabled = False

        self.is_first_init_attempt = True

        self.is_mic_init = False
        self.is_speaker_init = False

        self._mic_init_audio_block = None
        self._speaker_init_audio_block = None

        self.mic_transcribe_thread = None
        self.speaker_transcribe_thread = None

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.transcription_list = TranscriptionListWidget()
        self.transcription_list.selection_changed.connect(
            self._handle_selection_changed
        )
        self.transcription_list.forward_message_signal.connect(self.forward_signal.emit)
        main_layout.addWidget(self.transcription_list)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(0, 0, 0, 0)

        self.select_button = QPushButton()
        self.select_button.setCheckable(True)
        self.select_button.setToolTip("Select All")
        self.select_button.clicked.connect(self._on_select_clicked)
        button_layout.addWidget(self.select_button)

        self.delete_selected_button = QPushButton()
        self.delete_selected_button.setDisabled(True)
        self.delete_selected_button.setToolTip("Delete Selected")
        self.delete_selected_button.clicked.connect(
            self.transcription_list.remove_selected
        )
        button_layout.addWidget(self.delete_selected_button)

        self.forward_button = QPushButton()
        self.forward_button.setDisabled(True)
        self.forward_button.setToolTip("Forward Selected")
        self.forward_button.clicked.connect(self.forward_selected)
        button_layout.addWidget(self.forward_button)

        main_layout.addLayout(button_layout)

    def setup_audio_transcription(self):
        self.mic_audio_queue: deque[Tuple[datetime, bytes]] = deque()
        self.speaker_audio_queue: deque[Tuple[datetime, bytes]] = deque()
        self.transcriber = GroqTranscriber(groq_client, TRANSCRIPTION_MODEL)
        self._init_mic_recorder()

    def _update_mic_transcription_message(self, message: str):
        if self._mic_init_audio_block:
            self._mic_init_audio_block.set_text(message)
        else:
            self._mic_init_audio_block = (
                self.transcription_list.add_transcription_block(
                    AudioSourceType.MIC, message
                )
            )

    def _update_speaker_transcription_message(self, message: str):
        if self._speaker_init_audio_block:
            self._speaker_init_audio_block.set_text(message)
        else:
            self._speaker_init_audio_block = (
                self.transcription_list.add_transcription_block(
                    AudioSourceType.SPEAKER, message
                )
            )

    def _on_mic_recorder_error(self, error: str):
        self.mic_recorder_error.emit()
        self._update_mic_transcription_message("Mic init error: " + error)

        if self.is_first_init_attempt:
            self.is_first_init_attempt = False
            self._init_speaker_recorder()

    def _on_speaker_recorder_error(self, error: str):
        self.speaker_recorder_error.emit()
        self._update_speaker_transcription_message("Speaker init error: " + error)

        if self.is_first_init_attempt:
            self.is_first_init_attempt = False

    def _init_mic_recorder(self, is_retry: bool = False):
        self._update_mic_transcription_message(INIT_MESSAGE)

        self.mic_init_thread = MicInitTask()
        self.mic_init_thread.initialized.connect(self._on_mic_recorder_initialized)
        self.mic_init_thread.error.connect(self._on_mic_recorder_error)

        if is_retry:
            QTimer.singleShot(100, self.mic_init_thread.start)
        else:
            self.mic_init_thread.start()

    def _on_mic_recorder_initialized(self, mic_recorder: MicRecorder):
        self._update_mic_transcription_message(ADJUSTING_FOR_NOISE_MESSAGE)

        self.mic_record_audio = mic_recorder
        self.mic_transcriber = SourceTranscriber(
            self.transcriber,
            mic_recorder.source.SAMPLE_RATE,
            mic_recorder.source.SAMPLE_WIDTH,
            mic_recorder.source.channels,
        )

        self._mic_adjuct_noise_thread = AdjustForNoiseTask(self.mic_record_audio)
        self._mic_adjuct_noise_thread.noise_adjusted.connect(
            self._on_mic_noise_adjusted
        )
        self._mic_adjuct_noise_thread.start()

    def _on_mic_noise_adjusted(self):
        if self.mic_enabled:
            self.mic_record_audio.record_into_queue(self.mic_audio_queue)

        if self._mic_init_audio_block:
            try:
                self._mic_init_audio_block.delete_self()
            except RuntimeError:
                pass

            self._mic_init_audio_block = None

        self.mic_transcribe_thread = threading.Thread(
            target=self.mic_transcriber.transcribe_audio_queue,
            args=(self.mic_audio_queue, self._handle_mic_transcript_update),
        )
        self.mic_transcribe_thread.daemon = True
        self.mic_transcribe_thread.start()
        self.mic_init_signal.emit()
        self.is_mic_init = True

        if self.is_first_init_attempt:
            QTimer.singleShot(1000, self._init_speaker_recorder)

    def _init_speaker_recorder(self, is_retry: bool = False):
        self._update_speaker_transcription_message(INIT_MESSAGE)

        self.speaker_init_thread = SpeakerInitTask()
        self.speaker_init_thread.initialized.connect(
            self._on_speaker_recorder_initialized
        )
        self.speaker_init_thread.error.connect(self._on_speaker_recorder_error)

        if is_retry:
            QTimer.singleShot(100, self.speaker_init_thread.start)
        else:
            self.speaker_init_thread.start()

    def _on_speaker_recorder_initialized(self, speaker_recorder: SpeakerRecorder):
        self._update_speaker_transcription_message(ADJUSTING_FOR_NOISE_MESSAGE)

        self.speaker_record_audio = speaker_recorder
        self.speaker_transcriber = SourceTranscriber(
            self.transcriber,
            speaker_recorder.source.SAMPLE_RATE,
            speaker_recorder.source.SAMPLE_WIDTH,
            speaker_recorder.source.channels,
        )

        self._speaker_adjuct_noise_thread = AdjustForNoiseTask(
            self.speaker_record_audio
        )
        self._speaker_adjuct_noise_thread.noise_adjusted.connect(
            self._on_speaker_noise_adjusted
        )
        self._speaker_adjuct_noise_thread.start()

    def _on_speaker_noise_adjusted(self):
        if self.speaker_enabled:
            self.speaker_record_audio.record_into_queue(self.speaker_audio_queue)

        if self._speaker_init_audio_block:
            try:
                self._speaker_init_audio_block.delete_self()
            except RuntimeError:
                pass

            self._speaker_init_audio_block = None

        self.speaker_transcribe_thread = threading.Thread(
            target=self.speaker_transcriber.transcribe_audio_queue,
            args=(self.speaker_audio_queue, self._handle_speaker_transcript_update),
        )
        self.speaker_transcribe_thread.daemon = True
        self.speaker_transcribe_thread.start()
        self.speaker_init_signal.emit()
        self.is_speaker_init = True

    def retry_mic_init(self):
        self.is_mic_init = False
        if self.mic_transcribe_thread:
            self.mic_transcriber.stop()

        self._init_mic_recorder(True)

    def retry_speaker_init(self):
        self.is_speaker_init = False
        if self.speaker_transcribe_thread:
            self.speaker_transcriber.stop()

        self._init_speaker_recorder(True)

    @Slot(str, bool, bool)
    def update_transcription(self, text: str, is_new_phrase: bool, is_mic: bool):
        source_type = AudioSourceType.MIC if is_mic else AudioSourceType.SPEAKER
        if is_new_phrase:
            self.transcription_list.add_transcription_block(source_type, text)
            return

        self.transcription_list.update_last_block_text(source_type, text)

    def _handle_mic_transcript_update(self, text: str, is_new_phrase: bool):
        QMetaObject.invokeMethod(
            self,
            "update_transcription",
            Qt.QueuedConnection,
            Q_ARG(str, text),
            Q_ARG(bool, is_new_phrase),
            Q_ARG(bool, True),
        )

    def _handle_speaker_transcript_update(self, text: str, is_new_phrase: bool):
        QMetaObject.invokeMethod(
            self,
            "update_transcription",
            Qt.QueuedConnection,
            Q_ARG(str, text),
            Q_ARG(bool, is_new_phrase),
            Q_ARG(bool, False),
        )

    @staticmethod
    def _change_stream_enabled(
        enabled: bool,
        stream: MicRecorder | SpeakerRecorder,
        queue: deque[Tuple[datetime, bytes]],
    ):
        if not enabled:
            stream.stop_recording()
            return

        if not stream.is_recording():
            stream.record_into_queue(queue)

    def set_mic_enabled(self, enabled: bool):
        if self.mic_enabled != enabled:
            self.mic_enabled = enabled
            self._change_stream_enabled(
                enabled, self.mic_record_audio, self.mic_audio_queue
            )

    def set_speaker_enabled(self, enabled: bool):
        if self.speaker_enabled != enabled:
            self.speaker_enabled = enabled
            self._change_stream_enabled(
                enabled, self.speaker_record_audio, self.speaker_audio_queue
            )

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

        formatted_text = ""
        for block in selected_blocks:
            formatted_text += f"[{block.source.value}]: {block.text}\n\n"

        formatted_text = formatted_text.rstrip()

        self.forward_signal.emit(formatted_text)
        self.transcription_list.deselect_all()
        self.select_button.setChecked(False)

    def get_messages(
        self, limit: Optional[int] = None
    ) -> List[Tuple[AudioSourceType, str]]:
        return self.transcription_list.get_messages(limit)

    def update_theme_ui(self):
        self.select_button.setIcon(get_icon(Icon.SELECT_ALL))
        self.delete_selected_button.setIcon(get_icon(Icon.DELETE))
        self.forward_button.setIcon(get_icon(Icon.SEND))
        self.transcription_list.update_theme_ui()
