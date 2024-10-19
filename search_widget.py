from typing import List
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
)
import re


class SearchWidget(QWidget):
    search_requested = pyqtSignal()

    def __init__(self, config_manager: object) -> None:
        super().__init__()
        self.config_manager = config_manager
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        search_layout = self._create_search_layout()
        layout.addLayout(search_layout)

        self.search_type_combo = self._create_search_type_combo()
        layout.addWidget(self.search_type_combo)

    def _create_search_layout(self) -> QHBoxLayout:
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索語を入力 ( , または 、区切りで複数語検索)")
        self.search_input.returnPressed.connect(self.search_requested.emit)

        search_button = QPushButton("検索")
        search_button.clicked.connect(self.search_requested.emit)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        return search_layout

    @staticmethod
    def _create_search_type_combo() -> QComboBox:
        search_type_combo = QComboBox()
        search_type_combo.addItems([
            "AND検索(1ページに複数の検索語をすべて含む)",
            "OR検索(1ページに複数の検索語のいずれかを含む)"
        ])
        return search_type_combo

    def get_search_terms(self) -> List[str]:
        try:
            return [
                term.strip()
                for term in re.split('[,、]', self.search_input.text()) # 複数の区切り文字を一括処理
                if term.strip()
            ]
        except re.error as e:
            print(f"正規表現エラー: {e}")
            return []
        except AttributeError:
            print("検索入力フィールドが正しく初期化されていません")
            return []

    def get_search_type(self) -> str:
        try:
            return 'AND' if self.search_type_combo.currentText().startswith("AND") else 'OR'
        except AttributeError:
            print("検索タイプコンボボックスが正しく初期化されていません")
            return 'AND'
