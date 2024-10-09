import os
import subprocess
from PyQt5.QtWidgets import QMessageBox
from config_manager import ConfigManager
from pdf_handler import PDFHandler
from text_file_handler import TextFileHandler

class FileOpener:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.pdf_handler = PDFHandler(config_manager)
        self.text_file_handler = TextFileHandler(config_manager)

    def open_file(self, file_path: str, position: int):
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(None, "エラー", "ファイルが存在しません。")
            return

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.pdf':
            self.open_pdf(file_path, position)
        elif file_extension in ['.txt', '.md']:
            self.open_text_file(file_path)
        else:
            QMessageBox.warning(None, "エラー", "サポートされていないファイル形式です。")

    def open_pdf(self, file_path: str, page_number: int):
        try:
            self.pdf_handler.open_pdf(file_path, page_number)
        except Exception as e:
            QMessageBox.warning(None, "エラー", f"PDFを開けませんでした: {str(e)}")

    def open_text_file(self, file_path: str):
        try:
            self.text_file_handler.open_text_file(file_path)
        except Exception as e:
            QMessageBox.warning(None, "エラー", f"テキストファイルを開けませんでした: {str(e)}")

    def open_folder(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(None, "エラー", "ファイルが存在しません。")
            return

        folder_path = os.path.dirname(file_path)
        try:
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.warning(None, "エラー", f"フォルダを開けませんでした: {str(e)}")
