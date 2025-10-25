import hashlib
import logging
import os
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from service.content_extractor import ContentExtractor
from service.index_storage import IndexStorage
from utils.constants import (
    FILE_EXTENSION_PDF,
    INDEX_DEFAULT_CONTEXT_LENGTH,
    INDEX_HASH_READ_CHUNK_SIZE,
    INDEX_MAX_RESULTS,
    PDF_TEXT_PAGE_SEPARATOR,
    SEARCH_TYPE_AND,
    SUPPORTED_FILE_EXTENSIONS,
    TEXT_LINE_SEPARATOR,
)

logger = logging.getLogger(__name__)


class SearchIndexer:
    """検索インデックスの作成と管理"""

    def __init__(self, index_file_path: str = "search_index.json") -> None:
        """初期化

        Args:
            index_file_path: インデックスファイルパス
        """
        self.storage = IndexStorage(index_file_path)
        self.content_extractor = ContentExtractor()
        self.index_data = self.storage.load()

    def create_index(self, directories: List[str], include_subdirs: bool = True,
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        file_list = self._get_file_list(directories, include_subdirs)
        total_files = len(file_list)
        logger.info(f"対象ファイル数: {total_files}")

        processed = 0
        updated_files = 0

        for file_path in file_list:
            try:
                if self._should_update_file(file_path):
                    self._process_file(file_path)
                    updated_files += 1

                processed += 1

                if progress_callback and callable(progress_callback):
                    progress_callback(processed, total_files)

                if processed % max(1, total_files // 10) == 0:
                    logger.info(f"進行状況: {processed}/{total_files} ({(processed/total_files)*100:.1f}%)")

            except Exception as e:
                logger.error(f"ファイル処理エラー: {file_path} - {e}")

        self.storage.save(self.index_data)

        logger.info(f"インデックス作成完了: {updated_files} ファイルを更新")

    def search_in_index(self, search_terms: List[str], search_type: str = SEARCH_TYPE_AND) -> List[Tuple[str, List[Tuple[int, str]]]]:
        results = []

        for file_path, file_info in self.index_data["files"].items():
            content = file_info.get("content", "")

            if self._match_search_terms(content, search_terms, search_type):
                matches = self._find_matches_in_content(content, search_terms, file_path)
                if matches:
                    results.append((file_path, matches))

        return results

    def get_index_stats(self) -> Dict:
        return self.storage.get_stats(self.index_data)

    def remove_missing_files(self) -> int:
        return self.storage.remove_missing_files(self.index_data)

    def _get_file_list(self, directories: List[str], include_subdirs: bool) -> List[str]:
        file_list = []

        for directory in directories:
            if not os.path.exists(directory):
                logger.warning(f"ディレクトリが見つかりません: {directory}")
                continue

            if include_subdirs:
                for root, _, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self._is_supported_file(file_path):
                            file_list.append(file_path)
            else:
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path) and self._is_supported_file(file_path):
                        file_list.append(file_path)

        return file_list

    def _is_supported_file(self, file_path: str) -> bool:
        return any(file_path.lower().endswith(ext) for ext in SUPPORTED_FILE_EXTENSIONS)

    def _should_update_file(self, file_path: str) -> bool:
        try:
            current_mtime = os.path.getmtime(file_path)
            current_size = os.path.getsize(file_path)

            if file_path not in self.index_data["files"]:
                return True

            stored_info = self.index_data["files"][file_path]

            return (stored_info.get("mtime", 0) != current_mtime or
                   stored_info.get("size", 0) != current_size)

        except OSError:
            return False

    def _process_file(self, file_path: str) -> None:
        try:
            content = self.content_extractor.extract_text_content(file_path)
            if content:
                file_stats = os.stat(file_path)
                file_hash = self._calculate_file_hash(file_path)

                self.index_data["files"][file_path] = {
                    "content": content,
                    "mtime": file_stats.st_mtime,
                    "size": file_stats.st_size,
                    "hash": file_hash,
                    "indexed_at": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"ファイル処理エラー: {file_path} - {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(INDEX_HASH_READ_CHUNK_SIZE)
                hash_md5.update(chunk)
        except Exception:
            return ""

        return hash_md5.hexdigest()

    def _match_search_terms(self, content: str, search_terms: List[str], search_type: str) -> bool:
        content_lower = content.lower()

        if search_type == SEARCH_TYPE_AND:
            return all(term.lower() in content_lower for term in search_terms)
        else:  # OR
            return any(term.lower() in content_lower for term in search_terms)

    def _find_matches_in_content(self, content: str, search_terms: List[str],
                               file_path: str, context_length: int = INDEX_DEFAULT_CONTEXT_LENGTH) -> List[Tuple[int, str]]:
        matches = []

        if file_path.lower().endswith(FILE_EXTENSION_PDF):
            pages = content.split(PDF_TEXT_PAGE_SEPARATOR)
            for page_num, page_content in enumerate(pages, 1):
                for term in search_terms:
                    if term.lower() in page_content.lower():
                        context = self._extract_context(page_content, term, context_length)
                        matches.append((page_num, context))
                        break  # ページごとに1つのマッチのみ
        else:
            lines = content.split(TEXT_LINE_SEPARATOR)
            for line_num, line in enumerate(lines, 1):
                for term in search_terms:
                    if term.lower() in line.lower():
                        context = self._extract_context(line, term, context_length)
                        matches.append((line_num, context))
                        break  # 行ごとに1つのマッチのみ

        return matches[:INDEX_MAX_RESULTS]

    def _extract_context(self, text: str, search_term: str, context_length: int) -> str:
        term_index = text.lower().find(search_term.lower())
        if term_index == -1:
            return text[:context_length * 2]

        start = max(0, term_index - context_length)
        end = min(len(text), term_index + len(search_term) + context_length)

        return text[start:end]
