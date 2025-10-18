import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple

from PyQt5.QtCore import QThread, pyqtSignal

from service.pdf_search_strategy import PDFSearchStrategy
from service.search_matcher import SearchMatcher
from service.text_search_strategy import TextSearchStrategy
from utils.constants import SEARCH_METHODS_MAPPING
from utils.helpers import check_file_accessibility, normalize_path

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

        # 検索戦略の初期化
        self.matcher = SearchMatcher(search_terms, search_type, context_length)
        self.pdf_strategy = PDFSearchStrategy(self.matcher)
        self.text_strategy = TextSearchStrategy(self.matcher)

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

    def _get_search_method(self, file_extension: str) -> Optional[callable]:
        method_name = SEARCH_METHODS_MAPPING.get(file_extension)
        if method_name:
            return getattr(self, method_name, None)
        return None

    def search_pdf(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        """PDF検索を戦略に委譲"""
        return self.pdf_strategy.search(file_path)

    def search_text(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        """テキスト検索を戦略に委譲"""
        return self.text_strategy.search(file_path)
