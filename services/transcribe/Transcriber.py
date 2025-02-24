import lorem
from io import BytesIO
from abc import ABC, abstractmethod

from groq import Groq


class BaseTranscriber(ABC):
    @abstractmethod
    def get_transcription(self, buffer: BytesIO, file_extension: str) -> str:
        raise NotImplementedError("This is an abstract class")


class TestTranscriber(BaseTranscriber):

    def get_transcription(self, buffer: BytesIO, file_extension: str) -> str:
        return lorem.sentence()


class GroqTranscriber(BaseTranscriber):
    def __init__(self, client: Groq):
        self.client = client

    def get_transcription(self, buffer: BytesIO, file_extension: str) -> str:
        transcription = self.client.audio.transcriptions.create(
            file=(f"a.{file_extension}", buffer),
            model="whisper-large-v3-turbo",
        )

        return transcription.text
