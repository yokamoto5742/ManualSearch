import os
import subprocess
import tempfile
import time
import webbrowser
from typing import List, Tuple, Optional
import re

import fitz
import markdown
import psutil
import pyautogui
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QTextEdit, QFileDialog, QListWidget, QListWidgetItem, QMessageBox,
                             QCheckBox, QComboBox, QProgressDialog, QLabel, QStyleFactory)

from config_manager import ConfigManager
from file_searcher import FileSearcher


class AutoCloseMessage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #cccccc;
            border-radius: 5px;
        """)
        self.layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.close)

    def show_message(self, message: str, duration: int = 1000):
        self.label.setText(message)
        self.adjustSize()
        parent = self.parent()
        if parent:
            geometry = parent.geometry()
            self.move(geometry.center() - self.rect().center())
        self.show()
        self.timer.start(duration)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("マニュアル検索アプリ")
        self.setup_window_geometry()
        self.setup_font()
        self.setup_main_layout()
        self.setup_search_bar()
        self.setup_search_type()
        self.setup_directory_selection()
        self.setup_results_list()
        self.setup_result_display()
        self.setup_buttons()
        self.setup_status_variables()
        self.auto_close_message = AutoCloseMessage(self)

    def setup_window_geometry(self):
        geometry = self.config_manager.window_geometry
        self.setGeometry(*geometry)

    def setup_font(self):
        font = QFont()
        font.setPointSize(self.config_manager.font_size)
        self.setFont(font)

    def setup_main_layout(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.layout = QVBoxLayout()
        main_widget.setLayout(self.layout)

    def setup_search_bar(self):
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索語を入力 ( , または 、区切りで複数語検索)")
        self.search_input.returnPressed.connect(self.start_search)
        search_button = QPushButton("検索")
        search_button.clicked.connect(self.start_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        self.layout.addLayout(search_layout)

    def setup_search_type(self):
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["AND検索(複数語のすべてを含む)", "OR検索(複数語のいずれかを含む)"])
        self.layout.addWidget(self.search_type_combo)

    def setup_directory_selection(self):
        dir_layout = QVBoxLayout()
        self.dir_combo = QComboBox()
        self.update_directory_combo()
        self.dir_combo.setEditable(True)
        self.dir_combo.currentTextChanged.connect(self.update_last_directory)
        self.dir_combo.editTextChanged.connect(self.validate_directory)
        dir_layout.addWidget(self.dir_combo)

        dir_buttons_layout = QHBoxLayout()
        dir_add_button = QPushButton("追加")
        dir_add_button.clicked.connect(self.add_directory)
        dir_edit_button = QPushButton("編集")
        dir_edit_button.clicked.connect(self.edit_directory)
        dir_delete_button = QPushButton("削除")
        dir_delete_button.clicked.connect(self.delete_directory)
        self.include_subdirs_checkbox = QCheckBox("サブフォルダを含む")
        self.include_subdirs_checkbox.setChecked(True)

        dir_buttons_layout.addWidget(dir_add_button)
        dir_buttons_layout.addWidget(dir_edit_button)
        dir_buttons_layout.addWidget(dir_delete_button)
        dir_buttons_layout.addWidget(self.include_subdirs_checkbox)
        dir_buttons_layout.addStretch(1)

        dir_layout.addLayout(dir_buttons_layout)
        self.layout.addLayout(dir_layout)

    def setup_results_list(self):
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_result)
        self.layout.addWidget(self.results_list)

        self.filename_font = QFont()
        self.filename_font.setPointSize(self.config_manager.filename_font_size)

        self.result_detail_font = QFont()
        self.result_detail_font.setPointSize(self.config_manager.result_detail_font_size)

    def setup_result_display(self):
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setFont(self.result_detail_font)
        self.layout.addWidget(self.result_display)

    def setup_buttons(self):
        button_layout = QHBoxLayout()
        self.open_file_button = QPushButton("ファイルを開く")
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setEnabled(False)
        button_layout.addWidget(self.open_file_button)

        self.open_folder_button = QPushButton("フォルダを開く")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)

        self.layout.addLayout(button_layout)

    def setup_status_variables(self):
        self.current_file_path = None
        self.current_position = None
        self.search_term_colors = {}
        self.html_font_size = self.config_manager.html_font_size

    def update_directory_combo(self):
        self.dir_combo.clear()
        directories = self.config_manager.directories
        self.dir_combo.addItems(directories)
        last_directory = self.config_manager.last_directory
        if last_directory and last_directory in directories:
            self.dir_combo.setCurrentText(last_directory)
        elif directories:
            self.dir_combo.setCurrentText(directories[0])

    def update_last_directory(self, directory: str):
        if os.path.isdir(directory):
            self.config_manager.last_directory = directory

    def validate_directory(self, directory: str):
        if not os.path.isdir(directory):
            self.dir_combo.setStyleSheet("background-color: #FFCCCC;")
        else:
            self.dir_combo.setStyleSheet("")

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "フォルダを選択")
        if directory:
            current_dirs = self.config_manager.directories
            if directory not in current_dirs:
                current_dirs.append(directory)
                self.config_manager.directories = current_dirs
                self.dir_combo.addItem(directory)
            self.dir_combo.setCurrentText(directory)
            self.config_manager.last_directory = directory

    def edit_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            new_dir, ok = QFileDialog.getExistingDirectory(self, "フォルダを選択", current_dir)
            if ok and new_dir:
                current_dirs = self.config_manager.directories
                index = current_dirs.index(current_dir)
                current_dirs[index] = new_dir
                self.config_manager.directories = current_dirs
                self.dir_combo.setItemText(self.dir_combo.currentIndex(), new_dir)

    def delete_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            reply = QMessageBox.question(self, '確認',
                                         f"本当に「{current_dir}」を削除しますか？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                current_dirs = self.config_manager.directories
                current_dirs.remove(current_dir)
                self.config_manager.directories = current_dirs
                self.dir_combo.removeItem(self.dir_combo.currentIndex())

    def start_search(self):
        self.results_list.clear()
        self.result_display.clear()
        self.open_file_button.setEnabled(False)
        self.open_folder_button.setEnabled(False)

        directory = self.dir_combo.currentText()
        search_terms = [term.strip() for term in self.search_input.text().split(',') if term.strip()]

        colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
        self.search_term_colors = {term: colors[i % len(colors)] for i, term in enumerate(search_terms)}
        include_subdirs = self.include_subdirs_checkbox.isChecked()
        search_type = 'AND' if self.search_type_combo.currentText().startswith("AND") else 'OR'

        if not directory or not search_terms:
            return

        self.searcher = FileSearcher(self.config_manager, directory, search_terms, include_subdirs, search_type)
        self.searcher.result_found.connect(self.add_result)
        self.searcher.progress_update.connect(self.update_progress)
        self.searcher.search_completed.connect(self.search_completed)

        self.progress_dialog = QProgressDialog("検索中...", "キャンセル", 0, 100, self)
        self.progress_dialog.setWindowTitle("検索進捗")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.canceled.connect(self.cancel_search)
        self.progress_dialog.show()

        self.searcher.start()

    def update_progress(self, value: int):
        if self.progress_dialog:
            self.progress_dialog.setValue(value)

    def cancel_search(self):
        if hasattr(self, 'searcher'):
            self.searcher.cancel_search()

    def search_completed(self):
        if self.progress_dialog:
            self.progress_dialog.close()
        self.auto_close_message.show_message("ファイル検索が完了しました")

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

    def show_result(self, item: QListWidgetItem):
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
        self.open_file_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)

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

    def open_folder(self):
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            QMessageBox.warning(self, "エラー", "ファイルが存在しません。")
            return

        folder_path = os.path.dirname(self.current_file_path)
        try:
            os.startfile(folder_path)
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"フォルダを開けませんでした: {str(e)}")

    def open_file(self):
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            QMessageBox.warning(self, "エラー", "ファイルが存在しません。")
            return

        file_extension = os.path.splitext(self.current_file_path)[1].lower()

        if file_extension == '.pdf':
            self.open_pdf()
        elif file_extension in ['.txt', '.md']:
            self.open_text_file()
        else:
            QMessageBox.warning(self, "エラー", "サポートされていないファイル形式です。")

    def open_pdf(self):
        try:
            search_terms = [term.strip() for term in re.split('[,、]', self.search_input.text()) if term.strip()]
            highlighted_pdf_path = self.highlight_pdf(self.current_file_path, search_terms)

            process = subprocess.Popen([self.acrobat_path, highlighted_pdf_path])

            self.wait_for_acrobat(process.pid)

            self.navigate_to_page(self.current_position)

        except Exception as e:
            QMessageBox.warning(self, "エラー", f"PDFを開けませんでした: {str(e)}")

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

    def highlight_pdf(self, pdf_path: str, search_terms: List[str]) -> str:
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

    def open_text_file(self):
        try:
            search_terms = [term.strip() for term in self.search_input.text().split(',') if term.strip()]
            highlighted_html_path = self.highlight_text_file(self.current_file_path, search_terms)
            webbrowser.open(f'file://{highlighted_html_path}')
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"テキストファイルを開けませんでした: {str(e)}")

    def highlight_text_file(self, file_path: str, search_terms: List[str]) -> str:
        try:
            content = self.config_manager.read_file_with_auto_encoding(file_path)

            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension == '.md':
                content = markdown.markdown(content)

            colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
            for i, term in enumerate(search_terms):
                color = colors[i % len(colors)]
                content = re.sub(
                    f'({re.escape(term.strip())})',
                    f'<span style="background-color: {color};">\\1</span>',
                    content,
                    flags=re.IGNORECASE
                )

            html_template = f'''
            <!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{os.path.basename(file_path)}</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        padding: 20px; 
                        font-size: {self.html_font_size}px;
                    }}
                    pre {{ 
                        background-color: #f4f4f4; 
                        padding: 10px; 
                        border-radius: 5px; 
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                    #content {{
                        max-width: 100%;
                        overflow-x: auto;
                    }}
                    #controls {{
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background-color: rgba(255, 255, 255, 0.8);
                        padding: 10px;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div id="controls">
                    <button onclick="changeFontSize(1)">文字を大きく</button>
                    <button onclick="changeFontSize(-1)">文字を小さく</button>
                    <button onclick="toggleWordWrap()">文字の折り返し</button>
                </div>
                <h1>{os.path.basename(file_path)}</h1>
                <div id="content">{'<pre>' if file_extension == '.txt' else ''}{content}{'</pre>' if file_extension == '.txt' else ''}</div>
                <script>
                    var currentFontSize = {self.html_font_size};

                    function changeFontSize(delta) {{
                        currentFontSize += delta;
                        if (currentFontSize < 8) currentFontSize = 8;
                        if (currentFontSize > 32) currentFontSize = 32;
                        document.body.style.fontSize = currentFontSize + 'px';
                    }}

                    function toggleWordWrap() {{
                        var content = document.getElementById('content');
                        var pre = content.querySelector('pre');
                        if (pre) {{
                            if (pre.style.whiteSpace === 'pre-wrap') {{
                                pre.style.whiteSpace = 'pre';
                                pre.style.overflowX = 'auto';
                            }} else {{
                                pre.style.whiteSpace = 'pre-wrap';
                                pre.style.overflowX = 'hidden';
                            }}
                        }}
                    }}
                </script>
            </body>
            </html>
            '''

            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
                tmp_file.write(html_template)
                return tmp_file.name
        except ValueError as e:
            raise ValueError(f"ファイルの読み込みに失敗しました: {file_path} - {str(e)}")

    def closeEvent(self, event):
        geometry = self.geometry()
        self.config_manager.window_geometry = (geometry.x(), geometry.y(), geometry.width(), geometry.height())
        self.config_manager.html_font_size = self.html_font_size
        super().closeEvent(event)