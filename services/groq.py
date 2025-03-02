import os
from typing import Optional
from groq import Groq


class GroqClientSingleton:
    _instance: Optional[Groq] = None

    @staticmethod
    def get_instance() -> Groq:
        if GroqClientSingleton._instance is None:
            api_key = os.environ.get("GROQ_API_KEY")
            GroqClientSingleton._instance = Groq(api_key=api_key)

        return GroqClientSingleton._instance
