from io import BytesIO
from abc import ABC, abstractmethod

from groq import Groq


class AbstractTranscriber(ABC):
    @abstractmethod
    def get_transcription(self, buffer: BytesIO, file_extension: str) -> str:
        raise NotImplementedError("This is an abstract class")


class GroqTranscriber(AbstractTranscriber):

    def __init__(self, client: Groq, model: str):
        self.client = client
        self.model = model

    def get_transcription(self, buffer: BytesIO, file_extension: str) -> str:
        print("API REQUEST")
        transcription = self.client.audio.transcriptions.create(
            file=(f"a.{file_extension}", buffer),
            model=self.model,
        )
        print("API RESPONSE: ", transcription.text)

        return transcription.text
