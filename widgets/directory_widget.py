from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QWidget

from utils.config_manager import ConfigManager
from utils.constants import UI_LABELS
from widgets.directory_management_widget import DirectoryManagementDialog


class DirectoryWidget(QWidget):
    """検索対象フォルダの状態表示と検索オプションを扱うウィジェット"""

    # フォルダを開くリクエストシグナル
    open_folder_requested = pyqtSignal()

    def __init__(self, config_manager: 'ConfigManager') -> None:
        """初期化

        Args:
            config_manager: 設定管理オブジェクト
        """
        super().__init__()
        self.config_manager = config_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIレイアウトを構築"""
        layout = QHBoxLayout()
        self.setLayout(layout)

        settings_button = QPushButton(UI_LABELS['FOLDER_SETTINGS'])
        settings_button.clicked.connect(self.open_directory_settings)

        self.include_subdirs_checkbox = QCheckBox(UI_LABELS['INCLUDE_SUBDIRS'])
        self.include_subdirs_checkbox.setChecked(True)

        self.open_folder_button = QPushButton(UI_LABELS['OPEN_FOLDER'])
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)
        self.open_folder_button.setEnabled(False)

        layout.addWidget(settings_button)
        layout.addWidget(self.include_subdirs_checkbox)
        layout.addStretch(1)
        layout.addWidget(self.open_folder_button)

    def open_directory_settings(self) -> None:
        """検索フォルダ設定ダイアログを表示"""
        DirectoryManagementDialog(self.config_manager, self).exec_()

    def enable_open_folder_button(self) -> None:
        """フォルダ開くボタンを有効にする"""
        self.open_folder_button.setEnabled(True)

    def disable_open_folder_button(self) -> None:
        """フォルダ開くボタンを無効にする"""
        self.open_folder_button.setEnabled(False)

    def include_subdirs(self) -> bool:
        """サブディレクトリを含むかを取得

        Returns:
            含む場合True
        """
        return self.include_subdirs_checkbox.isChecked()
