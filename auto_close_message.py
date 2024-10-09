from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer


class AutoCloseMessage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 5px;
        """)
        self.layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)

    def show_message(self, message: str, duration: int = 1000):
        self.label.setText(message)
        self.adjustSize()
        parent = self.parent()
        if parent:
            geometry = parent.geometry()
            self.move(geometry.center() - self.rect().center())
        self.show()
        self.timer.start(duration)
