import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QCheckBox, QFileDialog, \
    QInputDialog, QMessageBox, QLineEdit


class DirectoryWidget(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        # ディレクトリ選択（1行目）
        self.dir_combo = QComboBox()
        directories = self.config_manager.get_directories()
        self.dir_combo.addItems(directories)
        self.dir_combo.setEditable(True)

        last_directory = self.config_manager.get_last_directory()
        if last_directory and last_directory in directories:
            self.dir_combo.setCurrentText(last_directory)
        elif directories:
            self.dir_combo.setCurrentText(directories[0])

        self.dir_combo.currentTextChanged.connect(self.update_last_directory)
        self.dir_combo.editTextChanged.connect(self.validate_directory)
        layout.addWidget(self.dir_combo)

        # ボタンとチェックボックス（2行目）
        button_layout = QHBoxLayout()
        dir_add_button = QPushButton("追加")
        dir_add_button.clicked.connect(self.add_directory)
        dir_edit_button = QPushButton("編集")
        dir_edit_button.clicked.connect(self.edit_directory)
        dir_delete_button = QPushButton("削除")
        dir_delete_button.clicked.connect(self.delete_directory)
        self.include_subdirs_checkbox = QCheckBox("サブフォルダを含む")
        self.include_subdirs_checkbox.setChecked(True)

        button_layout.addWidget(dir_add_button)
        button_layout.addWidget(dir_edit_button)
        button_layout.addWidget(dir_delete_button)
        button_layout.addWidget(self.include_subdirs_checkbox)
        button_layout.addStretch(1)  # 右側に余白を追加

        layout.addLayout(button_layout)

    def get_selected_directory(self):
        return self.dir_combo.currentText()

    def include_subdirs(self):
        return self.include_subdirs_checkbox.isChecked()

    def update_last_directory(self, directory):
        if os.path.isdir(directory):
            self.config_manager.set_last_directory(directory)

    def validate_directory(self, directory):
        if not os.path.isdir(directory):
            self.dir_combo.setStyleSheet("background-color: #FFCCCC;")
        else:
            self.dir_combo.setStyleSheet("")

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "フォルダを選択")
        if directory:
            current_dirs = self.config_manager.get_directories()
            if directory not in current_dirs:
                current_dirs.append(directory)
                self.config_manager.set_directories(current_dirs)
                self.dir_combo.addItem(directory)
            self.dir_combo.setCurrentText(directory)
            self.config_manager.set_last_directory(directory)

    def edit_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            new_dir, ok = QInputDialog.getText(self, "フォルダ編集", "新しいフォルダパス:", QLineEdit.Normal, current_dir)
            if ok and new_dir:
                current_dirs = self.config_manager.get_directories()
                index = current_dirs.index(current_dir)
                current_dirs[index] = new_dir
                self.config_manager.set_directories(current_dirs)
                self.dir_combo.setItemText(self.dir_combo.currentIndex(), new_dir)

    def delete_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            reply = QMessageBox.question(self, '確認',
                                         f"本当に「{current_dir}」を削除しますか？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                current_dirs = self.config_manager.get_directories()
                current_dirs.remove(current_dir)
                self.config_manager.set_directories(current_dirs)
                self.dir_combo.removeItem(self.dir_combo.currentIndex())
