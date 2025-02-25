import lorem
from random import randint
from abc import ABC, abstractmethod
from groq import Groq
from typing import TypedDict, Callable, List


class ChatCompletionMessageParam(TypedDict):
    content: str
    role: str


class BaseTextGenerator(ABC):
    @abstractmethod
    async def generate_text(
        self,
        messages: List[ChatCompletionMessageParam],
        callback: Callable[[str], None] = None,
    ) -> None:
        raise NotImplementedError("this is an abstract class")


class TestGenerator(BaseTextGenerator):

    async def generate_text(
        self,
        messages: List[ChatCompletionMessageParam],
        callback: Callable[[str], None],
    ) -> None:
        if not callback:
            raise ValueError("Callback function must be provided.")

        text = lorem.sentence()
        callback(text)

        for i in range(randint(0, 15)):
            text = " " + lorem.sentence()
            callback(text)


class GroqChatCompletion(BaseTextGenerator):

    def __init__(
        self,
        client: Groq,
        model: str,
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stream=True,
    ):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.stream = stream

    async def generate_text(
        self,
        messages: List[ChatCompletionMessageParam],
        callback: Callable[[str], None],
    ) -> None:
        if not callback:
            raise ValueError("Callback function must be provided.")

        stream = await self.client.chat.completions.create(
            messages,
            self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            stream=self.stream,
        )

        async for chunk in stream:
            callback(chunk.choices[0].delta.content)
