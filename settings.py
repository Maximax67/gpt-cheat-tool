import os
from pydantic import BaseModel, ValidationError
from typing import ClassVar, Optional

from services.generate_text.TextGenerator import TextGeneratorProvider
from services.transcribe.Transcriber import TranscriberProvider
from ui.themes import Theme


class TextGeneratorSettings(BaseModel):
    provider: TextGeneratorProvider = TextGeneratorProvider.GROQ
    prompt: Optional[str] = None
    message_context: Optional[int] = 5
    model: str = "deepseek-r1-distill-llama-70b"
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stream: bool = True
    timeout: float = 30.0


class TranscriberSettings(BaseModel):
    provider: TranscriberProvider = TranscriberProvider.GROQ
    model: str = "whisper-large-v3-turbo"
    language: Optional[str] = None
    temperature: Optional[float] = None
    timeout: float = 30.0


class QuickAnswersSettings(BaseModel):
    default_message: str = "Welcome to the ChatGPT cheat tool!"
    text_generator: TextGeneratorSettings = TextGeneratorSettings()


class ChatSettings(BaseModel):
    text_generator: TextGeneratorSettings = TextGeneratorSettings()


class AudioDeviceMessageSettings(BaseModel):
    init_message: str = "[ Initializing ]"
    adjust_noise_message: str = "[ Adjusting for ambient noise ]"
    init_error: str = "Recorder init error: {}"


class AudioDeviceSettings(BaseModel):
    device_index: Optional[int] = None
    transcriber: TranscriberSettings = TranscriberSettings()
    phrase_timeout: float = 5.0
    max_phrase_length: float = 17.0
    record_timeout: float = 4.0
    energy_threshold: float = 1000.0
    dynamic_energy_threshold: bool = False
    messages: AudioDeviceMessageSettings = AudioDeviceMessageSettings()


class TranscriptionSettings(BaseModel):
    speaker: AudioDeviceSettings = AudioDeviceSettings()
    mic: AudioDeviceSettings = AudioDeviceSettings()


class AppSettings(BaseModel):
    chat: ChatSettings = ChatSettings()
    quick_answers: QuickAnswersSettings = QuickAnswersSettings()
    transcription: TranscriptionSettings = TranscriptionSettings()
    theme: Theme = Theme.AUTO

    default_settings_path: ClassVar[str] = "settings.json"

    def save(self, file_path: str = default_settings_path):
        with open(file_path, "w") as f:
            f.write(self.model_dump_json(indent=4))

    @staticmethod
    def reset(file_path: str = default_settings_path):
        default_settings = AppSettings()
        default_settings.save(file_path)

        return default_settings

    @classmethod
    def load(cls, file_path: str = default_settings_path):
        if not os.path.exists(file_path):
            default_settings = cls()
            default_settings.save(file_path)
            return default_settings

        with open(file_path, "r") as f:
            data = f.read()

        try:
            settings = cls.model_validate_json(data)
        except ValidationError as e:
            print("Invalid settings data:", e)
            settings = cls()
            settings.save(file_path)

        return settings
