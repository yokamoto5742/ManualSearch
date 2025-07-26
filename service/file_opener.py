import os
import subprocess
import time
from typing import List

from PyQt5.QtWidgets import QMessageBox

from constants import (
    FILE_HANDLER_MAPPING,
    ERROR_MESSAGES,
    PROCESS_CLEANUP_DELAY
)
from service.pdf_handler import open_pdf, highlight_pdf, cleanup_temp_files
from service.text_handler import open_text_file
from utils.helpers import is_network_file


class FileOpener:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.acrobat_path: str = self.config_manager.get_acrobat_path()
        self._last_opened_file: str = ""

    SUPPORTED_EXTENSIONS = FILE_HANDLER_MAPPING

    def open_file(self, file_path: str, position: int, search_terms: List[str]) -> None:
        if not os.path.exists(file_path):
            self._show_error(ERROR_MESSAGES['FILE_NOT_FOUND'])
            return

        file_extension = os.path.splitext(file_path)[1].lower()
        handler_method = self.SUPPORTED_EXTENSIONS.get(file_extension)

        if not handler_method:
            self._show_error(ERROR_MESSAGES['UNSUPPORTED_FORMAT'])
            return

        if file_path == self._last_opened_file and file_extension == '.pdf':
            print(f"同じPDFファイルを再度開きます: {os.path.basename(file_path)}")
            cleanup_temp_files()
            time.sleep(PROCESS_CLEANUP_DELAY)

        try:
            method = getattr(self, handler_method)
            if file_extension == '.pdf':
                method(file_path, position, search_terms)
            else:
                method(file_path, search_terms)

            self._last_opened_file = file_path

        except Exception as e:
            self._show_error(f"ファイルを開く際にエラーが発生しました: {e}")
            if file_extension == '.pdf':
                cleanup_temp_files()

    def _open_pdf_file(self, file_path: str, position: int, search_terms: List[str]) -> None:
        try:
            if not self._check_pdf_accessibility(file_path):
                raise IOError(ERROR_MESSAGES['PDF_ACCESS_FAILED'])

            if not os.path.exists(self.acrobat_path):
                raise FileNotFoundError(f"{ERROR_MESSAGES['ACROBAT_NOT_FOUND']}: {self.acrobat_path}")

            open_pdf(file_path, self.acrobat_path, position, search_terms)

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
        try:
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if not header.startswith(b'%PDF'):
                    return False
            return True
        except (IOError, OSError):
            return False

    def _open_text_file(self, file_path: str, search_terms: List[str]) -> None:
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
        try:
            cleanup_temp_files()
            self._last_opened_file = ""
        except Exception as e:
            print(f"リソースクリーンアップ中にエラー: {e}")

    @staticmethod
    def _show_error(message: str) -> None:
        QMessageBox.warning(None, "エラー", message)
