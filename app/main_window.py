import os

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStyleFactory, QApplication, QMessageBox, QCheckBox
)

from app import __version__
from service.file_opener import FileOpener
from service.indexed_file_searcher import SmartFileSearcher, SearchMode
from service.pdf_handler import cleanup_temp_files
from utils.config_manager import ConfigManager
from utils.helpers import create_confirmation_dialog
from widgets.auto_close_message_widget import AutoCloseMessage
from widgets.directory_widget import DirectoryWidget
from widgets.index_management_widget import IndexManagementDialog
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
        self._setup_index_management_ui()
        self._setup_close_button()
        self._connect_signals()
        self._load_index_search_setting()

    def _setup_window_geometry(self) -> None:
        geometry = self.config_manager.get_window_size_and_position()  # 新しいメソッドに変更
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
        self.index_dialog = None
        self.use_index_search = False

    def _setup_close_button(self) -> None:
        close_button_layout = QHBoxLayout()
        close_button_layout.addStretch(1)

        self.close_button = QPushButton("閉じる")
        self.close_button.clicked.connect(self.close_application)
        close_button_layout.addWidget(self.close_button)

        self.main_layout.addLayout(close_button_layout)

    def _connect_signals(self) -> None:
        self.search_widget.search_requested.connect(self.start_search)
        self.results_widget.result_selected.connect(self.enable_open_buttons)
        self.results_widget.file_open_requested.connect(self.open_file)
        self.directory_widget.open_folder_requested.connect(self.open_folder)

    def _setup_index_management_ui(self) -> None:
        index_button_layout = QHBoxLayout()

        manage_index_button = QPushButton("インデックス設定")
        manage_index_button.clicked.connect(self.open_index_management)
        index_button_layout.addWidget(manage_index_button)

        self.index_search_checkbox = QCheckBox("インデックス検索")
        self.index_search_checkbox.toggled.connect(self.toggle_index_search)
        index_button_layout.addWidget(self.index_search_checkbox)

        self.main_layout.addLayout(index_button_layout)

    def _load_index_search_setting(self) -> None:
        try:
            use_index = self.config_manager.get_use_index_search()
            self.use_index_search = use_index
            self.index_search_checkbox.setChecked(use_index)
        except Exception as e:
            print(f"インデックス設定の読み込みに失敗: {e}")
            self.use_index_search = False
            self.index_search_checkbox.setChecked(False)

    def start_search(self) -> None:
        search_terms = self.search_widget.get_search_terms()
        directory = self.directory_widget.get_selected_directory()
        include_subdirs = self.directory_widget.include_subdirs()
        search_type = self.search_widget.get_search_type()

        if not directory or not search_terms:
            return

        self.results_widget.clear_results()
        self.directory_widget.disable_open_folder_button()

        try:
            if self.use_index_search:
                self.results_widget.perform_index_search(
                    directory, search_terms, include_subdirs, search_type
                )
            else:
                self.results_widget.perform_search(
                    directory, search_terms, include_subdirs, search_type
                )
        except Exception as e:
            self.auto_close_message.show_message(f"検索中にエラーが発生しました: {str(e)}", 5000)

    def open_index_management(self) -> None:
        if self.index_dialog is None:
            self.index_dialog = IndexManagementDialog(self.config_manager, self)

        self.index_dialog.show()
        self.index_dialog.raise_()
        self.index_dialog.activateWindow()

    def toggle_index_search(self, enabled: bool) -> None:
        self.use_index_search = enabled

        try:
            self.config_manager.set_use_index_search(enabled)
        except Exception as e:
            print(f"インデックス設定の保存に失敗: {e}")

        if hasattr(self, 'index_search_checkbox'):
            self.index_search_checkbox.setChecked(enabled)

    def enable_open_buttons(self) -> None:
        self.directory_widget.enable_open_folder_button()

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
            if not file_path:
                return
            folder_path = os.path.dirname(file_path)
            self.file_opener.open_folder(folder_path)
        except FileNotFoundError:
            self.auto_close_message.show_message("フォルダが見つかりません", 2000)
        except Exception as e:
            self.auto_close_message.show_message(f"フォルダを開く際にエラーが発生しました: {str(e)}", 2000)

    def close_application(self) -> None:
        msg_box = create_confirmation_dialog(
            self,
            '確認',
            "検索を終了しますか?",
            QMessageBox.Yes
        )

        reply = msg_box.exec_()
        if reply == QMessageBox.Yes:
            try:
                self.file_opener.cleanup_resources()
                cleanup_temp_files()
            except Exception as e:
                print(f"終了時のクリーンアップでエラー: {e}")

            QApplication.instance().quit()

    def closeEvent(self, event) -> None:
        try:
            # geometry = self.geometry()
            # self.config_manager.set_window_size_and_position(
            #     geometry.x(), geometry.y(), geometry.width(), geometry.height()
            # ) # 自動保存機能をコメントアウト
            self.file_opener.cleanup_resources()
            cleanup_temp_files()

        except Exception as e:
            print(f"ウィンドウ終了処理中にエラーが発生しました: {str(e)}")
        finally:
            super().closeEvent(event)
