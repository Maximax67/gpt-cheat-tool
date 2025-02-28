import os
from pydantic import BaseModel, ValidationError
from typing import Optional
from ui.themes import Theme


class TextGeneratorSettings(BaseModel):
    prompt: Optional[str] = None
    message_context: Optional[int] = 5
    model: str = "deepseek-r1-distill-llama-70b"
    temperature: float = 0.5
    max_tokens: int = 1024
    top_p: float = 1
    stream: bool = True


class QuickAnswersSettings(BaseModel):
    default_message: str = "Welcome to ChatGPT cheat tool!"
    text_generator: TextGeneratorSettings = TextGeneratorSettings()


class ChatSettings(BaseModel):
    text_generator: TextGeneratorSettings = TextGeneratorSettings()


class AudioDeviceMessageSettings(BaseModel):
    init_message: str = "[ Initializing ]"
    adjust_noise_message: str = "[ Adjusting for ambient noise ]"
    init_error: str = "Recorder init error: {}"


class AudioDeviceSettings(BaseModel):
    device_index: Optional[int] = None
    model: str = "whisper-large-v3-turbo"
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

    def save(self, file_path: str = "settings.json"):
        with open(file_path, "w") as f:
            f.write(self.model_dump_json(indent=4))

    @classmethod
    def load(cls, file_path: str = "settings.json"):
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
