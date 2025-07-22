from typing import List

from PyQt5.QtCore import QThread, pyqtSignal

from service.search_indexer import SearchIndexer


class IndexBuildThread(QThread):

    progress_updated = pyqtSignal(int, int)
    status_updated = pyqtSignal(str)
    completed = pyqtSignal(bool)

    def __init__(self, directories: List[str], index_file_path: str):
        super().__init__()
        self.directories = directories
        self.indexer = SearchIndexer(index_file_path)
        self.should_cancel = False

    def run(self):
        try:
            self.status_updated.emit("インデックス作成開始...")

            def progress_callback(processed: int, total: int):
                if not self.should_cancel:
                    self.progress_updated.emit(processed, total)

            self.indexer.create_index(self.directories, progress_callback=progress_callback)

            if not self.should_cancel:
                self.status_updated.emit("インデックス作成完了")
                self.completed.emit(True)
            else:
                self.status_updated.emit("インデックス作成がキャンセルされました")
                self.completed.emit(False)

        except Exception as e:
            self.status_updated.emit(f"エラー: {str(e)}")
            self.completed.emit(False)

    def cancel(self):
        self.should_cancel = True
