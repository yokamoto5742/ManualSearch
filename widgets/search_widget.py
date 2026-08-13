import logging
import re
from typing import List

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QWidget
)

from utils.config_manager import ConfigManager
from utils.constants import (
    SEARCH_TERM_SEPARATOR_PATTERN, SEARCH_TYPE_AND, SEARCH_TYPE_OR, UI_LABELS
)
from widgets.directory_management_widget import DirectoryManagementDialog

logger = logging.getLogger(__name__)


class SearchWidget(QWidget):
    """検索入力と検索オプション（検索フォルダ設定を含む）のUI"""

    search_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    open_folder_requested = pyqtSignal()

    def __init__(self, config_manager: 'ConfigManager') -> None:
        """初期化

        Args:
            config_manager: 設定マネージャーインスタンス
        """
        super().__init__()
        self.config_manager = config_manager
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        search_layout = self._create_search_layout()
        layout.addLayout(search_layout)

        options_layout = self._create_options_layout()
        layout.addLayout(options_layout)

    def _create_search_layout(self) -> QHBoxLayout:
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(UI_LABELS['SEARCH_PLACEHOLDER'])
        self.search_input.returnPressed.connect(self.search_requested.emit)

        search_button = QPushButton(UI_LABELS['SEARCH_BUTTON'])
        search_button.clicked.connect(self.search_requested.emit)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        return search_layout

    def _create_options_layout(self) -> QHBoxLayout:
        options_layout = QHBoxLayout()

        self.search_type_combo = self._create_search_type_combo()
        options_layout.addWidget(self.search_type_combo)

        settings_button = QPushButton(UI_LABELS['FOLDER_SETTINGS'])
        settings_button.clicked.connect(self.open_directory_settings)
        options_layout.addWidget(settings_button)

        self.include_subdirs_checkbox = QCheckBox(UI_LABELS['INCLUDE_SUBDIRS'])
        self.include_subdirs_checkbox.setChecked(True)
        options_layout.addWidget(self.include_subdirs_checkbox)

        options_layout.addStretch()

        self.open_folder_button = QPushButton(UI_LABELS['OPEN_FOLDER'])
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)
        self.open_folder_button.setEnabled(False)
        options_layout.addWidget(self.open_folder_button)

        clear_button = QPushButton(UI_LABELS['CLEAR_BUTTON'])
        clear_button.clicked.connect(self.clear_requested.emit)
        options_layout.addWidget(clear_button)

        return options_layout

    @staticmethod
    def _create_search_type_combo() -> QComboBox:
        search_type_combo = QComboBox()
        search_type_combo.addItems([
            UI_LABELS['AND_SEARCH_LABEL'],
            UI_LABELS['OR_SEARCH_LABEL']
        ])
        return search_type_combo


    def get_search_terms(self) -> List[str]:
        """検索語を取得

        Returns:
            検索語リスト
        """
        try:
            return [
                term.strip()
                for term in re.split(SEARCH_TERM_SEPARATOR_PATTERN, self.search_input.text())
                if term.strip()
            ]
        except re.error as e:
            logger.error(f"正規表現エラー: {e}")
            return []
        except AttributeError:
            logger.error("検索入力フィールドが正しく初期化されていません")
            return []

    def get_search_type(self) -> str:
        """検索タイプを取得

        Returns:
            検索タイプ（AND/OR）
        """
        try:
            return SEARCH_TYPE_AND if self.search_type_combo.currentText().startswith("AND") else SEARCH_TYPE_OR
        except AttributeError:
            logger.error("検索タイプコンボボックスが正しく初期化されていません")
            return SEARCH_TYPE_AND

    def clear_input(self) -> None:
        """検索入力をクリア"""
        self.search_input.clear()

    def open_directory_settings(self) -> None:
        """検索フォルダ設定ダイアログを表示"""
        DirectoryManagementDialog(self.config_manager, self).exec_()

    def include_subdirs(self) -> bool:
        """サブディレクトリを含むかを取得

        Returns:
            含む場合True
        """
        return self.include_subdirs_checkbox.isChecked()

    def enable_open_folder_button(self) -> None:
        """フォルダ開くボタンを有効にする"""
        self.open_folder_button.setEnabled(True)

    def disable_open_folder_button(self) -> None:
        """フォルダ開くボタンを無効にする"""
        self.open_folder_button.setEnabled(False)

