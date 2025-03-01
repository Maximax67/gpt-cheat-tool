from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Type, TypedDict, Callable, List

from services.groq import groq_client


class ChatMessageDict(TypedDict):
    content: str
    role: str


class AbstractTextGenerator(ABC):
    @abstractmethod
    def generate_text(
        self,
        chat_history: List[ChatMessageDict],
        callback: Callable[[str], None],
        completed_callback: Callable[[Optional[Exception]], None],
        model: Optional[str] = None,
    ) -> None:
        raise NotImplementedError("this is an abstract class")


class GroqTextGenerator(AbstractTextGenerator):

    def __init__(
        self,
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        stream=True,
        timeout=30.0,
        client=groq_client,
    ):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream
        self.timeout = timeout

    def generate_text(
        self,
        chat_history: List[ChatMessageDict],
        callback: Callable[[str], None],
        completed_callback: Callable[[bool], None],
        model: Optional[str] = None,
    ) -> None:
        try:
            if not model:
                model = self.model

            stream = self.client.chat.completions.create(
                messages=chat_history,
                model=model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=self.stream,
                reasoning_format="hidden",
                timeout=self.timeout,
            )

            for chunk in stream:
                text_chunk = chunk.choices[0].delta.content
                if text_chunk:
                    callback(text_chunk)
        except Exception as e:
            print(e)
            completed_callback(e)
        else:
            completed_callback(None)


class TextGeneratorProvider(Enum):
    GROQ = "Groq"


TEXT_GENERATORS: Dict[TextGeneratorProvider, Type[AbstractTextGenerator]] = {
    TextGeneratorProvider.GROQ: GroqTextGenerator,
}


def get_text_generator(
    generator_provider: TextGeneratorProvider, *args, **kwargs
) -> AbstractTextGenerator:
    generator_class = TEXT_GENERATORS.get(generator_provider)
    if not generator_class:
        raise ValueError(f"Unsupported text generator provider: {generator_provider}")

    return generator_class(*args, **kwargs)
