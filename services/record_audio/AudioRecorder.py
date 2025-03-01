import platform

from collections import deque
from datetime import datetime
from typing import Optional, Tuple

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
        pyaudio = sr.Microphone.get_pyaudio()
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
        pyaudio_instance = sr.Microphone.get_pyaudio()
        current_platform = platform.system()

        with pyaudio_instance.PyAudio() as p:
            device_index, device_name = self._select_device(
                p, current_platform, device_index
            )
            device_info = p.get_device_info_by_index(device_index)

        source = sr.Microphone(
            speaker=True,
            device_index=device_index,
            sample_rate=int(device_info["defaultSampleRate"]),
            chunk_size=pyaudio_instance.get_sample_size(pyaudio_instance.paInt16),
            channels=device_info["maxInputChannels"],
        )

        super().__init__(
            source,
            device_name,
            record_timeout,
            energy_threshold,
            dynamic_energy_threshold,
        )

    @staticmethod
    def _select_device(p, current_platform: str, device_index: Optional[int]):
        if current_platform == "Windows":
            return SpeakerRecorder._select_windows(p, device_index)
        elif current_platform == "Darwin":
            return SpeakerRecorder._select_darwin(p, device_index)
        elif current_platform == "Linux":
            return SpeakerRecorder._select_linux(p, device_index)
        else:
            raise RuntimeError(f"Unsupported platform: {current_platform}")

    @staticmethod
    def _select_windows(p, device_index: Optional[int]):
        pa = sr.Microphone.get_pyaudio()
        wasapi_info = p.get_host_api_info_by_type(pa.paWASAPI)
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

        return default_speakers["index"], default_speakers["name"]

    @staticmethod
    def _select_darwin(p, device_index: Optional[int]):
        predicate = (
            lambda info: "BlackHole" in info["name"] or "Soundflower" in info["name"]
        )
        if device_index is None:
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if predicate(info):
                    return info["index"], info["name"]
            raise RuntimeError(
                "No virtual loopback device found. Install BlackHole or Soundflower."
            )
        else:
            info = p.get_device_info_by_index(device_index)
            if predicate(info):
                return info["index"], info["name"]
            else:
                raise RuntimeError(
                    "Selected audio device is not a BlackHole or Soundflower source"
                )

    @staticmethod
    def _select_linux(p, device_index: Optional[int]):
        predicate = lambda info: "monitor" in info["name"].lower()
        if device_index is None:
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if predicate(info):
                    return info["index"], info["name"]
            raise RuntimeError(
                "No PulseAudio monitor source found. Run 'pactl list sources' to check."
            )
        else:
            info = p.get_device_info_by_index(device_index)
            if predicate(info):
                return info["index"], info["name"]
            else:
                raise RuntimeError(
                    "Selected audio device is not a PulseAudio monitor source"
                )
