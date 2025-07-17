from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class AutoCloseMessage(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet(
            "background-color: #f0f0f0; "
            "border: 1px solid #cccccc; "
            "border-radius: 5px;"
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)

    def show_message(self, message: str, duration: int = 1000) -> None:
        self.label.setText(message)
        self.adjustSize()
        self._center_on_parent()
        self.show()
        self.timer.start(duration)

    def _center_on_parent(self) -> None:
        parent = self.parent()
        if parent:
            geometry = parent.geometry()
            self.move(geometry.center() - self.rect().center())
