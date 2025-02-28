from abc import ABC, abstractmethod
from groq import Groq
from typing import Optional, TypedDict, Callable, List


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
        client: Groq,
        default_model: str,
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stream=True,
    ):
        self.client = client
        self.default_model = default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream

    def generate_text(
        self,
        chat_history: List[ChatMessageDict],
        callback: Callable[[str], None],
        completed_callback: Callable[[bool], None],
        model: Optional[str] = None,
    ) -> None:
        try:
            if not model:
                model = self.default_model

            stream = self.client.chat.completions.create(
                messages=chat_history,
                model=model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=self.stream,
                reasoning_format="hidden",
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
