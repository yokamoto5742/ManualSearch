import os
import tempfile
import time
import subprocess
import psutil
import pyautogui
import fitz
from PyQt5.QtWidgets import QMessageBox
from config_manager import ConfigManager

class PDFHandler:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def open_pdf(self, pdf_path: str, page_number: int):
        try:
            search_terms = self.config_manager.get_current_search_terms()
            highlighted_pdf_path = self.highlight_pdf(pdf_path, search_terms)

            acrobat_path = self.config_manager.acrobat_path

            if not os.path.exists(acrobat_path):
                QMessageBox.warning(None, "エラー", f"Adobe Acrobat が見つかりません: {acrobat_path}")
                return

            process = subprocess.Popen([acrobat_path, highlighted_pdf_path])

            if self.wait_for_acrobat(process.pid):
                self.navigate_to_page(page_number)
            else:
                QMessageBox.warning(None, "エラー", "Adobe Acrobat の起動に失敗しました")

        except Exception as e:
            QMessageBox.warning(None, "エラー", f"PDFを開けませんでした: {str(e)}")

    def wait_for_acrobat(self, pid: int, timeout: int = 30) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                process = psutil.Process(pid)
                if process.status() == psutil.STATUS_RUNNING:
                    time.sleep(2)
                    if "Acrobat" in pyautogui.getActiveWindowTitle():
                        return True
            except psutil.NoSuchProcess:
                return False
            time.sleep(0.5)
        return False

    def navigate_to_page(self, page_number: int):
        if page_number == 1:
            return

        try:
            pyautogui.hotkey('ctrl', 'shift', 'n')
            time.sleep(0.5)
            pyautogui.write(str(page_number))
            time.sleep(0.5)
            pyautogui.press('enter')
        except Exception as e:
            print(f"ページ移動中にエラーが発生しました: {str(e)}")

    def highlight_pdf(self, pdf_path: str, search_terms: list) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name

        doc = fitz.open(pdf_path)
        colors = [
            (1, 1, 0),  # yellow
            (0.5, 1, 0.5),  # light green
            (0.5, 0.7, 1),  # light blue
            (1, 0.6, 0.4),  # light salmon
            (1, 0.7, 0.7)  # light pink
        ]

        for page in doc:
            for i, term in enumerate(search_terms):
                text_instances = page.search_for(term.strip())
                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=colors[i % len(colors)])
                    highlight.update()

        doc.save(tmp_path)
        doc.close()

        return tmp_path
