import threading

from collections import deque
from datetime import datetime
from typing import List, Optional, Tuple

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, QMetaObject, Qt, Q_ARG, Slot, QThread, QTimer

from services.record_audio.audio_source_type import AudioSourceType
from services.transcribe.source_transcriber import SourceTranscriber
from services.record_audio.audio_recorder import (
    BaseRecorder,
    MicRecorder,
    SpeakerRecorder,
)
from services.transcribe.transcriber import get_transcriber

from settings import TranscriptionSettings
from widgets.transcription_list import SelectionStates, TranscriptionListWidget
from ui.icons import Icon, get_icon


class MicInitTask(QThread):
    initialized = Signal(MicRecorder)
    error = Signal(str)

    def __init__(
        self,
        device_index=None,
        record_timeout=4.0,
        energy_threshold=1000.0,
        dynamic_energy_threshold=False,
        parent=None,
    ):
        super().__init__(parent)
        self.device_index = device_index
        self.record_timeout = record_timeout
        self.energy_threshold = energy_threshold
        self.dynamic_energy_threshold = dynamic_energy_threshold

    def run(self):
        try:
            mic = MicRecorder(
                self.device_index,
                self.record_timeout,
                self.energy_threshold,
                self.dynamic_energy_threshold,
            )
            self.initialized.emit(mic)
        except Exception as e:
            print(e)
            self.error.emit(str(e))


class SpeakerInitTask(QThread):
    initialized = Signal(SpeakerRecorder)
    error = Signal(str)

    def __init__(
        self,
        device_index=None,
        record_timeout=4.0,
        energy_threshold=1000.0,
        dynamic_energy_threshold=False,
        parent=None,
    ):
        super().__init__(parent)
        self.device_index = device_index
        self.record_timeout = record_timeout
        self.energy_threshold = energy_threshold
        self.dynamic_energy_threshold = dynamic_energy_threshold

    def run(self):
        try:
            speaker = SpeakerRecorder(
                self.device_index,
                self.record_timeout,
                self.energy_threshold,
                self.dynamic_energy_threshold,
            )
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
            print(e)
            self.error.emit(str(e))


class TranscriptionPanel(QWidget):
    forward_signal = Signal(str)

    mic_init_signal = Signal()
    speaker_init_signal = Signal()

    mic_recorder_error = Signal()
    speaker_recorder_error = Signal()

    def __init__(self, settings: TranscriptionSettings):
        super().__init__()

        self.settings = settings

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

        mic_transcriber_settings = self.settings.mic.transcriber
        speaker_transcriber_settings = self.settings.speaker.transcriber

        self.mic_transcriber = get_transcriber(
            mic_transcriber_settings.provider,
            model=mic_transcriber_settings.model,
            language=mic_transcriber_settings.language,
            temperature=mic_transcriber_settings.temperature,
            timeout=mic_transcriber_settings.timeout,
        )
        self.speaker_transcriber = get_transcriber(
            speaker_transcriber_settings.provider,
            model=speaker_transcriber_settings.model,
            language=speaker_transcriber_settings.language,
            temperature=speaker_transcriber_settings.temperature,
            timeout=speaker_transcriber_settings.timeout,
        )

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
        self._update_mic_transcription_message(
            self.settings.mic.messages.init_error.format(error)
        )

        if self.is_first_init_attempt:
            self.is_first_init_attempt = False
            self._init_speaker_recorder()

    def _on_speaker_recorder_error(self, error: str):
        self.speaker_recorder_error.emit()
        self._update_speaker_transcription_message(
            self.settings.speaker.messages.init_error.format(error)
        )

        if self.is_first_init_attempt:
            self.is_first_init_attempt = False

    def _init_mic_recorder(self, is_retry: bool = False):
        mic_settings = self.settings.mic

        self._update_mic_transcription_message(mic_settings.messages.init_message)

        self.mic_init_thread = MicInitTask(
            mic_settings.device_index,
            mic_settings.record_timeout,
            mic_settings.energy_threshold,
            mic_settings.dynamic_energy_threshold,
        )
        self.mic_init_thread.initialized.connect(self._on_mic_recorder_initialized)
        self.mic_init_thread.error.connect(self._on_mic_recorder_error)

        if is_retry:
            QTimer.singleShot(100, self.mic_init_thread.start)
        else:
            self.mic_init_thread.start()

    def _on_mic_recorder_initialized(self, mic_recorder: MicRecorder):
        self._update_mic_transcription_message(
            self.settings.mic.messages.adjust_noise_message
        )

        self.mic_record_audio = mic_recorder
        self.mic_transcriber = SourceTranscriber(
            self.mic_transcriber,
            mic_recorder.source.SAMPLE_RATE,
            mic_recorder.source.SAMPLE_WIDTH,
            mic_recorder.source.channels,
            self.settings.mic.phrase_timeout,
            self.settings.mic.max_phrase_length,
        )

        self._mic_adjuct_noise_thread = AdjustForNoiseTask(self.mic_record_audio)
        self._mic_adjuct_noise_thread.noise_adjusted.connect(
            self._on_mic_noise_adjusted
        )
        self._mic_adjuct_noise_thread.error.connect(self._on_mic_recorder_error)
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
            self.is_first_init_attempt = False
            QTimer.singleShot(1000, self._init_speaker_recorder)

    def _init_speaker_recorder(self, is_retry: bool = False):
        speaker_settings = self.settings.speaker

        self._update_speaker_transcription_message(
            speaker_settings.messages.init_message
        )

        self.speaker_init_thread = SpeakerInitTask(
            speaker_settings.device_index,
            speaker_settings.record_timeout,
            speaker_settings.energy_threshold,
            speaker_settings.dynamic_energy_threshold,
        )
        self.speaker_init_thread.initialized.connect(
            self._on_speaker_recorder_initialized
        )
        self.speaker_init_thread.error.connect(self._on_speaker_recorder_error)

        if is_retry:
            QTimer.singleShot(100, self.speaker_init_thread.start)
        else:
            self.speaker_init_thread.start()

    def _on_speaker_recorder_initialized(self, speaker_recorder: SpeakerRecorder):
        self._update_speaker_transcription_message(
            self.settings.speaker.messages.adjust_noise_message
        )

        self.speaker_record_audio = speaker_recorder
        self.speaker_transcriber = SourceTranscriber(
            self.speaker_transcriber,
            speaker_recorder.source.SAMPLE_RATE,
            speaker_recorder.source.SAMPLE_WIDTH,
            speaker_recorder.source.channels,
            self.settings.speaker.phrase_timeout,
            self.settings.speaker.max_phrase_length,
        )

        self._speaker_adjuct_noise_thread = AdjustForNoiseTask(
            self.speaker_record_audio
        )
        self._speaker_adjuct_noise_thread.noise_adjusted.connect(
            self._on_speaker_noise_adjusted
        )
        self._speaker_adjuct_noise_thread.error.connect(self._on_speaker_recorder_error)
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
