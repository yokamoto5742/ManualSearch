import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QCheckBox,
    QFileDialog, QInputDialog, QMessageBox, QLineEdit, QSizePolicy
)

from constants import (
    UI_LABELS
)
from utils.config_manager import ConfigManager
from utils.helpers import create_confirmation_dialog


class DirectoryWidget(QWidget):
    open_folder_requested = pyqtSignal()

    def __init__(self, config_manager: 'ConfigManager') -> None:
        super().__init__()
        self.config_manager = config_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        self._setup_directory_combo()
        layout.addWidget(self.dir_combo)

        button_layout = self._setup_button_layout()
        layout.addLayout(button_layout)

    def _setup_directory_combo(self) -> None:
        self.dir_combo = QComboBox()
        self.dir_combo.setEditable(True)

        directories = self.config_manager.get_directories()
        self.dir_combo.addItems(directories)

        last_directory = self.config_manager.get_last_directory()
        if last_directory and last_directory in directories:
            self.dir_combo.setCurrentText(last_directory)
        elif directories:
            self.dir_combo.setCurrentText(directories[0])

        self.dir_combo.currentTextChanged.connect(self.update_last_directory)
        self.dir_combo.editTextChanged.connect(self.validate_directory)

    def _setup_button_layout(self) -> QHBoxLayout:
        button_layout = QHBoxLayout()

        dir_add_button = QPushButton(UI_LABELS['ADD_BUTTON'])
        dir_add_button.clicked.connect(self.add_directory)

        dir_edit_button = QPushButton(UI_LABELS['EDIT_BUTTON'])
        dir_edit_button.clicked.connect(self.edit_directory)

        dir_delete_button = QPushButton(UI_LABELS['DELETE_BUTTON'])
        dir_delete_button.clicked.connect(self.delete_directory)

        self.include_subdirs_checkbox = QCheckBox(UI_LABELS['INCLUDE_SUBDIRS'])
        self.include_subdirs_checkbox.setChecked(True)

        self.open_folder_button = QPushButton(UI_LABELS['OPEN_FOLDER'])
        self.open_folder_button.clicked.connect(self.open_folder_requested.emit)
        self.open_folder_button.setEnabled(False)

        button_layout.addWidget(dir_add_button)
        button_layout.addWidget(dir_edit_button)
        button_layout.addWidget(dir_delete_button)
        button_layout.addWidget(self.include_subdirs_checkbox)
        button_layout.addStretch(1)
        button_layout.addWidget(self.open_folder_button)

        return button_layout

    def enable_open_folder_button(self) -> None:
        self.open_folder_button.setEnabled(True)

    def disable_open_folder_button(self) -> None:
        self.open_folder_button.setEnabled(False)

    def get_selected_directory(self) -> str:
        return self.dir_combo.currentText()

    def include_subdirs(self) -> bool:
        return self.include_subdirs_checkbox.isChecked()

    def update_last_directory(self, directory: str) -> None:
        if os.path.isdir(directory):
            self.config_manager.set_last_directory(directory)

    def validate_directory(self, directory: str) -> None:
        self.dir_combo.setStyleSheet(
            "" if os.path.isdir(directory) else "background-color: #FFCCCC;"
        )

    def add_directory(self) -> None:
        try:
            directory = QFileDialog.getExistingDirectory(self, "フォルダを選択")
            if directory:
                current_dirs = self.config_manager.get_directories()
                if directory not in current_dirs:
                    current_dirs.append(directory)
                    self.config_manager.set_directories(current_dirs)
                    self.dir_combo.addItem(directory)
                self.dir_combo.setCurrentText(directory)
                self.config_manager.set_last_directory(directory)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ディレクトリの追加中にエラーが発生しました: {str(e)}")

    def edit_directory(self) -> None:
        current_dir = self.dir_combo.currentText()
        if not current_dir:
            return

        try:
            dialog = QInputDialog(self)
            dialog.setWindowTitle("フォルダパスの編集")
            dialog.setLabelText("フォルダパスを編集してOKをクリックしてください。")
            dialog.setTextValue(current_dir)
            dialog.setInputMode(QInputDialog.TextInput)

            text_field = dialog.findChild(QLineEdit)
            if text_field:
                text_field.setMinimumWidth(1100)

            dialog.setSizeGripEnabled(True)
            dialog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            if dialog.exec_() == QInputDialog.Accepted:
                new_dir = dialog.textValue()
                if new_dir:
                    current_dirs = self.config_manager.get_directories()
                    index = current_dirs.index(current_dir)
                    current_dirs[index] = new_dir
                    self.config_manager.set_directories(current_dirs)
                    self.dir_combo.setItemText(self.dir_combo.currentIndex(), new_dir)
        except ValueError:
            QMessageBox.warning(self, "警告", "指定されたディレクトリが見つかりません。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ディレクトリの編集中にエラーが発生しました: {str(e)}")

    def delete_directory(self) -> None:
        current_dir = self.dir_combo.currentText()
        if not current_dir:
            return

        try:
            msg_box = create_confirmation_dialog(
                self,
                '確認',
                f"「{current_dir}」を削除しますか？",
                QMessageBox.No
            )

            reply = msg_box.exec_()

            if reply == QMessageBox.Yes:
                current_dirs = self.config_manager.get_directories()
                current_dirs.remove(current_dir)
                self.config_manager.set_directories(current_dirs)
                self.dir_combo.removeItem(self.dir_combo.currentIndex())
        except ValueError:
            QMessageBox.warning(self, "警告", "指定されたディレクトリが見つかりません。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ディレクトリの削除中にエラーが発生しました: {str(e)}")
