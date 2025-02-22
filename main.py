import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

import time
import queue
import threading

from services.transcribe.SourceTranscriber import SourceTranscriber
from services.record_audio.AudioRecorder import MicRecorder, SpeakerRecorder
from services.transcribe.Transcriber import TestTranscriber

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

    audio_queue = queue.Queue()
    user_record_audio = MicRecorder()
    user_record_audio.record_into_queue(audio_queue)

    time.sleep(2)

    speaker_record_audio = SpeakerRecorder()
    speaker_record_audio.record_into_queue(audio_queue)

    model = TestTranscriber()

    transcriber = SourceTranscriber(
        user_record_audio.source, speaker_record_audio.source, model
    )
    transcribe = threading.Thread(
        target=transcriber.transcribe_audio_queue, args=(audio_queue,)
    )
    transcribe.daemon = True
    transcribe.start()

    print("READY")

    for _ in range(20):
        time.sleep(2)
        print(transcriber.get_transcript())
