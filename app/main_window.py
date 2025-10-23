import logging
import os

from PyQt5.QtGui import QFont, QCloseEvent
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStyleFactory, QApplication, QMessageBox, QCheckBox
)

from app import __version__
from service.file_opener import FileOpener
from service.pdf_handler import cleanup_temp_files
from utils.config_manager import ConfigManager
from utils.helpers import create_confirmation_dialog
from widgets.auto_close_message_widget import AutoCloseMessage
from widgets.directory_widget import DirectoryWidget
from widgets.index_management_widget import IndexManagementDialog
from widgets.results_widget import ResultsWidget
from widgets.search_widget import SearchWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """メインアプリケーションウィンドウ.

    検索機能、ファイル操作、インデックス管理を統括する.
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        """ウィンドウを初期化する.

        Args:
            config_manager: 設定管理オブジェクト.
        """
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
        geometry = self.config_manager.get_window_size_and_position()
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
            logger.error(f"インデックス設定の読み込みに失敗: {e}")
            self.use_index_search = False
            self.index_search_checkbox.setChecked(False)

    def start_search(self) -> None:
        """検索を実行する.

        インデックス検索が有効な場合は利用し、無効時は全ファイル検索を実施.
        """
        search_terms = self.search_widget.get_search_terms()
        directory = self.directory_widget.get_selected_directory()
        include_subdirs = self.directory_widget.include_subdirs()
        search_type = self.search_widget.get_search_type()
        is_global_search = self.directory_widget.is_global_search()

        if not search_terms:
            return

        if not is_global_search and not directory:
            return

        logger.info(f"検索開始: 検索語={search_terms}, タイプ={search_type}, グローバル検索={is_global_search}")
        self.results_widget.clear_results()
        self.directory_widget.disable_open_folder_button()

        try:
            if is_global_search:
                global_directories = self.config_manager.get_directories()
                if self.use_index_search:
                    self.results_widget.perform_global_index_search(
                        global_directories, search_terms, include_subdirs, search_type
                    )
                else:
                    self.results_widget.perform_global_search(
                        global_directories, search_terms, include_subdirs, search_type
                    )
            else:
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
        """インデックス管理ダイアログを表示する"""
        if self.index_dialog is None:
            self.index_dialog = IndexManagementDialog(self.config_manager, self)

        self.index_dialog.show()
        self.index_dialog.raise_()
        self.index_dialog.activateWindow()

    def toggle_index_search(self, enabled: bool) -> None:
        """インデックス検索モードを切り替える.

        Args:
            enabled: 有効にする場合True、無効にする場合False.
        """
        self.use_index_search = enabled
        logger.info(f"インデックス検索を{'有効' if enabled else '無効'}にしました")

        try:
            self.config_manager.set_use_index_search(enabled)
        except Exception as e:
            logger.error(f"インデックス設定の保存に失敗: {e}")

        if hasattr(self, 'index_search_checkbox'):
            self.index_search_checkbox.setChecked(enabled)

    def enable_open_buttons(self) -> None:
        self.directory_widget.enable_open_folder_button()

    def open_file(self) -> None:
        """選択されたファイルを開く"""
        try:
            file_path, position = self.results_widget.get_selected_file_info()
            if not file_path:
                return
            search_terms = self.search_widget.get_search_terms()
            use_highlight = self.directory_widget.get_use_pdf_highlight()
            self.file_opener.open_file(file_path, position or 0, search_terms, use_highlight)
        except FileNotFoundError:
            self._show_error_message("ファイルが見つかりません")
        except Exception as e:
            self._show_error_message(f"ファイルを開く際にエラーが発生しました: {e}")

    def _show_error_message(self, message: str) -> None:
        self.auto_close_message.show_message(message, 2000)

    def open_folder(self) -> None:
        """選択ファイルの親フォルダを開く"""
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
        """アプリケーションを終了する"""
        msg_box = create_confirmation_dialog(
            self,
            '確認',
            "検索を終了しますか?",
            QMessageBox.Yes
        )

        reply = msg_box.exec_()
        if reply == QMessageBox.Yes:
            logger.info("アプリケーションを終了します")
            try:
                self.file_opener.cleanup_resources()
                cleanup_temp_files()
            except Exception as e:
                logger.error(f"終了時のクリーンアップでエラー: {e}")

            app = QApplication.instance()
            if app is not None:
                app.quit()

    def closeEvent(self, a0: QCloseEvent) -> None:
        """ウィンドウクローズイベントを処理する"""
        try:
            self.file_opener.cleanup_resources()
            cleanup_temp_files()

        except Exception as e:
            logger.error(f"ウィンドウ終了処理中にエラーが発生しました: {str(e)}")
        finally:
            super().closeEvent(a0)
