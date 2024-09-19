import configparser
import os
import re
import subprocess
import sys
import tempfile
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor

import PyPDF2
import fitz
import markdown
import psutil
import pyautogui
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, \
    QTextEdit, QFileDialog, QListWidget, QListWidgetItem, QMessageBox, QCheckBox, QComboBox, QInputDialog
from PyQt5.QtWidgets import QStyleFactory

VERSION = "0.0.0"
LAST_UPDATED = "2024/09/12"


class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)

    def save_config(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get_file_extensions(self):
        return self.config.get('FileTypes', 'extensions', fallback='.pdf,.txt,.md').split(',')

    def get_window_geometry(self):
        geometry = self.config.get('WindowSettings', 'geometry', fallback='100,100,800,600')
        return [int(x) for x in geometry.split(',')]

    def get_font_size(self):
        return self.config.getint('WindowSettings', 'font_size', fallback=16)

    def get_acrobat_path(self):
        return self.config.get('Paths', 'acrobat_path', fallback=r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe')

    def set_file_extensions(self, extensions):
        if 'FileTypes' not in self.config:
            self.config['FileTypes'] = {}
        self.config['FileTypes']['extensions'] = ','.join(extensions)
        self.save_config()

    def set_window_geometry(self, x, y, width, height):
        if 'WindowSettings' not in self.config:
            self.config['WindowSettings'] = {}
        self.config['WindowSettings']['geometry'] = f"{x},{y},{width},{height}"
        self.save_config()

    def set_font_size(self, size):
        if 'WindowSettings' not in self.config:
            self.config['WindowSettings'] = {}
        self.config['WindowSettings']['font_size'] = str(size)
        self.save_config()

    def set_acrobat_path(self, path):
        if 'Paths' not in self.config:
            self.config['Paths'] = {}
        self.config['Paths']['acrobat_path'] = path
        self.save_config()

    def get_directories(self):
        return self.config.get('Directories', 'list', fallback='').split(',')

    def set_directories(self, directories):
        if 'Directories' not in self.config:
            self.config['Directories'] = {}
        self.config['Directories']['list'] = ','.join(directories)
        self.save_config()

    def get_last_directory(self):
        return self.config.get('Directories', 'last_directory', fallback='')

    def set_last_directory(self, directory):
        if 'Directories' not in self.config:
            self.config['Directories'] = {}
        self.config['Directories']['last_directory'] = directory
        self.save_config()


class FileSearcher(QThread):
    result_found = pyqtSignal(str, list)

    def __init__(self, directory, search_terms, include_subdirs, search_type, file_extensions):
        super().__init__()
        self.directory = directory
        self.search_terms = search_terms
        self.include_subdirs = include_subdirs
        self.search_type = search_type
        self.file_extensions = file_extensions

    def process_files(self, executor, root, files):
        futures = []
        for file in files:
            if any(file.endswith(ext) for ext in self.file_extensions):
                future = executor.submit(self.search_file, os.path.join(root, file))
                futures.append(future)
        for future in futures:
            result = future.result()
            if result:
                file_path, matches = result
                self.result_found.emit(file_path, matches)

    def run(self):
        with ThreadPoolExecutor() as executor:
            if self.include_subdirs:
                for root, _, files in os.walk(self.directory):
                    self.process_files(executor, root, files)
            else:
                files = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
                self.process_files(executor, self.directory, files)

    def search_file(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.pdf':
            return self.search_pdf(file_path)
        elif file_extension in ['.txt', '.md']:
            return self.search_text(file_path)

    def search_pdf(self, file_path):
        results = []
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if self.match_search_terms(text):
                    for search_term in self.search_terms:
                        for match in re.finditer(search_term, text, re.IGNORECASE):
                            start = max(0, match.start() - 50)
                            end = min(len(text), match.end() + 50)
                            context = text[start:end]
                            results.append((page_num + 1, context))  # Page numbers start from 1
        return (file_path, results) if results else None

    def search_text(self, file_path):
        results = []
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            if self.match_search_terms(content):
                for search_term in self.search_terms:
                    for match in re.finditer(search_term, content, re.IGNORECASE):
                        start = max(0, match.start() - 50)
                        end = min(len(content), match.end() + 50)
                        context = content[start:end]
                        line_number = content.count('\n', 0, match.start()) + 1
                        results.append((line_number, context))
        return (file_path, results) if results else None

    def match_search_terms(self, text):
        if self.search_type == 'AND':
            return all(re.search(term, text, re.IGNORECASE) for term in self.search_terms)
        elif self.search_type == 'OR':
            return any(re.search(term, text, re.IGNORECASE) for term in self.search_terms)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()

        self.setWindowTitle("マニュアル検索アプリ")

        QApplication.setStyle(QStyleFactory.create('Fusion'))

        # ウィンドウのジオメトリを設定
        geometry = self.config_manager.get_window_geometry()
        self.setGeometry(*geometry)

        font = QFont()
        font.setPointSize(self.config_manager.get_font_size())
        QApplication.setFont(font)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # 検索入力とボタン
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("検索語を入力 ( , 区切りで複数語検索)")
        self.search_input.returnPressed.connect(self.start_search)
        search_button = QPushButton("検索")
        search_button.clicked.connect(self.start_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # 検索タイプ選択
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems(["AND検索(複数語のすべてを含む)", "OR検索(複数語のいずれかを含む)"])
        layout.addWidget(self.search_type_combo)

        # フォルダ選択（1行目）
        dir_layout = QVBoxLayout()
        self.dir_combo = QComboBox()
        directories = self.config_manager.get_directories()
        self.dir_combo.addItems(directories)
        self.dir_combo.setEditable(True)

        last_directory = self.config_manager.get_last_directory()
        if last_directory and last_directory in directories:
            self.dir_combo.setCurrentText(last_directory)
        elif directories:
            self.dir_combo.setCurrentText(directories[0])

        self.dir_combo.currentTextChanged.connect(self.update_last_directory)
        self.dir_combo.editTextChanged.connect(self.validate_directory)
        dir_layout.addWidget(self.dir_combo)

        # ボタンとチェックボックス（2行目）
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
        dir_buttons_layout.addStretch(1)  # 右側に余白を追加

        dir_layout.addLayout(dir_buttons_layout)
        layout.addLayout(dir_layout)

        # 結果リスト
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.show_result)
        layout.addWidget(self.results_list)

        # 結果表示
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)

        # ファイルを開くボタン
        self.open_file_button = QPushButton("ファイルを開く")
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setEnabled(False)
        layout.addWidget(self.open_file_button)

        self.current_file_path = None
        self.current_position = None
        self.acrobat_path = self.config_manager.get_acrobat_path()

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "フォルダを選択")
        if directory:
            current_dirs = self.config_manager.get_directories()
            if directory not in current_dirs:
                current_dirs.append(directory)
                self.config_manager.set_directories(current_dirs)
                self.dir_combo.addItem(directory)
            self.dir_combo.setCurrentText(directory)
            self.config_manager.set_last_directory(directory)

    def update_last_directory(self, directory):
        if os.path.isdir(directory):
            self.config_manager.set_last_directory(directory)

    def validate_directory(self, directory):
        if not os.path.isdir(directory):
            self.dir_combo.setStyleSheet("background-color: #FFCCCC;")
        else:
            self.dir_combo.setStyleSheet("")

    def edit_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            new_dir, ok = QInputDialog.getText(self, "フォルダ編集", "新しいフォルダパス:", QLineEdit.Normal, current_dir)
            if ok and new_dir:
                current_dirs = self.config_manager.get_directories()
                index = current_dirs.index(current_dir)
                current_dirs[index] = new_dir
                self.config_manager.set_directories(current_dirs)
                self.dir_combo.setItemText(self.dir_combo.currentIndex(), new_dir)

    def delete_directory(self):
        current_dir = self.dir_combo.currentText()
        if current_dir:
            reply = QMessageBox.question(self, '確認',
                                         f"本当に「{current_dir}」を削除しますか？",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                current_dirs = self.config_manager.get_directories()
                current_dirs.remove(current_dir)
                self.config_manager.set_directories(current_dirs)
                self.dir_combo.removeItem(self.dir_combo.currentIndex())

    def start_search(self):
        self.results_list.clear()
        self.result_display.clear()
        self.open_file_button.setEnabled(False)

        directory = self.dir_combo.currentText()
        search_terms = [term.strip() for term in self.search_input.text().split(',')]
        include_subdirs = self.include_subdirs_checkbox.isChecked()
        search_type = 'AND' if self.search_type_combo.currentText() == "AND検索" else 'OR'

        if not directory or not search_terms:
            return

        file_extensions = self.config_manager.get_file_extensions()
        self.searcher = FileSearcher(directory, search_terms, include_subdirs, search_type, file_extensions)
        self.searcher.result_found.connect(self.add_result)
        self.searcher.start()

    def add_result(self, file_path, results):
        for i, (position, context) in enumerate(results):
            file_name = os.path.basename(file_path)
            if file_path.lower().endswith('.pdf'):
                item = f"{file_name} (ページ: {position}, 一致: {i + 1})"
            else:
                item = f"{file_name} (行: {position}, 一致: {i + 1})"
            list_item = QListWidgetItem(item)
            list_item.setData(Qt.UserRole, (file_path, position, context))
            self.results_list.addItem(list_item)

    def show_result(self, item):
        file_path, position, context = item.data(Qt.UserRole)
        highlighted_content = self.highlight_content(context, self.search_input.text().split(','))
        result_html = f"<h3>ファイル: {os.path.basename(file_path)}</h3>"
        if file_path.lower().endswith('.pdf'):
            result_html += f"<p>ページ: {position}</p>"
        else:
            result_html += f"<p>行: {position}</p>"
        result_html += f"<p>{highlighted_content}</p>"
        self.result_display.setHtml(result_html)

        self.current_file_path = file_path
        self.current_position = position
        self.open_file_button.setEnabled(True)

    def highlight_content(self, content, search_terms):
        highlighted = content
        for term in search_terms:
            highlighted = re.sub(
                f'({re.escape(term)})',
                r'<span style="background-color: yellow;">\1</span>',
                highlighted,
                flags=re.IGNORECASE
            )
        return highlighted

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
            highlighted_pdf_path = self.highlight_pdf(self.current_file_path, self.search_input.text())

            process = subprocess.Popen([self.acrobat_path, highlighted_pdf_path])

            self.wait_for_acrobat(process.pid)

            self.navigate_to_page(self.current_position)

        except Exception as e:
            QMessageBox.warning(self, "エラー", f"PDFを開けませんでした: {str(e)}")

    def wait_for_acrobat(self, pid, timeout=30):
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

    def navigate_to_page(self, page_number):
        # ページ数が1の場合は何もせずに関数を終了
        if page_number == 1:
            return

        try:
            # Ctrl+Shift+Nを押してページ移動ダイアログを開く
            pyautogui.hotkey('ctrl', 'shift', 'n')
            time.sleep(0.5)

            # ページ番号を入力
            pyautogui.write(str(page_number))
            time.sleep(0.5)

            # Enterを押してページに移動
            pyautogui.press('enter')

        except Exception as e:
            print(f"ページ移動中にエラーが発生しました: {str(e)}")

    def highlight_pdf(self, pdf_path, search_term):
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name

        # PDFを開く
        doc = fitz.open(pdf_path)

        # 各ページで検索語を探してハイライト
        for page in doc:
            text_instances = page.search_for(search_term)
            for inst in text_instances:
                highlight = page.add_highlight_annot(inst)
                highlight.update()

        # 変更を保存
        doc.save(tmp_path)
        doc.close()

        return tmp_path

    def open_text_file(self):
        try:
            # 検索語をハイライトしたHTMLを作成
            highlighted_html_path = self.highlight_text_file(self.current_file_path, self.search_input.text())

            # デフォルトのブラウザで開く
            webbrowser.open(f'file://{highlighted_html_path}')

        except Exception as e:
            QMessageBox.warning(self, "エラー", f"テキストファイルを開けませんでした: {str(e)}")

    def highlight_text_file(self, file_path, search_term):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.md':
            # Markdownをレンダリング
            content = markdown.markdown(content)

        # 検索語をハイライト
        highlighted_content = re.sub(
            f'({re.escape(search_term)})',
            r'<span style="background-color: yellow;">\1</span>',
            content,
            flags=re.IGNORECASE
        )

        # HTMLテンプレート
        html_template = f'''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{os.path.basename(file_path)}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
                pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>{os.path.basename(file_path)}</h1>
            {'<pre>' if file_extension == '.txt' else ''}
            {highlighted_content}
            {'</pre>' if file_extension == '.txt' else ''}
        </body>
        </html>
        '''

        # 一時HTMLファイルを作成
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write(html_template)
            return tmp_file.name

    def closeEvent(self, event):
        geometry = self.geometry()
        self.config_manager.set_window_geometry(geometry.x(), geometry.y(), geometry.width(), geometry.height())
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
