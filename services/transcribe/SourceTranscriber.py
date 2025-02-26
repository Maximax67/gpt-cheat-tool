from typing import Callable
import wave
import io
from queue import Queue
from datetime import timedelta
from services.record_audio.AudioSourceType import AudioSourceType
from services.transcribe.Transcriber import AbstractTranscriber
import services.record_audio.custom_speech_recognition as sr
import pyaudiowpatch as pyaudio

PHRASE_TIMEOUT = 5
MAX_PHRASE_LENGTH = 17


class SourceTranscriber:

    def __init__(
        self,
        mic_source: sr.Microphone,
        speaker_source: sr.Microphone,
        transcriber: AbstractTranscriber,
    ):
        self.transcriber = transcriber
        self.audio_sources = {
            AudioSourceType.MIC: {
                "sample_rate": mic_source.SAMPLE_RATE,
                "sample_width": mic_source.SAMPLE_WIDTH,
                "channels": mic_source.channels,
                "last_sample": bytes(),
                "first_spoken": None,
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_mic_data,
            },
            AudioSourceType.SPEAKER: {
                "sample_rate": speaker_source.SAMPLE_RATE,
                "sample_width": speaker_source.SAMPLE_WIDTH,
                "channels": speaker_source.channels,
                "last_sample": bytes(),
                "first_spoken": None,
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_speaker_data,
            },
        }

    def transcribe_audio_queue(
        self,
        audio_queue: Queue,
        callback: Callable[[AudioSourceType, str, bool], None],
    ):
        while True:
            source_type, data, time_spoken = audio_queue.get()
            self.update_last_sample_and_phrase_status(source_type, data, time_spoken)
            source_info = self.audio_sources[source_type]

            text = ""
            try:
                wav_buffer = source_info["process_data_func"](
                    source_info["last_sample"]
                )

                text = self.transcriber.get_transcription(wav_buffer, "wav").strip()
            except Exception as e:
                print(e)

            if text != "" and text.lower() != "you" and text.lower() != "thank you.":
                self.update_transcript(source_type, text, callback)

    def update_last_sample_and_phrase_status(self, source_type, data, time_spoken):
        source_info = self.audio_sources[source_type]
        last_spoken = source_info["last_spoken"]
        first_spoken = source_info["first_spoken"]

        if not first_spoken:
            first_spoken = last_spoken
            source_info["first_spoken"] = last_spoken

        if last_spoken and first_spoken:
            print(time_spoken - first_spoken)
            print(time_spoken - first_spoken < timedelta(seconds=MAX_PHRASE_LENGTH))

        if (
            not last_spoken
            or not first_spoken
            or (
                time_spoken - last_spoken > timedelta(seconds=PHRASE_TIMEOUT)
                or time_spoken - first_spoken > timedelta(seconds=MAX_PHRASE_LENGTH)
            )
        ):
            print("NEW PHRASE")
            source_info["last_sample"] = bytes()
            source_info["new_phrase"] = True
            source_info["first_spoken"] = time_spoken
        else:
            print("UPDATE OLD PHRASE")
            source_info["new_phrase"] = False

        source_info["last_sample"] += data
        source_info["last_spoken"] = time_spoken

    def process_mic_data(self, data):
        audio_data = sr.AudioData(
            data,
            self.audio_sources[AudioSourceType.MIC]["sample_rate"],
            self.audio_sources[AudioSourceType.MIC]["sample_width"],
        )
        wav_buffer = io.BytesIO(audio_data.get_wav_data())
        wav_buffer.seek(0)

        return wav_buffer

    def process_speaker_data(self, data):
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(self.audio_sources[AudioSourceType.SPEAKER]["channels"])
            p = pyaudio.PyAudio()
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.audio_sources[AudioSourceType.SPEAKER]["sample_rate"])
            wf.writeframes(data)

        wav_buffer.seek(0)

        return wav_buffer

    def update_transcript(
        self,
        source_type: AudioSourceType,
        text: str,
        callback: Callable[[AudioSourceType, str, bool], None],
    ):
        source_info = self.audio_sources[source_type]

        if source_info["new_phrase"]:
            print("NEW TRANSCRIPT BLOCK: ", text)
            callback(source_type, text, True)
        else:
            print("UPDATE TRANSCRIPT: ", text)
            callback(source_type, text, False)
