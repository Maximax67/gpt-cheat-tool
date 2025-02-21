from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from widgets.chat_panel import ChatPanel
from widgets.transcription_panel import TranscriptionPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Groq Audio Transcription & Chat")
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel: Chat UI
        self.chat_panel = ChatPanel()
        splitter.addWidget(self.chat_panel)

        # Right panel: Transcription panel
        self.transcription_panel = TranscriptionPanel()
        splitter.addWidget(self.transcription_panel)

        # Set initial sizes (adjust as needed)
        splitter.setSizes([600, 400])

        # Connect the transcription panel's forward signal to a slot here.
        self.transcription_panel.forwardSignal.connect(
            self.forward_transcription_to_chat
        )

    def forward_transcription_to_chat(self, text):
        """
        When transcription blocks are forwarded, if the chat prompt field is nonempty,
        prepend its text to the transcription text.
        """
        prompt_text = self.chat_panel.get_prompt_text()
        if prompt_text:
            full_text = prompt_text + "\n" + text
        else:
            full_text = text

        self.chat_panel.send_message(full_text)
        self.chat_panel.clear_prompt()
