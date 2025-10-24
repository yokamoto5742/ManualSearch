from typing import List

from PyQt5.QtCore import QThread, pyqtSignal

from service.search_indexer import SearchIndexer


class IndexBuildThread(QThread):
    """インデックスをバックグラウンドで作成するスレッド"""
    # シグナル定義
    progress_updated = pyqtSignal(int, int)  # (処理済み, 総数)
    status_updated = pyqtSignal(str)  # ステータスメッセージ
    completed = pyqtSignal(bool)  # 成功/失敗

    def __init__(self, directories: List[str], index_file_path: str):
        """初期化

        Args:
            directories: インデックス対象のディレクトリリスト
            index_file_path: インデックスファイルパス
        """
        super().__init__()
        self.directories = directories
        self.indexer = SearchIndexer(index_file_path)
        self.should_cancel = False

    def run(self) -> None:
        """インデックス作成処理を実行"""
        try:
            self.status_updated.emit("インデックス作成開始...")

            # 進捗コールバック関数
            def progress_callback(processed: int, total: int) -> None:
                if not self.should_cancel:
                    self.progress_updated.emit(processed, total)

            self.indexer.create_index(self.directories, progress_callback=progress_callback)

            # 完了またはキャンセルを通知
            if not self.should_cancel:
                self.status_updated.emit("インデックス作成完了")
                self.completed.emit(True)
            else:
                self.status_updated.emit("インデックス作成がキャンセルされました")
                self.completed.emit(False)

        except Exception as e:
            self.status_updated.emit(f"エラー: {str(e)}")
            self.completed.emit(False)

    def cancel(self) -> None:
        """インデックス作成をキャンセル"""
        self.should_cancel = True
