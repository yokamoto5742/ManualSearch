import os

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStyleFactory, QApplication
)

from app import __version__
from service.file_opener import FileOpener
from utils.config_manager import ConfigManager
from widgets.auto_close_message_widget import AutoCloseMessage
from widgets.directory_widget import DirectoryWidget
from widgets.results_widget import ResultsWidget
from widgets.search_widget import SearchWidget


class MainWindow(QMainWindow):
    def __init__(self, config_manager: ConfigManager) -> None:
        super().__init__()
        self.config_manager = config_manager

        self.setWindowTitle(f"マニュアル検索 v{__version__}")
        QApplication.setStyle(QStyleFactory.create('Fusion'))

        self._setup_window_geometry()
        self._setup_font()
        self._setup_main_layout()
        self._setup_widgets()
        self._setup_buttons()
        self._connect_signals()

    def _setup_window_geometry(self) -> None:
        geometry = self.config_manager.get_window_geometry()
        self.setGeometry(*geometry)

    def _setup_font(self) -> None:
        font = QFont()
        font.setPointSize(self.config_manager.get_font_size())
        QApplication.setFont(font)

    def _setup_main_layout(self) -> None:
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)
        main_widget.setLayout(layout)

        self.main_layout = layout

    def _setup_widgets(self) -> None:
        self.search_widget = SearchWidget(self.config_manager)
        self.main_layout.addWidget(self.search_widget)

        self.directory_widget = DirectoryWidget(self.config_manager)
        self.main_layout.addWidget(self.directory_widget)

        self.results_widget = ResultsWidget(self.config_manager)
        self.main_layout.addWidget(self.results_widget)

        self.file_opener = FileOpener(self.config_manager)
        self.auto_close_message = AutoCloseMessage(self)

    def _setup_buttons(self) -> None:
        button_layout = QHBoxLayout()

        self.open_file_button = QPushButton("ファイルを開く")
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setEnabled(False)
        button_layout.addWidget(self.open_file_button)

        self.open_folder_button = QPushButton("フォルダを開く")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)

        self.main_layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        self.search_widget.search_requested.connect(self.start_search)
        self.results_widget.result_selected.connect(self.enable_open_buttons)

    def start_search(self) -> None:
        search_terms = self.search_widget.get_search_terms()
        directory = self.directory_widget.get_selected_directory()
        include_subdirs = self.directory_widget.include_subdirs()
        search_type = self.search_widget.get_search_type()

        if not directory or not search_terms:
            return

        self.results_widget.clear_results()
        self.open_file_button.setEnabled(False)
        self.open_folder_button.setEnabled(False)

        try:
            self.results_widget.perform_search(directory, search_terms, include_subdirs, search_type)
        except Exception as e:
            self.auto_close_message.show_message(f"検索中にエラーが発生しました: {str(e)}", 5000)

    def enable_open_buttons(self) -> None:
        self.open_file_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)

    def open_file(self) -> None:
        try:
            file_path, position = self.results_widget.get_selected_file_info()
            if not file_path:
                return
            search_terms = self.search_widget.get_search_terms()
            self.file_opener.open_file(file_path, position, search_terms)
        except FileNotFoundError:
            self._show_error_message("ファイルが見つかりません")
        except Exception as e:
            self._show_error_message(f"ファイルを開く際にエラーが発生しました: {e}")

    def _show_error_message(self, message: str) -> None:
        self.auto_close_message.show_message(message, 2000)

    def open_folder(self) -> None:
        try:
            file_path, _ = self.results_widget.get_selected_file_info()
            folder_path = os.path.dirname(file_path)
            self.file_opener.open_folder(folder_path)
        except FileNotFoundError:
            self.auto_close_message.show_message("フォルダが見つかりません", 2000)
        except Exception as e:
            self.auto_close_message.show_message(f"フォルダを開く際にエラーが発生しました: {str(e)}", 2000)

    def closeEvent(self, event) -> None:
        try:
            geometry = self.geometry()
            self.config_manager.set_window_geometry(
                geometry.x(), geometry.y(), geometry.width(), geometry.height()
            )
        except Exception as e:
            print(f"ウィンドウジオメトリの保存中にエラーが発生しました: {str(e)}")
        super().closeEvent(event)
