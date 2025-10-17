import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

import fitz
from PyQt5.QtCore import QThread, pyqtSignal

from utils.constants import (
    MAX_SEARCH_RESULTS_PER_FILE,
    SEARCH_METHODS_MAPPING,
    SEARCH_TYPE_AND,
    SEARCH_TYPE_OR,
)
from utils.helpers import check_file_accessibility, normalize_path, read_file_with_auto_encoding

logger = logging.getLogger(__name__)


class FileSearcher(QThread):
    result_found = pyqtSignal(str, list)
    progress_update = pyqtSignal(int)
    search_completed = pyqtSignal()

    def __init__(
        self,
        directory: str,
        search_terms: List[str],
        include_subdirs: bool,
        search_type: str,
        file_extensions: List[str],
        context_length: int,
        global_search: bool = False,
        global_directories: Optional[List[str]] = None
    ):
        super().__init__()
        self.directory = directory
        self.search_terms = search_terms
        self.include_subdirs = include_subdirs
        self.search_type = search_type
        self.file_extensions = file_extensions
        self.context_length = context_length
        self.global_search = global_search
        self.global_directories = global_directories or []
        self.cancel_flag = False

    def run(self) -> None:
        """検索を実行"""
        directories = self._get_target_directories()
        self._execute_search(directories)
        self.search_completed.emit()

    def _get_target_directories(self) -> List[str]:
        if self.global_search and self.global_directories:
            return self.global_directories
        return [self.directory]

    def _execute_search(self, directories: List[str]) -> None:
        total_files = self._count_total_files(directories)
        processed_files = 0

        with ThreadPoolExecutor() as executor:
            for directory in directories:
                if self.cancel_flag or not os.path.isdir(directory):
                    continue

                files_processed = self._search_in_directory(executor, directory)
                processed_files += files_processed

                if total_files > 0:
                    progress = int((processed_files / total_files) * 100)
                    self.progress_update.emit(progress)

    def _count_total_files(self, directories: List[str]) -> int:
        total = 0
        for directory in directories:
            if not os.path.isdir(directory):
                continue
            
            try:
                if self.include_subdirs:
                    total += sum(len(files) for _, _, files in os.walk(directory))
                else:
                    files = os.listdir(directory)
                    total += len([f for f in files if os.path.isfile(os.path.join(directory, f))])
            except OSError as e:
                logger.warning(f"ディレクトリアクセスエラー: {directory} - {e}")
                continue
        
        return total

    def _search_in_directory(self, executor: ThreadPoolExecutor, directory: str) -> int:
        try:
            if self.include_subdirs:
                return self._search_with_subdirs(executor, directory)
            else:
                return self._search_without_subdirs(executor, directory)
        except OSError as e:
            logger.error(f"ディレクトリ検索エラー: {directory} - {e}")
            return 0

    def _search_with_subdirs(self, executor: ThreadPoolExecutor, directory: str) -> int:
        processed = 0
        for root, _, files in os.walk(directory):
            if self.cancel_flag:
                break
            self.process_files(executor, root, files)
            processed += len(files)
        return processed

    def _search_without_subdirs(self, executor: ThreadPoolExecutor, directory: str) -> int:
        files = [f for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f))]
        self.process_files(executor, directory, files)
        return len(files)

    def process_files(self, executor: ThreadPoolExecutor, root: str, files: List[str]) -> None:
        futures = []
        
        for file in files:
            if self.cancel_flag:
                break
            
            if not self._is_supported_file(file):
                continue
            
            file_path = os.path.join(root, file)
            future = executor.submit(self.search_file, file_path)
            futures.append(future)
        
        # 結果を収集
        for future in futures:
            if self.cancel_flag:
                break
            
            result = future.result()
            if result:
                file_path, matches = result
                self.result_found.emit(file_path, matches)

    def _is_supported_file(self, filename: str) -> bool:
        return any(filename.endswith(ext) for ext in self.file_extensions)

    def cancel_search(self) -> None:
        self.cancel_flag = True

    def search_file(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        normalized_path = normalize_path(file_path)
        
        if not check_file_accessibility(normalized_path):
            return None

        file_extension = os.path.splitext(normalized_path)[1].lower()
        search_method = self._get_search_method(file_extension)
        
        if not search_method:
            logger.warning(f"サポートされていないファイル形式: {file_extension}")
            return None

        try:
            return search_method(normalized_path)
        except Exception as e:
            logger.error(f"検索エラー: {normalized_path} - {e}")
            return None

    def _get_search_method(self, file_extension: str):
        method_name = SEARCH_METHODS_MAPPING.get(file_extension)
        if method_name:
            return getattr(self, method_name, None)
        return None

    def search_pdf(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        results = []
        
        try:
            with fitz.open(file_path) as doc:
                for page_num, page in enumerate(doc):
                    text = page.get_text()
                    
                    if not self.match_search_terms(text):
                        continue
                    
                    # マッチした検索語のコンテキストを抽出
                    for search_term in self.search_terms:
                        contexts = self._extract_contexts(text, search_term)
                        for context in contexts:
                            results.append((page_num + 1, context))
                        
                        if len(results) >= MAX_SEARCH_RESULTS_PER_FILE:
                            break
                    
                    if len(results) >= MAX_SEARCH_RESULTS_PER_FILE:
                        break
        
        except Exception as e:
            logger.error(f"PDFの処理中にエラーが発生しました: {file_path} - {e}")
            return None
        
        return (file_path, results) if results else None

    def search_text(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        results = []
        
        try:
            content = read_file_with_auto_encoding(file_path)
            
            if not self.match_search_terms(content):
                return None
            
            for search_term in self.search_terms:
                contexts = self._extract_contexts_with_line_numbers(content, search_term)
                results.extend(contexts)
        
        except UnicodeDecodeError as e:
            logger.error(f"ファイルのデコードエラー: {file_path} - {e}")
        except ValueError as e:
            logger.error(f"ファイルの読み込みに失敗しました: {file_path} - {e}")
        
        return (file_path, results) if results else None

    def _extract_contexts(self, text: str, search_term: str) -> List[str]:
        contexts = []
        
        for match in re.finditer(re.escape(search_term), text, re.IGNORECASE):
            start = max(0, match.start() - self.context_length)
            end = min(len(text), match.end() + self.context_length)
            context = text[start:end]
            contexts.append(context)
        
        return contexts

    def _extract_contexts_with_line_numbers(
        self, 
        content: str, 
        search_term: str
    ) -> List[Tuple[int, str]]:
        contexts = []
        
        for match in re.finditer(re.escape(search_term), content, re.IGNORECASE):
            line_number = content.count('\n', 0, match.start()) + 1
            start = max(0, match.start() - self.context_length)
            end = min(len(content), match.end() + self.context_length)
            context = content[start:end]
            contexts.append((line_number, context))
        
        return contexts

    def match_search_terms(self, text: str) -> bool:
        text_lower = text.lower()
        
        if self.search_type == SEARCH_TYPE_AND:
            return all(term.lower() in text_lower for term in self.search_terms)
        elif self.search_type == SEARCH_TYPE_OR:
            return any(term.lower() in text_lower for term in self.search_terms)
        
        return False
