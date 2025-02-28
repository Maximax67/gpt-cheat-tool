import io
import time
import wave

from collections import deque
from typing import Callable, Optional, Tuple
from datetime import datetime, timedelta
from services.transcribe.Transcriber import AbstractTranscriber


class SourceTranscriber:

    def __init__(
        self,
        transcriber: AbstractTranscriber,
        sample_rate: int,
        sample_width: int,
        channels: int,
        phrase_timeout: float = 5,
        max_phrase_length: float = 17,
    ):
        self.transcriber = transcriber
        self.sample_rate = sample_rate
        self.sample_width = sample_width
        self.channels = channels
        self.last_sample = bytes()
        self.first_spoken: Optional[datetime] = None
        self.last_spoken: Optional[datetime] = None
        self.new_phrase = True
        self.is_transcribing = False
        self.queue: deque[Tuple[datetime, bytes]] = deque()
        self.phrase_timeout = phrase_timeout
        self.max_phrase_length = max_phrase_length

    def transcribe_audio_queue(
        self,
        audio_queue: deque[Tuple[datetime, bytes]],
        callback: Callable[[str, bool], None],
    ):
        self.queue = audio_queue
        self.is_transcribing = True

        while self.is_transcribing:
            if not len(self.queue):
                time.sleep(0.01)
                continue

            data, time_spoken = self.queue.popleft()

            if self._is_same_phrase(time_spoken):
                self._continue_phrase(data, time_spoken)
            else:
                self._start_new_phrase(data, time_spoken)

            # Now, check if there are additional items for the same source that are still part of the same phrase.
            while len(self.queue):
                try:
                    next_item = self.queue.popleft()
                except Exception:
                    break

                next_data, next_time_spoken = next_item

                # Check whether it belongs to the same phrase.
                if self._is_same_phrase(next_time_spoken):
                    # Accumulate the data for the same phrase.
                    self._continue_phrase(next_data, next_time_spoken)
                else:
                    # New phrase detected – put the item back for later and stop accumulating.
                    self.queue.appendleft(next_item)
                    break

            # Now process the accumulated data for the current phrase.
            try:
                wav_buffer = self._convert_to_buffer(self.last_sample)
                text = self.transcriber.get_transcription(wav_buffer, "wav").strip()
            except Exception as e:
                print(e)
                text = ""

            if text and text.lower() not in ["you", "thank you.", "."]:
                callback(text, self.new_phrase)
            else:
                self.last_spoken = None

    def _is_same_phrase(self, time_spoken: datetime) -> bool:
        if self.last_spoken is None or self.first_spoken is None:
            return False

        if time_spoken - self.last_spoken > timedelta(seconds=self.phrase_timeout):
            return False

        if time_spoken - self.first_spoken > timedelta(seconds=self.max_phrase_length):
            return False

        return True

    def _start_new_phrase(self, data: bytes, time_spoken: datetime):
        self.new_phrase = True
        self.last_sample = data
        self.first_spoken = time_spoken
        self.last_spoken = time_spoken

    def _continue_phrase(self, data: bytes, time_spoken: datetime):
        self.new_phrase = False
        self.last_sample += data
        self.last_spoken = time_spoken

    def _convert_to_buffer(self, data: bytearray) -> io.BytesIO:
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.sample_width)
            wf.setframerate(self.sample_rate)
            wf.writeframes(data)

        wav_buffer.seek(0)

        return wav_buffer

    def stop(self):
        self.is_transcribing = False
        self.queue.clear()
