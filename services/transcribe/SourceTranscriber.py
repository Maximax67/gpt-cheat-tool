import wave
import threading
import io
from queue import Queue
from datetime import timedelta
from heapq import merge
from services.record_audio.AudioSourceTypes import AudioSourceTypes
from services.transcribe.Transcriber import BaseTranscriber
import services.record_audio.custom_speech_recognition as sr
import pyaudiowpatch as pyaudio

PHRASE_TIMEOUT = 3.05
MAX_PHRASES = 10


class SourceTranscriber:

    def __init__(
        self,
        mic_source: sr.Microphone,
        speaker_source: sr.Microphone,
        transcriber: BaseTranscriber,
    ):
        self.transcript_data = {AudioSourceTypes.MIC: [], AudioSourceTypes.SPEAKERS: []}
        self.transcript_changed_event = threading.Event()
        self.transcriber = transcriber
        self.audio_sources = {
            AudioSourceTypes.MIC: {
                "sample_rate": mic_source.SAMPLE_RATE,
                "sample_width": mic_source.SAMPLE_WIDTH,
                "channels": mic_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_mic_data,
            },
            AudioSourceTypes.SPEAKERS: {
                "sample_rate": speaker_source.SAMPLE_RATE,
                "sample_width": speaker_source.SAMPLE_WIDTH,
                "channels": speaker_source.channels,
                "last_sample": bytes(),
                "last_spoken": None,
                "new_phrase": True,
                "process_data_func": self.process_speaker_data,
            },
        }

    def transcribe_audio_queue(self, audio_queue: Queue):
        while True:
            source_type, data, time_spoken = audio_queue.get()
            self.update_last_sample_and_phrase_status(source_type, data, time_spoken)
            source_info = self.audio_sources[source_type]

            text = ""
            try:
                wav_buffer = source_info["process_data_func"](
                    source_info["last_sample"]
                )

                text = self.transcriber.get_transcription(wav_buffer)
            except Exception as e:
                print(e)

            if text != "" and text.lower() != "you":
                self.update_transcript(source_type, text, time_spoken)
                self.transcript_changed_event.set()

    def update_last_sample_and_phrase_status(self, source_type, data, time_spoken):
        source_info = self.audio_sources[source_type]
        if source_info["last_spoken"] and time_spoken - source_info[
            "last_spoken"
        ] > timedelta(seconds=PHRASE_TIMEOUT):
            source_info["last_sample"] = bytes()
            source_info["new_phrase"] = True
        else:
            source_info["new_phrase"] = False

        source_info["last_sample"] += data
        source_info["last_spoken"] = time_spoken

    def process_mic_data(self, data):
        audio_data = sr.AudioData(
            data,
            self.audio_sources[AudioSourceTypes.MIC]["sample_rate"],
            self.audio_sources[AudioSourceTypes.MIC]["sample_width"],
        )
        wav_buffer = io.BytesIO(audio_data.get_wav_data())
        wav_buffer.seek(0)

        return wav_buffer

    def process_speaker_data(self, data):
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(self.audio_sources[AudioSourceTypes.SPEAKERS]["channels"])
            p = pyaudio.PyAudio()
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.audio_sources[AudioSourceTypes.SPEAKERS]["sample_rate"])
            wf.writeframes(data)

        wav_buffer.seek(0)

        return wav_buffer

    def update_transcript(self, source_type: AudioSourceTypes, text, time_spoken):
        source_info = self.audio_sources[source_type]
        transcript = self.transcript_data[source_type]

        if source_info["new_phrase"] or len(transcript) == 0:
            if len(transcript) > MAX_PHRASES:
                transcript.pop(-1)
            transcript.insert(0, (f"{source_type.value}: [{text}]\n\n", time_spoken))
        else:
            transcript[0] = (f"{source_type.value}: [{text}]\n\n", time_spoken)

    def get_transcript(self):
        combined_transcript = list(
            merge(
                self.transcript_data[AudioSourceTypes.MIC],
                self.transcript_data[AudioSourceTypes.SPEAKERS],
                key=lambda x: x[1],
                reverse=True,
            )
        )
        combined_transcript = combined_transcript[:MAX_PHRASES]
        return "".join([t[0] for t in combined_transcript])

    def clear_transcript_data(self):
        self.transcript_data[AudioSourceTypes.MIC].clear()
        self.transcript_data[AudioSourceTypes.SPEAKERS].clear()

        self.audio_sources[AudioSourceTypes.MIC]["last_sample"] = bytes()
        self.audio_sources[AudioSourceTypes.SPEAKERS]["last_sample"] = bytes()

        self.audio_sources[AudioSourceTypes.MIC]["new_phrase"] = True
        self.audio_sources[AudioSourceTypes.SPEAKERS]["new_phrase"] = True
