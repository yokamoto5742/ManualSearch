from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QInputDialog, QLineEdit,
    QListWidget, QMessageBox, QPushButton, QSizePolicy, QVBoxLayout, QWidget
)

from utils.config_manager import ConfigManager
from utils.constants import (
    DIALOG_MESSAGES,
    DIALOG_TITLES,
    DIRECTORY_MANAGEMENT_DIALOG_HEIGHT,
    DIRECTORY_MANAGEMENT_DIALOG_WIDTH,
    FOLDER_PATH_INPUT_MIN_WIDTH,
    UI_LABELS
)
from utils.helpers import create_confirmation_dialog


class DirectoryManagementDialog(QDialog):
    """検索対象フォルダを管理するダイアログ"""

    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None) -> None:
        """初期化

        Args:
            config_manager: 設定管理オブジェクト
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.config_manager = config_manager

        self.setWindowTitle(DIALOG_TITLES['DIRECTORY_MANAGEMENT'])
        self.setModal(True)
        self.resize(DIRECTORY_MANAGEMENT_DIALOG_WIDTH, DIRECTORY_MANAGEMENT_DIALOG_HEIGHT)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIレイアウトを構築"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.dir_list = QListWidget()
        self.dir_list.addItems(self.config_manager.get_directories())
        layout.addWidget(self.dir_list)

        layout.addLayout(self._setup_button_layout())

        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.button(QDialogButtonBox.Close).setText(UI_LABELS['CLOSE_BUTTON'])
        button_box.rejected.connect(self.close)
        layout.addWidget(button_box)

    def _setup_button_layout(self) -> QHBoxLayout:
        """フォルダ操作ボタンを配置

        Returns:
            ボタンレイアウト
        """
        button_layout = QHBoxLayout()

        add_button = QPushButton(UI_LABELS['ADD_BUTTON'])
        add_button.clicked.connect(self.add_directory)

        edit_button = QPushButton(UI_LABELS['EDIT_BUTTON'])
        edit_button.clicked.connect(self.edit_directory)

        delete_button = QPushButton(UI_LABELS['DELETE_BUTTON'])
        delete_button.clicked.connect(self.delete_directory)

        button_layout.addWidget(add_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        button_layout.addStretch(1)

        return button_layout

    def _save_directories(self) -> None:
        """リストの内容を設定へ保存"""
        items = (self.dir_list.item(row) for row in range(self.dir_list.count()))
        self.config_manager.set_directories([item.text() for item in items if item])

    def add_directory(self) -> None:
        """検索対象のフォルダを追加"""
        try:
            directory = QFileDialog.getExistingDirectory(self, DIALOG_TITLES['SELECT_FOLDER'])
            if not directory:
                return

            if self.dir_list.findItems(directory, Qt.MatchExactly):
                return

            self.dir_list.addItem(directory)
            self._save_directories()
        except Exception as e:
            QMessageBox.critical(self, DIALOG_TITLES['ERROR'], f"フォルダの追加中にエラーが発生しました: {str(e)}")

    def edit_directory(self) -> None:
        """選択されているフォルダのパスを編集"""
        current_item = self.dir_list.currentItem()
        if current_item is None:
            return

        try:
            dialog = QInputDialog(self)
            dialog.setWindowTitle(DIALOG_TITLES['EDIT_FOLDER_PATH'])
            dialog.setLabelText(DIALOG_MESSAGES['EDIT_FOLDER_PATH_LABEL'])
            dialog.setTextValue(current_item.text())
            dialog.setInputMode(QInputDialog.TextInput)

            text_field = dialog.findChild(QLineEdit)
            if text_field:
                text_field.setMinimumWidth(FOLDER_PATH_INPUT_MIN_WIDTH)

            dialog.setSizeGripEnabled(True)
            dialog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            if dialog.exec_() == QInputDialog.Accepted:
                new_directory = dialog.textValue()
                if new_directory:
                    current_item.setText(new_directory)
                    self._save_directories()
        except Exception as e:
            QMessageBox.critical(self, DIALOG_TITLES['ERROR'], f"フォルダの編集中にエラーが発生しました: {str(e)}")

    def delete_directory(self) -> None:
        """選択されているフォルダを削除"""
        current_item = self.dir_list.currentItem()
        if current_item is None:
            return

        try:
            msg_box = create_confirmation_dialog(
                self,
                DIALOG_TITLES['CONFIRM'],
                f"「{current_item.text()}」を削除しますか？",
                QMessageBox.No
            )

            if msg_box.exec_() == QMessageBox.Yes:
                self.dir_list.takeItem(self.dir_list.row(current_item))
                self._save_directories()
        except Exception as e:
            QMessageBox.critical(self, DIALOG_TITLES['ERROR'], f"フォルダの削除中にエラーが発生しました: {str(e)}")
