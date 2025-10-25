from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget

from utils.constants import STYLESHEETS


class AutoCloseMessage(QWidget):
    """指定時間後に自動的に閉じるメッセージウィジェット"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """初期化

        親ウィジェットを指定して、常に手前に表示されるウィンドウを作成
        """
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet(STYLESHEETS['AUTO_CLOSE_MESSAGE'])
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIコンポーネントを初期化"""
        layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        # 自動クローズタイマーを設定
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)

    def show_message(self, message: str, duration: int = 1000) -> None:
        """メッセージを表示して自動クローズをスケジュール

        Args:
            message: 表示するメッセージテキスト
            duration: 表示時間（ミリ秒）デフォルト1000ms
        """
        self.label.setText(message)
        self.adjustSize()
        self._center_on_parent()
        self.show()
        self.timer.start(duration)

    def _center_on_parent(self) -> None:
        """親ウィジェットの中央にウィンドウを配置"""
        parent = self.parent()
        if parent and isinstance(parent, QWidget):
            geometry = parent.geometry()
            self.move(geometry.center() - self.rect().center())
