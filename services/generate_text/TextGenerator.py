import lorem
from typing import TypedDict


class ChatCompletionMessageParam(TypedDict):
    content: str
    role: str


class BaseTextGenerator:
    def generate_text(self, messages: list[ChatCompletionMessageParam]) -> str:
        raise NotImplementedError("this is an abstract class")


class TestGenerator(BaseTextGenerator):
    def generate_text(self, messages: list[ChatCompletionMessageParam]) -> str:
        return lorem.sentence()
