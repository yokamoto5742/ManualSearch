import logging
from typing import List, Optional, Tuple

from PyQt5.QtCore import QRegularExpression, Qt
from PyQt5.QtGui import (
    QColor,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from utils.constants import (
    HIGHLIGHT_COLORS,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    TEXT_VIEWER_DEFAULT_HEIGHT,
    TEXT_VIEWER_DEFAULT_WIDTH,
    TEXT_VIEWER_ZOOM_IN_LABEL,
    TEXT_VIEWER_ZOOM_OUT_LABEL,
)
from utils.constants.ui import DEFAULT_HTML_FONT_SIZE

logger = logging.getLogger(__name__)


class SearchHighlighter(QSyntaxHighlighter):
    """検索キーワードを背景色でハイライトするハイライタ"""

    def __init__(self, document: QTextDocument, search_terms: List[str]) -> None:
        super().__init__(document)
        self.rules: List[Tuple[QRegularExpression, QTextCharFormat]] = []

        for i, term in enumerate(search_terms):
            stripped = term.strip()
            if not stripped:
                continue

            fmt = QTextCharFormat()
            fmt.setBackground(QColor(HIGHLIGHT_COLORS[i % len(HIGHLIGHT_COLORS)]))

            regex = QRegularExpression(
                QRegularExpression.escape(stripped),
                QRegularExpression.CaseInsensitiveOption,
            )
            self.rules.append((regex, fmt))

    def highlightBlock(self, text: str) -> None:
        for regex, fmt in self.rules:
            iterator = regex.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class TextViewerWindow(QMainWindow):
    """アプリ内完結のテキスト・Markdownビューアウィンドウ"""

    def __init__(
        self,
        title: str,
        content: str,
        search_terms: List[str],
        font_size: int,
        is_markdown: bool = False,
        position: int = 0,
        width: int = TEXT_VIEWER_DEFAULT_WIDTH,
        height: int = TEXT_VIEWER_DEFAULT_HEIGHT,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)
        self.resize(width, height)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        layout.addLayout(self._create_control_bar())

        self.text_browser = QTextBrowser()
        self._apply_font_size(font_size)

        if is_markdown:
            self.text_browser.setMarkdown(content)
        else:
            self.text_browser.setPlainText(content)

        if search_terms:
            self.highlighter = SearchHighlighter(self.text_browser.document(), search_terms)

        layout.addWidget(self.text_browser)

        # Markdownは描画で行構造が変わるため、行ジャンプはプレーンテキストのみ
        if position > 0 and not is_markdown:
            self._scroll_to_line(position)

    def _create_control_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        zoom_in_button = QPushButton(TEXT_VIEWER_ZOOM_IN_LABEL)
        zoom_out_button = QPushButton(TEXT_VIEWER_ZOOM_OUT_LABEL)
        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button.clicked.connect(self.zoom_out)
        bar.addWidget(zoom_in_button)
        bar.addWidget(zoom_out_button)
        bar.addStretch()
        return bar

    def _apply_font_size(self, font_size: int) -> None:
        size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, font_size or DEFAULT_HTML_FONT_SIZE))
        font = self.text_browser.font()
        font.setPointSize(size)
        self.text_browser.setFont(font)

    def _scroll_to_line(self, line: int) -> None:
        """1始まりの行番号へカーソルを移動してスクロールする"""
        block = self.text_browser.document().findBlockByLineNumber(max(0, line - 1))
        cursor = QTextCursor(block)
        self.text_browser.setTextCursor(cursor)
        self.text_browser.ensureCursorVisible()

    def zoom_in(self) -> None:
        self.text_browser.zoomIn(1)

    def zoom_out(self) -> None:
        self.text_browser.zoomOut(1)
