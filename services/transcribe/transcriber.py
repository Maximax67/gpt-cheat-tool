from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, Optional, Type
from groq import Groq

from services.groq import GroqClientSingleton


class AbstractTranscriber(ABC):
    @abstractmethod
    def get_transcription(self, buffer: bytes, file_extension: str) -> str:
        raise NotImplementedError("This is an abstract class")


class GroqTranscriber(AbstractTranscriber):

    def __init__(
        self,
        model: str,
        language: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout=30.0,
        client: Optional[Groq] = None,
    ):
        if client is None:
            client = GroqClientSingleton.get_instance()

        self.client = client
        self.model = model
        self.language = language
        self.temperature = temperature
        self.timeout = timeout

    def get_transcription(
        self,
        buffer: bytes,
        file_extension: str,
    ) -> str:
        transcription = self.client.audio.transcriptions.create(
            file=(f"a.{file_extension}", buffer),
            model=self.model,
            language=self.language,
            temperature=self.temperature,
            timeout=self.timeout,
        )

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
