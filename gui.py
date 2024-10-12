import os
import re
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, \
    QTextEdit, QFileDialog, QListWidget, QListWidgetItem, QMessageBox, QCheckBox, QComboBox, QInputDialog, \
    QProgressDialog, QLabel, QStyleFactory, QApplication
from file_searcher import FileSearcher
from pdf_handler import open_pdf, wait_for_acrobat, navigate_to_page, highlight_pdf
from text_handler import open_text_file
import subprocess


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

    def show_message(self, message, duration=1000):
        self.label.setText(message)
        self.adjustSize()
        parent = self.parent()
        if parent:
            geometry = parent.geometry()
            self.move(geometry.center() - self.rect().center())
        self.show()
        self.timer.start(duration)


class MainWindow(QMainWindow):
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager

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
        self.search_input.setPlaceholderText("検索語を入力 ( , または 、区切りで複数語検索)")
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

        self.search_term_colors = {}

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
        self.html_font_size = self.config_manager.get_html_font_size()

        button_layout = QHBoxLayout()
        self.open_file_button = QPushButton("ファイルを開く")
        self.open_file_button.clicked.connect(self.open_file)
        self.open_file_button.setEnabled(False)
        button_layout.addWidget(self.open_file_button)

        self.open_folder_button = QPushButton("フォルダを開く")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)

        layout.addLayout(button_layout)

        self.current_file_path = None
        self.current_position = None
        self.acrobat_path = self.config_manager.get_acrobat_path()
        self.progress_dialog = None
        self.auto_close_message = AutoCloseMessage(self)

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
        search_terms = [term.strip() for term in re.split('[,、]', self.search_input.text()) if term.strip()]

        # 検索語と色のマッピングを作成
        colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
        self.search_term_colors = {term: colors[i % len(colors)] for i, term in enumerate(search_terms)}
        include_subdirs = self.include_subdirs_checkbox.isChecked()
        search_type = 'AND' if self.search_type_combo.currentText().startswith("AND") else 'OR'

        if not directory or not search_terms:
            return

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

        self.auto_close_message.show_message("ファイル検索が完了しました")

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

    def get_result_background_color(self, context):
        # コンテキスト内の検索語の出現回数を数える
        term_counts = {term: context.lower().count(term.lower()) for term in self.search_term_colors.keys()}

        # 最も出現回数の多い検索語を見つける
        max_term = max(term_counts, key=term_counts.get)

        # 対応する色を返す（薄い色にする）
        color = QColor(self.search_term_colors[max_term])
        color.setAlpha(40)  # 透明度を設定（0-255の範囲、値が小さいほど透明）
        return color

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
        self.open_file_button.setEnabled(True)
        self.open_folder_button.setEnabled(True)  # フォルダを開くボタンを有効化

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
        search_terms = [term.strip() for term in re.split('[,、]', self.search_input.text()) if term.strip()]

        if file_extension == '.pdf':
            try:
                open_pdf(self.current_file_path, self.acrobat_path, self.current_position, search_terms)
            except Exception as e:
                QMessageBox.warning(self, "エラー", str(e))
        elif file_extension in ['.txt', '.md']:
            try:
                open_text_file(self.current_file_path, search_terms, self.config_manager.get_html_font_size())
            except Exception as e:
                QMessageBox.warning(self, "エラー", str(e))
        else:
            QMessageBox.warning(self, "エラー", "サポートされていないファイル形式です。")

    def open_pdf(self):
        try:
            search_terms = [term.strip() for term in re.split('[,、]', self.search_input.text()) if term.strip()]
            highlighted_pdf_path = highlight_pdf(self.current_file_path, search_terms)

            process = subprocess.Popen([self.acrobat_path, highlighted_pdf_path])

            wait_for_acrobat(process.pid)

            navigate_to_page(self.current_position)

        except Exception as e:
            QMessageBox.warning(self, "エラー", f"PDFを開けませんでした: {str(e)}")


    def closeEvent(self, event):
        geometry = self.geometry()
        self.config_manager.set_window_geometry(geometry.x(), geometry.y(), geometry.width(), geometry.height())
        self.config_manager.set_html_font_size(self.html_font_size)
        super().closeEvent(event)
