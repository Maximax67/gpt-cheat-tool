import pyaudiowpatch as pyaudio

from collections import deque
from datetime import datetime
from typing import Tuple

import services.record_audio.custom_speech_recognition as sr
from services.record_audio.AudioSourceType import AudioSourceType


class BaseRecorder:
    source_type = None

    def __init__(
        self,
        source: sr.Microphone,
        device_name: str,
        record_timeout: float = 4,
        energy_threshold: float = 1000,
        dynamic_energy_threshold: bool = False,
    ):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = energy_threshold
        self.recorder.dynamic_energy_threshold = dynamic_energy_threshold
        self.device_name = device_name
        self.record_timeout = record_timeout

        if source is None:
            raise ValueError("audio source can't be None")

        self.source = source
        self.stopper = None

    def adjust_for_noise(self):
        print(f"[INFO] Adjusting for ambient noise from {self.device_name}.")

        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)

        print(f"[INFO] Completed ambient noise adjustment for {self.device_name}.")

    def record_into_queue(self, audio_queue: deque[Tuple[datetime, bytes]]):
        def record_callback(_, audio: sr.AudioData) -> None:
            data = audio.get_raw_data()
            audio_queue.append((data, datetime.now()))

        self.stopper = self.recorder.listen_in_background(
            self.source, record_callback, phrase_time_limit=self.record_timeout
        )

    def stop_recording(self):
        if self.stopper:
            self.stopper(wait_for_stop=True, callback_last_audio_chunk=True)
            self.stopper = None

            return True

        return False

    def is_recording(self):
        return bool(self.stopper)


class MicRecorder(BaseRecorder):
    source_type = AudioSourceType.MIC

    def __init__(
        self,
        device_index=None,
        record_timeout: float = 4,
        energy_threshold: float = 1000,
        dynamic_energy_threshold: bool = False,
    ):
        with pyaudio.PyAudio() as p:
            if device_index is None:
                device_index = p.get_default_input_device_info()["index"]
                device_name = p.get_default_input_device_info()["name"]
            else:
                device_name = p.get_device_info_by_index(device_index)["name"]

        source = sr.Microphone(device_index=device_index, sample_rate=16000)
        super().__init__(
            source,
            device_name,
            record_timeout,
            energy_threshold,
            dynamic_energy_threshold,
        )


class SpeakerRecorder(BaseRecorder):
    source_type = AudioSourceType.SPEAKER

    def __init__(
        self,
        device_index=None,
        record_timeout: float = 4,
        energy_threshold: float = 1000,
        dynamic_energy_threshold: bool = False,
    ):
        with pyaudio.PyAudio() as p:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = (
                p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
                if device_index is None
                else p.get_device_info_by_index(device_index)
            )

            if not default_speakers.get("isLoopbackDevice", False):
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    raise RuntimeError("No loopback device found.")

            device_index = default_speakers["index"]
            device_name = default_speakers["name"]

        source = sr.Microphone(
            speaker=True,
            device_index=device_index,
            sample_rate=int(default_speakers["defaultSampleRate"]),
            chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
            channels=default_speakers["maxInputChannels"],
        )
        super().__init__(
            source,
            device_name,
            record_timeout,
            energy_threshold,
            dynamic_energy_threshold,
        )
