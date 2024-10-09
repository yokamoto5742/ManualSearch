import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional

import PyPDF2
from PyQt5.QtCore import QThread, pyqtSignal

from config_manager import ConfigManager
from utils import normalize_path, check_file_accessibility, read_file_with_auto_encoding


class FileSearcher(QThread):
    result_found = pyqtSignal(str, list)
    progress_update = pyqtSignal(int)
    search_completed = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, directory: str, search_terms: List[str],
                 include_subdirs: bool, search_type: str):
        super().__init__()
        self.config_manager = config_manager
        self.directory = directory
        self.search_terms = search_terms
        self.include_subdirs = include_subdirs
        self.search_type = search_type
        self.cancel_flag = False

    def run(self):
        total_files = sum([len(files) for _, _, files in os.walk(self.directory)])
        processed_files = 0

        with ThreadPoolExecutor() as executor:
            if self.include_subdirs:
                for root, _, files in os.walk(self.directory):
                    if self.cancel_flag:
                        break
                    self.process_files(executor, root, files)
                    processed_files += len(files)
                    self.progress_update.emit(int((processed_files / total_files) * 100))
            else:
                files = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
                self.process_files(executor, self.directory, files)
                self.progress_update.emit(100)

        self.search_completed.emit()

    def process_files(self, executor: ThreadPoolExecutor, root: str, files: List[str]):
        futures = []
        for file in files:
            if self.cancel_flag:
                break
            if any(file.endswith(ext) for ext in self.config_manager.file_extensions):
                future = executor.submit(self.search_file, os.path.join(root, file))
                futures.append(future)
        for future in futures:
            if self.cancel_flag:
                break
            result = future.result()
            if result:
                file_path, matches = result
                self.result_found.emit(file_path, matches)

    def cancel_search(self):
        self.cancel_flag = True

    def search_file(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        normalized_path = normalize_path(file_path)
        if not check_file_accessibility(normalized_path):
            print(f"ファイルにアクセスできません: {normalized_path}")
            return None

        try:
            file_extension = os.path.splitext(normalized_path)[1].lower()

            if file_extension == '.pdf':
                return self.search_pdf(normalized_path)
            elif file_extension in ['.txt', '.md']:
                return self.search_text(normalized_path)
            else:
                print(f"サポートされていないファイル形式: {file_extension}")
                return None

        except IOError as e:
            print(f"ファイルアクセスエラー: {normalized_path} - {str(e)}")
        except Exception as e:
            print(f"予期せぬエラー: {normalized_path} - {str(e)}")

        return None

    def search_pdf(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        results = []
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if self.match_search_terms(text):
                        for search_term in self.search_terms:
                            for match in re.finditer(re.escape(search_term), text, re.IGNORECASE):
                                start = max(0, match.start() - self.config_manager.context_length)
                                end = min(len(text), match.end() + self.config_manager.context_length)
                                context = text[start:end]
                                results.append((page_num + 1, context))
                    if len(results) >= 100:  # 結果の数を制限
                        break
        except Exception as e:
            print(f"PDFの処理中にエラーが発生しました: {file_path} - {str(e)}")
        return (file_path, results) if results else None

    def search_text(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        results = []
        try:
            content = read_file_with_auto_encoding(file_path)
            if self.match_search_terms(content):
                for search_term in self.search_terms:
                    for match in re.finditer(re.escape(search_term), content, re.IGNORECASE):
                        start = max(0, match.start() - self.config_manager.context_length)
                        end = min(len(content), match.end() + self.config_manager.context_length)
                        context = content[start:end]
                        line_number = content.count('\n', 0, match.start()) + 1
                        results.append((line_number, context))
        except ValueError as e:
            print(f"ファイルの読み込みに失敗しました: {file_path} - {str(e)}")
        return (file_path, results) if results else None

    def match_search_terms(self, text: str) -> bool:
        if self.search_type == 'AND':
            return all(term.lower() in text.lower() for term in self.search_terms)
        elif self.search_type == 'OR':
            return any(term.lower() in text.lower() for term in self.search_terms)
        else:
            raise ValueError(f"Invalid search type: {self.search_type}")
