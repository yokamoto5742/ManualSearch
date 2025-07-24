import os
from typing import List, Tuple, Optional
from PyQt5.QtCore import QThread, pyqtSignal

from service.search_indexer import SearchIndexer
from service.file_searcher import FileSearcher as OriginalFileSearcher


class IndexedFileSearcher(QThread):

    result_found = pyqtSignal(str, list)
    progress_update = pyqtSignal(int)
    search_completed = pyqtSignal()
    index_status_changed = pyqtSignal(str)

    def __init__(
            self,
            directory: str,
            search_terms: List[str],
            include_subdirs: bool,
            search_type: str,
            file_extensions: List[str],
            context_length: int,
            use_index: bool = True,
            index_file_path: str = "search_index.json"
    ):
        super().__init__()
        self.directory = directory
        self.search_terms = search_terms
        self.include_subdirs = include_subdirs
        self.search_type = search_type
        self.file_extensions = file_extensions
        self.context_length = context_length
        self.use_index = use_index
        self.cancel_flag = False

        self.indexer = SearchIndexer(index_file_path)
        self.fallback_searcher = None

    def run(self) -> None:
        try:
            if self.use_index and self._is_index_available():
                self._search_with_index()
            else:
                self._search_without_index()
        except Exception as e:
            print(f"検索中にエラーが発生しました: {e}")
        finally:
            self.search_completed.emit()

    def _is_index_available(self) -> bool:
        if not os.path.exists(self.indexer.index_file_path):
            self.index_status_changed.emit("インデックスファイルが見つかりません")
            return False

        stats = self.indexer.get_index_stats()
        if stats["files_count"] == 0:
            self.index_status_changed.emit("インデックスが空です")
            return False

        return True

    def _search_with_index(self) -> None:
        try:
            results = self.indexer.search_in_index(self.search_terms, self.search_type)

            total_results = len(results)
            emitted_count = 0
            for i, (file_path, matches) in enumerate(results):
                if self.cancel_flag:
                    break

                if self._should_include_file(file_path):
                    self.result_found.emit(file_path, matches)
                    emitted_count += 1

                progress = int((i + 1) / total_results * 100) if total_results > 0 else 100
                self.progress_update.emit(progress)

        except Exception as e:
            print(f"インデックス検索でエラー: {e}")
            self.index_status_changed.emit("インデックス検索でエラーが発生しました")
            self._search_without_index()

    def _search_without_index(self) -> None:
        self.index_status_changed.emit("インデックスなしで検索中...")

        self.fallback_searcher = OriginalFileSearcher(
            self.directory,
            self.search_terms,
            self.include_subdirs,
            self.search_type,
            self.file_extensions,
            self.context_length
        )

        self.fallback_searcher.result_found.connect(self.result_found.emit)
        self.fallback_searcher.progress_update.connect(self.progress_update.emit)
        self.fallback_searcher.search_completed.connect(self.search_completed.emit)
        self.fallback_searcher.run()

    def _should_include_file(self, file_path: str) -> bool:
        try:
            if not os.path.isabs(file_path):
                file_path = os.path.abspath(file_path)

            file_dir = os.path.normpath(os.path.dirname(file_path))
            target_dir = os.path.normpath(os.path.abspath(self.directory))

            if self.include_subdirs:
                result = os.path.commonpath([file_dir, target_dir]) == target_dir
                print(f"フィルタリング: {file_path} -> {result} (target: {target_dir})")
                return result
            else:
                result = file_dir == target_dir
                print(f"フィルタリング: {file_path} -> {result} (target: {target_dir})")
                return result
        except (ValueError, OSError) as e:
            print(f"フィルタリングエラー: {file_path} - {e}")
            return True

    def cancel_search(self) -> None:
        self.cancel_flag = True
        if self.fallback_searcher:
            self.fallback_searcher.cancel_search()

    def create_or_update_index(self, directories: List[str], progress_callback: Optional[callable] = None) -> None:
        self.index_status_changed.emit("インデックスを作成中...")

        try:
            self.indexer.create_index(directories, progress_callback=progress_callback)

            stats = self.indexer.get_index_stats()
            self.index_status_changed.emit(
                f"インデックス作成完了: {stats['files_count']} ファイル, "
                f"{stats['index_file_size_mb']:.1f}MB"
            )

        except Exception as e:
            self.index_status_changed.emit(f"インデックス作成エラー: {e}")
            print(f"インデックス作成エラー: {e}")

    def get_index_stats(self) -> dict:
        return self.indexer.get_index_stats()

    def cleanup_index(self) -> None:
        try:
            removed_count = self.indexer.remove_missing_files()
            self.index_status_changed.emit(f"インデックスクリーンアップ完了: {removed_count} ファイルを削除")
        except Exception as e:
            self.index_status_changed.emit(f"インデックスクリーンアップエラー: {e}")

    def rebuild_index(self, directories: List[str]) -> None:
        try:
            self.indexer._initialize_new_index()
            self.create_or_update_index(directories)

        except Exception as e:
            self.index_status_changed.emit(f"インデックス再構築エラー: {e}")


class SearchMode:
    INDEX_ONLY = "index_only"
    FALLBACK = "fallback"
    TRADITIONAL = "traditional"


class SmartFileSearcher(IndexedFileSearcher):
    def __init__(self, *args, search_mode: str = SearchMode.FALLBACK, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_mode = search_mode

    def run(self) -> None:
        if self.search_mode == SearchMode.TRADITIONAL:
            self._search_without_index()
        elif self.search_mode == SearchMode.INDEX_ONLY:
            if self._is_index_available():
                self._search_with_index()
            else:
                self.index_status_changed.emit("インデックスが利用できません")
                self.search_completed.emit()
        else:  # FALLBACK
            super().run()

    def auto_update_index_if_needed(self, directories: List[str]) -> bool:
        try:
            stats = self.get_index_stats()

            if stats["files_count"] == 0:
                self.index_status_changed.emit("インデックスを新規作成します...")
                self.create_or_update_index(directories)
                return True

            return False

        except Exception as e:
            print(f"インデックス自動更新チェックでエラー: {e}")
            return False
