import os
from typing import List, Tuple, Optional
from PyQt5.QtCore import QThread, pyqtSignal

from service.search_indexer import SearchIndexer
from service.file_searcher import FileSearcher as OriginalFileSearcher


class IndexedFileSearcher(QThread):
    """インデックスを使用した高速検索クラス"""

    result_found = pyqtSignal(str, list)
    progress_update = pyqtSignal(int)
    search_completed = pyqtSignal()
    index_status_changed = pyqtSignal(str)  # インデックス状態の変化を通知

    def __init__(
            self,
            directory: str,
            search_terms: List[str],
            include_subdirs: bool,
            search_type: str,
            file_extensions: List[str],
            context_length: int,
            use_index: bool = True,
            index_file_path: str = "search_index.json"  # デフォルト値を設定
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

        # インデックス管理
        self.indexer = SearchIndexer(index_file_path)

        # 従来の検索クラス（フォールバック用）
        self.fallback_searcher = None

    def run(self) -> None:
        """検索を実行"""
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
        """インデックスが利用可能かチェック"""
        if not os.path.exists(self.indexer.index_file_path):
            self.index_status_changed.emit("インデックスファイルが見つかりません")
            return False

        # インデックスが古すぎる場合は無効とする
        stats = self.indexer.get_index_stats()
        if stats["files_count"] == 0:
            self.index_status_changed.emit("インデックスが空です")
            return False

        self.index_status_changed.emit(f"インデックスを使用: {stats['files_count']} ファイル")
        return True

    def _search_with_index(self) -> None:
        """インデックスを使用した検索"""
        self.index_status_changed.emit("インデックスで検索中...")

        try:
            # インデックスから検索
            results = self.indexer.search_in_index(self.search_terms, self.search_type)

            # 結果を処理
            total_results = len(results)
            emitted_count = 0
            for i, (file_path, matches) in enumerate(results):
                if self.cancel_flag:
                    break

                # ディレクトリフィルタリング
                if self._should_include_file(file_path):
                    self.result_found.emit(file_path, matches)
                    emitted_count += 1

                # 進行状況更新
                progress = int((i + 1) / total_results * 100) if total_results > 0 else 100
                self.progress_update.emit(progress)

            self.index_status_changed.emit(f"インデックス検索完了: {emitted_count} ファイルを表示")

        except Exception as e:
            print(f"インデックス検索でエラー: {e}")
            self.index_status_changed.emit("インデックス検索でエラーが発生しました")
            # フォールバックとして従来の検索を実行
            self._search_without_index()

    def _search_without_index(self) -> None:
        """従来の方法で検索（フォールバック）"""
        self.index_status_changed.emit("従来の検索方法を使用中...")

        # 従来のFileSearcherを使用
        self.fallback_searcher = OriginalFileSearcher(
            self.directory,
            self.search_terms,
            self.include_subdirs,
            self.search_type,
            self.file_extensions,
            self.context_length
        )

        # シグナルを接続
        self.fallback_searcher.result_found.connect(self.result_found.emit)
        self.fallback_searcher.progress_update.connect(self.progress_update.emit)
        self.fallback_searcher.search_completed.connect(self.search_completed.emit)

        # 検索実行
        self.fallback_searcher.run()

    def _should_include_file(self, file_path: str) -> bool:
        """ファイルを結果に含めるべきかチェック"""
        try:
            # 指定されたディレクトリ内のファイルかチェック
            file_dir = os.path.normpath(os.path.dirname(file_path))
            target_dir = os.path.normpath(self.directory)

            if self.include_subdirs:
                # サブディレクトリを含む場合
                result = file_dir.startswith(target_dir)
                print(f"フィルタリング: {file_path} -> {result} (target: {target_dir})")
                return result
            else:
                # 直下のファイルのみ
                result = file_dir == target_dir
                print(f"フィルタリング: {file_path} -> {result} (target: {target_dir})")
                return result
        except Exception as e:
            print(f"フィルタリングエラー: {file_path} - {e}")
            return True  # エラーの場合は表示する

    def cancel_search(self) -> None:
        """検索をキャンセル"""
        self.cancel_flag = True
        if self.fallback_searcher:
            self.fallback_searcher.cancel_search()

    def create_or_update_index(self, directories: List[str], progress_callback: Optional[callable] = None) -> None:
        """インデックスを作成または更新"""
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
        """インデックスの統計情報を取得"""
        return self.indexer.get_index_stats()

    def cleanup_index(self) -> None:
        """インデックスをクリーンアップ（存在しないファイルを削除）"""
        try:
            removed_count = self.indexer.remove_missing_files()
            self.index_status_changed.emit(f"インデックスクリーンアップ完了: {removed_count} ファイルを削除")
        except Exception as e:
            self.index_status_changed.emit(f"インデックスクリーンアップエラー: {e}")

    def rebuild_index(self, directories: List[str]) -> None:
        """インデックスを完全に再構築"""
        try:
            # 既存のインデックスをクリア
            self.indexer._initialize_new_index()

            # 新しいインデックスを作成
            self.create_or_update_index(directories)

        except Exception as e:
            self.index_status_changed.emit(f"インデックス再構築エラー: {e}")


class SearchMode:
    """検索モードの定数"""
    INDEX_ONLY = "index_only"  # インデックスのみ使用
    FALLBACK = "fallback"  # インデックス→従来の順で試行
    TRADITIONAL = "traditional"  # 従来の検索のみ


class SmartFileSearcher(IndexedFileSearcher):
    """賢い検索クラス - 状況に応じて最適な検索方法を選択"""

    def __init__(self, *args, search_mode: str = SearchMode.FALLBACK, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_mode = search_mode

    def run(self) -> None:
        """検索モードに応じて最適な検索を実行"""
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
        """必要に応じてインデックスを自動更新"""
        try:
            stats = self.get_index_stats()

            # インデックスが存在しない場合
            if stats["files_count"] == 0:
                self.index_status_changed.emit("インデックスが存在しないため作成します...")
                self.create_or_update_index(directories)
                return True

            return False

        except Exception as e:
            print(f"インデックス自動更新チェックでエラー: {e}")
            return False