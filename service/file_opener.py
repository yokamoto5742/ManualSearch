import logging
import os
import subprocess
import time
from typing import List

from PyQt5.QtWidgets import QMessageBox

from service.pdf_handler import open_pdf, temp_file_manager
from service.text_handler import open_text_file
from utils.constants import (
    FILE_HANDLER_MAPPING,
    ERROR_MESSAGES,
    PROCESS_CLEANUP_DELAY
)
from utils.helpers import is_network_file

logger = logging.getLogger(__name__)


class FileOpener:
    """ファイルを適切なアプリケーションで開く処理を管理"""

    SUPPORTED_EXTENSIONS = FILE_HANDLER_MAPPING

    def __init__(self, config_manager) -> None:
        """初期化

        Args:
            config_manager: 設定マネージャーインスタンス
        """
        self.config_manager = config_manager
        self.acrobat_path = self.config_manager.find_available_acrobat_path() or ""
        self._last_opened_file: str = ""

    def open_file(self, file_path: str, position: int, search_terms: List[str], use_highlight: bool = True) -> None:
        """ファイルを開く

        Args:
            file_path: ファイルパス
            position: ページ/行位置
            search_terms: 検索語リスト
            use_highlight: ハイライトを使用するか
        """
        if not os.path.exists(file_path):
            self._show_error(ERROR_MESSAGES['FILE_NOT_FOUND'])
            return

        file_extension = os.path.splitext(file_path)[1].lower()
        handler_method = self.SUPPORTED_EXTENSIONS.get(file_extension)

        if not handler_method:
            self._show_error(ERROR_MESSAGES['UNSUPPORTED_FORMAT'])
            return

        if file_path == self._last_opened_file and file_extension == '.pdf':
            temp_file_manager.cleanup_all()
            time.sleep(PROCESS_CLEANUP_DELAY)

        try:
            method = getattr(self, handler_method)
            if file_extension == '.pdf':
                method(file_path, position, search_terms, use_highlight)
            else:
                method(file_path, search_terms)

            self._last_opened_file = file_path

        except Exception as e:
            self._show_error(f"ファイルを開く際にエラーが発生しました: {e}")
            if file_extension == '.pdf':
                temp_file_manager.cleanup_all()

    def _open_pdf_file(self, file_path: str, position: int, search_terms: List[str], use_highlight: bool = True) -> None:
        """PDFファイルを開く

        Args:
            file_path: PDFファイルパス
            position: ページ番号
            search_terms: 検索語リスト
            use_highlight: ハイライトを使用するかどうか

        Raises:
            IOError: ファイルアクセス失敗
            FileNotFoundError: Acrobatが見つからない
        """
        try:
            if not self._check_pdf_accessibility(file_path):
                raise IOError(ERROR_MESSAGES['PDF_ACCESS_FAILED'])

            if not self.acrobat_path or not os.path.exists(self.acrobat_path):
                raise FileNotFoundError(ERROR_MESSAGES['ALL_ACROBAT_PATHS_NOT_FOUND'])

            open_pdf(file_path, self.acrobat_path, position, search_terms, use_highlight)

        except IOError as e:
            self._show_error(f"PDFの処理に失敗しました: {e}")
            raise
        except subprocess.SubprocessError as e:
            self._show_error(f"{ERROR_MESSAGES['ACROBAT_START_FAILED']}: {e}")
            raise
        except Exception as e:
            self._show_error(f"PDFの操作中にエラーが発生しました: {e}")
            raise

    def _check_pdf_accessibility(self, file_path: str) -> bool:
        """PDFファイルのアクセス可能性を確認

        Args:
            file_path: PDFファイルパス

        Returns:
            アクセス可能な場合True
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if not header.startswith(b'%PDF'):
                    return False
            return True
        except (IOError, OSError):
            return False

    def _open_text_file(self, file_path: str, search_terms: List[str]) -> None:
        """テキストファイルを開く

        Args:
            file_path: ファイルパス
            search_terms: 検索語リスト

        Raises:
            IOError: ファイル読み込み失敗
            ValueError: ファイル処理エラー
        """
        try:
            font_size = self.config_manager.get_html_font_size()
            open_text_file(file_path, search_terms, font_size)
        except IOError as e:
            self._show_error(f"テキストファイルの読み込みに失敗しました: {e}")
            raise
        except ValueError as e:
            self._show_error(f"テキストファイルの処理中にエラーが発生しました: {e}")
            raise

    def open_folder(self, folder_path: str) -> None:
        """フォルダをエクスプローラーで開く

        Args:
            folder_path: フォルダパス
        """
        try:
            if is_network_file(folder_path):
                if folder_path.startswith('//'):
                    folder_path = folder_path.replace('/', '\\')

            os.startfile(folder_path)

        except FileNotFoundError:
            self._show_error(ERROR_MESSAGES['FOLDER_NOT_FOUND'])
        except OSError as e:
            self._show_error(f"{ERROR_MESSAGES['FOLDER_OPEN_FAILED']}: {e}")
        except Exception as e:
            self._show_error(f"フォルダを開く際にエラーが発生しました: {e}")

    def cleanup_resources(self) -> None:
        """リソースをクリーンアップ"""
        try:
            temp_file_manager.cleanup_all()
            self._last_opened_file = ""
        except Exception as e:
            logger.error(f"リソースクリーンアップ中にエラー: {e}")

    @staticmethod
    def _show_error(message: str) -> None:
        """エラーダイアログを表示

        Args:
            message: エラーメッセージ
        """
        QMessageBox.warning(None, "エラー", message)
