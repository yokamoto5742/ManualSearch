import os
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QStyleFactory, QApplication

from search_widget import SearchWidget
from directory_widget import DirectoryWidget
from results_widget import ResultsWidget
from file_opener import FileOpener
from auto_close_message import AutoCloseMessage


class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

        self.setWindowTitle("マニュアル検索アプリ")

        QApplication.setStyle(QStyleFactory.create('Fusion'))

        # ウィンドウのジオメトリを設定
        geometry = self.config_manager.get_window_geometry()
        self.setGeometry(*geometry)

        font = QFont()
        font.setPointSize(self.config_manager.get_font_size())
        QApplication.setFont(font)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # SearchWidget
        self.search_widget = SearchWidget(self.config_manager)
        layout.addWidget(self.search_widget)

        # DirectoryWidget
        self.directory_widget = DirectoryWidget(self.config_manager)
        layout.addWidget(self.directory_widget)

        # ResultsWidget
        self.results_widget = ResultsWidget(self.config_manager)
        layout.addWidget(self.results_widget)

        # FileOpener
        self.file_opener = FileOpener(self.config_manager)

        # Buttons
        button_layout = QHBoxLayout()
        self.open_file_button = QPushButton("ファイルを開く")
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setEnabled(False)
        button_layout.addWidget(self.open_file_button)

        self.open_folder_button = QPushButton("フォルダを開く")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)

        layout.addLayout(button_layout)

        self.auto_close_message = AutoCloseMessage(self)

        # Connect signals
        self.search_widget.search_requested.connect(self.start_search)
        self.results_widget.result_selected.connect(self.enable_open_buttons)

    def start_search(self):
        search_terms = self.search_widget.get_search_terms()
        directory = self.directory_widget.get_selected_directory()
        include_subdirs = self.directory_widget.include_subdirs()
        search_type = self.search_widget.get_search_type()

        if not directory or not search_terms:
            return

        self.results_widget.clear_results()
        self.open_file_button.setEnabled(False)
        self.open_folder_button.setEnabled(False)

        self.results_widget.perform_search(directory, search_terms, include_subdirs, search_type)

    def enable_open_buttons(self):
        self.open_file_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)

    def open_file(self):
        file_path, position = self.results_widget.get_selected_file_info()
        search_terms = self.search_widget.get_search_terms()
        self.file_opener.open_file(file_path, position, search_terms)

    def open_folder(self):
        file_path, _ = self.results_widget.get_selected_file_info()
        folder_path = os.path.dirname(file_path)
        self.file_opener.open_folder(folder_path)

    def closeEvent(self, event):
        geometry = self.geometry()
        self.config_manager.set_window_geometry(geometry.x(), geometry.y(), geometry.width(), geometry.height())
        super().closeEvent(event)
