import os
import re
from typing import Dict, List, Tuple, Optional
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QTextEdit, QProgressDialog
)

from file_searcher import FileSearcher

class ResultsWidget(QWidget):
    result_selected = pyqtSignal()

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

        self._setup_ui()
        self._setup_fonts()

        self.search_term_colors: Dict[str, str] = {}
        self.html_font_size: int = self.config_manager.get_html_font_size()
        self.current_file_path: Optional[str] = None
        self.current_position: Optional[int] = None
        self.searcher: Optional[FileSearcher] = None
        self.progress_dialog: Optional[QProgressDialog] = None

    def _setup_ui(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_result)
        layout.addWidget(self.results_list)

        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

    def _setup_fonts(self) -> None:
        self.filename_font = QFont()
        self.filename_font.setPointSize(self.config_manager.get_filename_font_size())

        self.result_detail_font = QFont()
        self.result_detail_font.setPointSize(self.config_manager.get_result_detail_font_size())
        self.result_display.setFont(self.result_detail_font)

    def perform_search(self, directory: str, search_terms: List[str],
                       include_subdirs: bool, search_type: str) -> None:
        self._setup_search_colors(search_terms)
        self._setup_searcher(directory, search_terms, include_subdirs, search_type)
        self._setup_progress_dialog()
        self.searcher.start()

    def _setup_search_colors(self, search_terms: List[str]) -> None:
        colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
        self.search_term_colors = {term: colors[i % len(colors)] for i, term in enumerate(search_terms)}

    def _setup_searcher(self, directory: str, search_terms: List[str],
                        include_subdirs: bool, search_type: str) -> None:
        file_extensions = self.config_manager.get_file_extensions()
        context_length = self.config_manager.get_context_length()
        self.searcher = FileSearcher(directory, search_terms, include_subdirs,
                                     search_type, file_extensions, context_length)
        self.searcher.result_found.connect(self.add_result)
        self.searcher.progress_update.connect(self.update_progress)
        self.searcher.search_completed.connect(self.search_completed)

    def _setup_progress_dialog(self) -> None:
        self.progress_dialog = QProgressDialog("検索中...", "キャンセル", 0, 100, self)
        self.progress_dialog.setWindowTitle("検索進捗")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.cancel_search)
        self.progress_dialog.show()

    def update_progress(self, value: int) -> None:
        if self.progress_dialog:
            self.progress_dialog.setValue(value)

    def cancel_search(self) -> None:
        if self.searcher:
            self.searcher.cancel_search()

    def search_completed(self) -> None:
        if self.progress_dialog:
            self.progress_dialog.close()

    def add_result(self, file_path: str, results: List[Tuple[int, str]]) -> None:
        for i, (position, context) in enumerate(results):
            file_name = os.path.basename(file_path)
            item_text = self._create_item_text(file_name, file_path, position, i)
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.UserRole, (file_path, position, context))
            list_item.setFont(self.filename_font)
            self.results_list.addItem(list_item)

    @staticmethod
    def _create_item_text(file_name: str, file_path: str, position: int, index: int) -> str:
        if file_path.lower().endswith('.pdf'):
            return f"{file_name} (ページ: {position}, 一致: {index + 1})"
        return f"{file_name} (行: {position}, 一致: {index + 1})"

    def show_result(self, item: QListWidgetItem) -> None:
        try:
            file_path, position, context = item.data(Qt.UserRole)
            highlighted_content = self._highlight_content(context)
            result_html = self._create_result_html(file_path, position, highlighted_content)
            self.result_display.setHtml(result_html)

            self.current_file_path = file_path
            self.current_position = position
            self.result_selected.emit()
        except AttributeError:
            print("Error: Invalid item data")
        except Exception as e:
            print(f"Unexpected error in show_result: {e}")

    def _create_result_html(self, file_path: str, position: int, highlighted_content: str) -> str:
        result_html = f'<span style="font-size:{self.result_detail_font.pointSize()}pt;">'
        result_html += f"<h3>ファイル: {os.path.basename(file_path)}</h3>"
        result_html += f"<p>{'ページ' if file_path.lower().endswith('.pdf') else '行'}: {position}</p>"
        result_html += f"<p>{highlighted_content}</p>"
        result_html += '</span>'
        return result_html

    def _highlight_content(self, content: str) -> str:
        highlighted = content
        for term, color in self.search_term_colors.items():
            try:
                highlighted = re.sub(
                    f'({re.escape(term)})',
                    f'<span style="background-color: {color};">\\1</span>',
                    highlighted,
                    flags=re.IGNORECASE
                )
            except re.error:
                print(f"正規表現エラー: term={term}")
        return highlighted

    def clear_results(self) -> None:
        self.results_list.clear()
        self.result_display.clear()

    def get_selected_file_info(self) -> Tuple[Optional[str], Optional[int]]:
        return self.current_file_path, self.current_position
