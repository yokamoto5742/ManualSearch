import os
import re
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QTextEdit, QProgressDialog

from file_searcher import FileSearcher

class ResultsWidget(QWidget):
    result_selected = pyqtSignal()

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 結果リスト
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_result)
        layout.addWidget(self.results_list)

        # ファイル名のフォントサイズを設定
        self.filename_font = QFont()
        self.filename_font.setPointSize(self.config_manager.get_filename_font_size())

        # 結果詳細のフォントサイズを設定
        self.result_detail_font = QFont()
        self.result_detail_font.setPointSize(self.config_manager.get_result_detail_font_size())

        # 結果表示
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setFont(self.result_detail_font)
        layout.addWidget(self.result_display)

        self.search_term_colors = {}
        self.html_font_size = self.config_manager.get_html_font_size()
        self.current_file_path = None
        self.current_position = None
        self.searcher = None
        self.progress_dialog = None

    def perform_search(self, directory, search_terms, include_subdirs, search_type):
        self.search_term_colors = {}
        colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
        self.search_term_colors = {term: colors[i % len(colors)] for i, term in enumerate(search_terms)}

        file_extensions = self.config_manager.get_file_extensions()
        context_length = self.config_manager.get_context_length()
        self.searcher = FileSearcher(directory, search_terms, include_subdirs, search_type, file_extensions, context_length)
        self.searcher.result_found.connect(self.add_result)
        self.searcher.progress_update.connect(self.update_progress)
        self.searcher.search_completed.connect(self.search_completed)

        # 進捗ダイアログの設定
        self.progress_dialog = QProgressDialog("検索中...", "キャンセル", 0, 100, self)
        self.progress_dialog.setWindowTitle("検索進捗")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.cancel_search)
        self.progress_dialog.show()

        self.searcher.start()

    def update_progress(self, value):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)

    def cancel_search(self):
        if self.searcher:
            self.searcher.cancel_search()

    def search_completed(self):
        if self.progress_dialog:
            self.progress_dialog.close()

    def add_result(self, file_path, results):
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

    def show_result(self, item):
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

        self.result_display.setHtml(result_html)

        self.current_file_path = file_path
        self.current_position = position
        self.result_selected.emit()

    def highlight_content(self, content):
        highlighted = content
        for term, color in self.search_term_colors.items():
            highlighted = re.sub(
                f'({re.escape(term)})',
                f'<span style="background-color: {color};">\\1</span>',
                highlighted,
                flags=re.IGNORECASE
            )
        return highlighted

    def clear_results(self):
        self.results_list.clear()
        self.result_display.clear()

    def get_selected_file_info(self):
        return self.current_file_path, self.current_position
