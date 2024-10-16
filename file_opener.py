import os
import subprocess
from PyQt5.QtWidgets import QMessageBox

from pdf_handler import open_pdf, wait_for_acrobat, navigate_to_page, highlight_pdf
from text_handler import open_text_file

class FileOpener:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.acrobat_path = self.config_manager.get_acrobat_path()

    def open_file(self, file_path, position, search_terms):
        if not os.path.exists(file_path):
            QMessageBox.warning(None, "エラー", "ファイルが存在しません。")
            return

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.pdf':
            self.open_pdf_file(file_path, position, search_terms)
        elif file_extension in ['.txt', '.md']:
            self.open_text_file(file_path, search_terms)
        else:
            QMessageBox.warning(None, "エラー", "サポートされていないファイル形式です。")

    def open_pdf_file(self, file_path, position, search_terms):
        try:
            highlighted_pdf_path = highlight_pdf(file_path, search_terms)
            process = subprocess.Popen([self.acrobat_path, highlighted_pdf_path])
            wait_for_acrobat(process.pid)
            navigate_to_page(position)
        except Exception as e:
            QMessageBox.warning(None, "エラー", f"PDFを開けませんでした: {str(e)}")

    def open_text_file(self, file_path, search_terms):
        try:
            open_text_file(file_path, search_terms, self.config_manager.get_html_font_size())
        except Exception as e:
            QMessageBox.warning(None, "エラー", f"テキストファイルを開けませんでした: {str(e)}")

    def open_folder(self, folder_path):
        try:
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.warning(None, "エラー", f"フォルダを開けませんでした: {str(e)}")
