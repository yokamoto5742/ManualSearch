import os
import subprocess
from typing import List

from PyQt5.QtWidgets import QMessageBox

from service.pdf_handler import open_pdf, highlight_pdf
from service.text_handler import open_text_file


class FileOpener:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.acrobat_path: str = self.config_manager.get_acrobat_path()

    def open_file(self, file_path: str, position: int, search_terms: List[str]) -> None:
        if not os.path.exists(file_path):
            self._show_error("ファイルが存在しません。")
            return

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.pdf':
            self._open_pdf_file(file_path, position, search_terms)
        elif file_extension in ['.txt', '.md']:
            self._open_text_file(file_path, search_terms)
        else:
            self._show_error("サポートされていないファイル形式です。")

    def _open_pdf_file(self, file_path: str, position: int, search_terms: List[str]) -> None:
        try:
            highlighted_pdf_path = highlight_pdf(file_path, search_terms)
            open_pdf(highlighted_pdf_path, self.acrobat_path, position, search_terms)
        except IOError as e:
            self._show_error(f"PDFの処理に失敗しました: {e}")
        except subprocess.SubprocessError as e:
            self._show_error(f"Acrobatの起動に失敗しました: {e}")
        except Exception as e:
            self._show_error(f"PDFの操作中にエラーが発生しました: {e}")

    def _open_text_file(self, file_path: str, search_terms: List[str]) -> None:
        try:
            font_size = self.config_manager.get_html_font_size()
            open_text_file(file_path, search_terms, font_size)
        except IOError as e:
            self._show_error(f"テキストファイルの読み込みに失敗しました: {e}")
        except ValueError as e:
            self._show_error(f"テキストファイルの処理中にエラーが発生しました: {e}")

    def open_folder(self, folder_path: str) -> None:
        try:
            os.startfile(folder_path)
        except FileNotFoundError:
            self._show_error("指定されたフォルダが見つかりません。")
        except OSError as e:
            self._show_error(f"フォルダを開けませんでした: {e}")
        except Exception as e:
            self._show_error(f"フォルダを開く際にエラーが発生しました: {e}")

    @staticmethod
    def _show_error(message: str) -> None:
        QMessageBox.warning(None, "エラー", message)
