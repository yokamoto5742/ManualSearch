from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QComboBox
import re

class SearchWidget(QWidget):
    search_requested = pyqtSignal()

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 検索入力とボタン
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索語を入力 ( , または 、区切りで複数語検索)")
        self.search_input.returnPressed.connect(self.search_requested.emit)
        search_button = QPushButton("検索")
        search_button.clicked.connect(self.search_requested.emit)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # 検索タイプ選択
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["AND検索(複数語のすべてを含む)", "OR検索(複数語のいずれかを含む)"])
        layout.addWidget(self.search_type_combo)

    def get_search_terms(self):
        return [term.strip() for term in re.split('[,、]', self.search_input.text()) if term.strip()]

    def get_search_type(self):
        return 'AND' if self.search_type_combo.currentText().startswith("AND") else 'OR'
