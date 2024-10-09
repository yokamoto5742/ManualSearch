import os

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QTextEdit, QListWidget, QComboBox, QCheckBox, QFileDialog, QMessageBox, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config_manager import ConfigManager
from auto_close_message import AutoCloseMessage
from search_manager import SearchManager
from file_opener import FileOpener, open_folder


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.search_manager = SearchManager(self.config_manager)
        self.file_opener = FileOpener(self.config_manager)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("マニュアル検索アプリ")
        self.setup_window_geometry()
        self.setup_font()
        self.setup_main_layout()
        self.setup_search_bar()
        self.setup_search_type()
        self.setup_directory_selection()
        self.setup_results_list()
        self.setup_result_display()
        self.setup_buttons()
        self.auto_close_message = AutoCloseMessage(self)

    def setup_window_geometry(self):
        geometry = self.config_manager.window_geometry
        self.setGeometry(*geometry)

    def setup_font(self):
        font = QFont()
        font.setPointSize(self.config_manager.font_size)
        self.setFont(font)

    def setup_main_layout(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout()
        main_widget.setLayout(self.layout)

    def setup_search_bar(self):
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索語を入力 ( , または 、区切りで複数語検索)")
        self.search_input.returnPressed.connect(self.start_search)
        search_button = QPushButton("検索")
        search_button.clicked.connect(self.start_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        self.layout.addLayout(search_layout)

    def setup_search_type(self):
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["AND検索(複数語のすべてを含む)", "OR検索(複数語のいずれかを含む)"])
        self.layout.addWidget(self.search_type_combo)

    def setup_directory_selection(self):
        dir_layout = QVBoxLayout()

        # コンボボックスの設定
        self.dir_combo = QComboBox()
        directories = self.config_manager.directories
        self.dir_combo.addItems(directories)
        self.dir_combo.setEditable(True)

        last_directory = self.config_manager.last_directory
        if last_directory and last_directory in directories:
            self.dir_combo.setCurrentText(last_directory)
        elif directories:
            self.dir_combo.setCurrentText(directories[0])

        self.dir_combo.currentTextChanged.connect(self.update_last_directory)
        self.dir_combo.editTextChanged.connect(self.validate_directory)
        dir_layout.addWidget(self.dir_combo)

        # ボタンとチェックボックスの設定
        dir_buttons_layout = QHBoxLayout()
        dir_add_button = QPushButton("追加")
        dir_add_button.clicked.connect(self.add_directory)
        dir_edit_button = QPushButton("編集")
        dir_edit_button.clicked.connect(self.edit_directory)
        dir_delete_button = QPushButton("削除")
        dir_delete_button.clicked.connect(self.delete_directory)
        self.include_subdirs_checkbox = QCheckBox("サブフォルダを含む")
        self.include_subdirs_checkbox.setChecked(True)

        dir_buttons_layout.addWidget(dir_add_button)
        dir_buttons_layout.addWidget(dir_edit_button)
        dir_buttons_layout.addWidget(dir_delete_button)
        dir_buttons_layout.addWidget(self.include_subdirs_checkbox)
        dir_buttons_layout.addStretch(1)  # 右側に余白を追加

        dir_layout.addLayout(dir_buttons_layout)
        self.layout.addLayout(dir_layout)

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "フォルダを選択")
        if directory:
            current_dirs = self.config_manager.directories
            if directory not in current_dirs:
                current_dirs.append(directory)
                self.config_manager.directories = current_dirs
                self.dir_combo.addItem(directory)
            self.dir_combo.setCurrentText(directory)
            self.config_manager.last_directory = directory

    def update_last_directory(self, directory):
        if os.path.isdir(directory):
            self.config_manager.last_directory = directory

    def validate_directory(self, directory):
        if not os.path.isdir(directory):
            self.dir_combo.setStyleSheet("background-color: #FFCCCC;")
        else:
            self.dir_combo.setStyleSheet("")

    def edit_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            new_dir, ok = QInputDialog.getText(self, "フォルダ編集", "新しいフォルダパス:", QLineEdit.Normal,
                                               current_dir)
            if ok and new_dir:
                current_dirs = self.config_manager.directories
                index = current_dirs.index(current_dir)
                current_dirs[index] = new_dir
                self.config_manager.directories = current_dirs
                self.dir_combo.setItemText(self.dir_combo.currentIndex(), new_dir)

    def delete_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            reply = QMessageBox.question(self, '確認',
                                         f"本当に「{current_dir}」を削除しますか？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                current_dirs = self.config_manager.directories
                current_dirs.remove(current_dir)
                self.config_manager.directories = current_dirs
                self.dir_combo.removeItem(self.dir_combo.currentIndex())

    def setup_results_list(self):
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_result)
        self.layout.addWidget(self.results_list)

    def setup_result_display(self):
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.layout.addWidget(self.result_display)

    def setup_buttons(self):
        button_layout = QHBoxLayout()
        self.open_file_button = QPushButton("ファイルを開く")
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setEnabled(False)
        button_layout.addWidget(self.open_file_button)

        self.open_folder_button = QPushButton("フォルダを開く")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)

        self.layout.addLayout(button_layout)

    def start_search(self):
        # 検索処理の開始（SearchManagerに委譲）
        self.search_manager.start_search(self.search_input.text(), self.dir_combo.currentText(),
                                         self.search_type_combo.currentText(), self.include_subdirs_checkbox.isChecked())

    def show_result(self, item):
        # 検索結果の表示（SearchManagerに委譲）
        self.search_manager.show_result(item, self.result_display)
        self.open_file_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)

    def open_file(self):
        # ファイルを開く処理（FileOpenerに委譲）
        self.file_opener.open_file(self.search_manager.current_file_path, self.search_manager.current_position)

    def open_folder(self):
        # フォルダを開く処理（FileOpenerに委譲）
        open_folder(self.search_manager.current_file_path)

    def closeEvent(self, event):
        # 設定の保存
        geometry = self.geometry()
        self.config_manager.window_geometry = (geometry.x(), geometry.y(), geometry.width(), geometry.height())
        self.config_manager.html_font_size = self.search_manager.html_font_size
        super().closeEvent(event)
