from enum import Enum
from io import BytesIO
from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from services.groq import groq_client


class AbstractTranscriber(ABC):
    @abstractmethod
    def get_transcription(self, buffer: BytesIO, file_extension: str) -> str:
        raise NotImplementedError("This is an abstract class")


class GroqTranscriber(AbstractTranscriber):

    def __init__(
        self,
        model: str,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout=30.0,
        client=groq_client,
    ):
        self.client = client
        self.model = model
        self.language = language
        self.temperature = temperature
        self.timeout = timeout

    def get_transcription(
        self,
        buffer: BytesIO,
        file_extension: str,
    ) -> str:
        print("API REQUEST")
        transcription = self.client.audio.transcriptions.create(
            file=(f"a.{file_extension}", buffer),
            model=self.model,
            language=self.language,
            temperature=self.temperature,
            timeout=self.timeout,
        )
        print("API RESPONSE: ", transcription.text)

        return transcription.text


class TranscriberProvider(Enum):
    GROQ = "Groq"


TRANSCRIBERS: Dict[TranscriberProvider, Type[AbstractTranscriber]] = {
    TranscriberProvider.GROQ: GroqTranscriber,
}


def get_transcriber(
    transcriber_provider: TranscriberProvider, *args, **kwargs
) -> AbstractTranscriber:
    transcriber_class = TRANSCRIBERS.get(transcriber_provider)
    if not transcriber_class:
        raise ValueError(f"Unsupported transcriber provider: {transcriber_provider}")

    return transcriber_class(*args, **kwargs)
