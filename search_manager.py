import os
import re
from typing import List, Tuple
from PyQt5.QtWidgets import QListWidgetItem, QTextEdit, QProgressDialog
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont

from config_manager import ConfigManager
from file_searcher import FileSearcher

class SearchManager(QObject):
    search_completed = pyqtSignal()

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.current_file_path = None
        self.current_position = None
        self.search_term_colors = {}
        self.html_font_size = self.config_manager.html_font_size
        self.filename_font = QFont()
        self.filename_font.setPointSize(self.config_manager.filename_font_size)
        self.result_detail_font = QFont()
        self.result_detail_font.setPointSize(self.config_manager.result_detail_font_size)

    def start_search(self, search_input: str, directory: str, search_type: str, include_subdirs: bool):
        self.results_list.clear()
        self.result_display.clear()
        search_terms = [term.strip() for term in re.split('[,、]', search_input) if term.strip()]

        colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
        self.search_term_colors = {term: colors[i % len(colors)] for i, term in enumerate(search_terms)}

        if not directory or not search_terms:
            return

        self.searcher = FileSearcher(self.config_manager, directory, search_terms, include_subdirs, 
                                     'AND' if search_type.startswith("AND") else 'OR')
        self.searcher.result_found.connect(self.add_result)
        self.searcher.progress_update.connect(self.update_progress)
        self.searcher.search_completed.connect(self.on_search_completed)

        self.progress_dialog = QProgressDialog("検索中...", "キャンセル", 0, 100, self.parent())
        self.progress_dialog.setWindowTitle("検索進捗")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.cancel_search)
        self.progress_dialog.show()

        self.searcher.start()

    def add_result(self, file_path: str, results: List[Tuple[int, str]]):
        for i, (position, context) in enumerate(results):
            file_name = os.path.basename(file_path)
            if file_path.lower().endswith('.pdf'):
                item = f"{file_name} (ページ: {position}, 一致: {i + 1})"
            else:
                item = f"{file_name} (行: {position}, 一致: {i + 1})"
            list_item = QListWidgetItem(item)
            list_item.setData(Qt.UserRole, (file_path, position, context))
            list_item.setFont(self.filename_font)
            self.results_list.addItem(list_item)

    def show_result(self, item: QListWidgetItem, result_display: QTextEdit):
        file_path, position, context = item.data(Qt.UserRole)
        highlighted_content = self.highlight_content(context)

        result_html = f'<span style="font-size:{self.result_detail_font.pointSize()}pt;">'
        result_html += f"<h3>ファイル: {os.path.basename(file_path)}</h3>"
        if file_path.lower().endswith('.pdf'):
            result_html += f"<p>ページ: {position}</p>"
        else:
            result_html += f"<p>行: {position}</p>"
        result_html += f"<p>{highlighted_content}</p>"
        result_html += '</span>'

        result_display.setHtml(result_html)

        self.current_file_path = file_path
        self.current_position = position

    def highlight_content(self, content: str) -> str:
        highlighted = content
        for term, color in self.search_term_colors.items():
            highlighted = re.sub(
                f'({re.escape(term)})',
                f'<span style="background-color: {color};">\\1</span>',
                highlighted,
                flags=re.IGNORECASE
            )
        return highlighted

    def update_progress(self, value: int):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)

    def cancel_search(self):
        if hasattr(self, 'searcher'):
            self.searcher.cancel_search()

    def on_search_completed(self):
        if self.progress_dialog:
            self.progress_dialog.close()
        self.search_completed.emit()
