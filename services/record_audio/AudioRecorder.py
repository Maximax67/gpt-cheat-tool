from queue import Queue
from datetime import datetime
import pyaudiowpatch as pyaudio

import services.record_audio.custom_speech_recognition as sr
from services.record_audio.AudioSourceTypes import AudioSourceTypes

RECORD_TIMEOUT = 4
ENERGY_THRESHOLD = 1000
DYNAMIC_ENERGY_THRESHOLD = False


class BaseRecorder:
    source_type = None

    def __init__(self, source):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = ENERGY_THRESHOLD
        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

        if source is None:
            raise ValueError("audio source can't be None")

        self.source = source

    def adjust_for_noise(self, device_name, msg):
        print(f"[INFO] Adjusting for ambient noise from {device_name}. " + msg)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print(f"[INFO] Completed ambient noise adjustment for {device_name}.")

    def record_into_queue(self, audio_queue: Queue):
        def record_callback(_, audio: sr.AudioData) -> None:
            data = audio.get_raw_data()
            audio_queue.put((self.source_type, data, datetime.now()))

        self.stopper = self.recorder.listen_in_background(
            self.source, record_callback, phrase_time_limit=RECORD_TIMEOUT
        )

    def stop_recording(self):
        if self.stopper:
            self.stopper(wait_for_stop=False, callback_last_audio_chunk=True)
            self.stopper = None

            return True

        return False

    def is_recording(self):
        return bool(self.stopper)


class MicRecorder(BaseRecorder):
    source_type = AudioSourceTypes.MIC

    def __init__(self, device_index=None):
        with pyaudio.PyAudio() as p:
            if device_index is None:
                device_index = p.get_default_input_device_info()["index"]
                device_name = p.get_default_input_device_info()["name"]
            else:
                device_name = p.get_device_info_by_index(device_index)["name"]

        super().__init__(sr.Microphone(device_index=device_index, sample_rate=16000))
        self.adjust_for_noise(
            device_name, f"Please make some noise from {device_name}..."
        )


class SpeakerRecorder(BaseRecorder):
    source_type = AudioSourceTypes.SPEAKER

    def __init__(self, device_index=None):
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
        super().__init__(source)
        self.adjust_for_noise(
            device_name, f"Please make or play some noise from {device_name}..."
        )
