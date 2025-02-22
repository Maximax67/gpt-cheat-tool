import lorem
from io import BytesIO


class BaseTranscriber:
    def get_transcription(self, buffer: BytesIO):
        raise NotImplementedError("this is an abstract class")


class TestTranscriber(BaseTranscriber):
    def get_transcription(self, buffer: BytesIO):
        return lorem.sentence()
