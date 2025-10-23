import json
import logging
import os
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class IndexStorage:
    """検索インデックスの永続化を管理。"""

    def __init__(self, index_file_path: str = "search_index.json") -> None:
        """初期化。

        Args:
            index_file_path: インデックスファイルパス
        """
        self.index_file_path = index_file_path

    def load(self) -> Dict:
        if os.path.exists(self.index_file_path):
            try:
                with open(self.index_file_path, encoding='utf-8') as f:
                    index_data = json.load(f)
                logger.info(f"既存のインデックスを読み込みました: {len(index_data.get('files', {}))} ファイル")
                return index_data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.error(f"インデックスファイルの読み込みに失敗: {e}")
                return self._create_new_index()
        else:
            return self._create_new_index()

    def save(self, index_data: Dict) -> None:
        index_data["last_updated"] = datetime.now().isoformat()

        try:
            with open(self.index_file_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            logger.info(f"インデックスを保存しました: {self.index_file_path}")
        except Exception as e:
            logger.error(f"インデックス保存エラー: {e}")

    def get_stats(self, index_data: Dict) -> Dict:
        files_count = len(index_data.get("files", {}))
        total_size = sum(info.get("size", 0) for info in index_data.get("files", {}).values())

        return {
            "files_count": files_count,
            "total_size_mb": total_size / (1024 * 1024),
            "created_at": index_data.get("created_at"),
            "last_updated": index_data.get("last_updated"),
            "index_file_size_mb": os.path.getsize(self.index_file_path) / (1024 * 1024) if os.path.exists(self.index_file_path) else 0
        }

    def remove_missing_files(self, index_data: Dict) -> int:
        missing_files = []

        for file_path in index_data["files"]:
            if not os.path.exists(file_path):
                missing_files.append(file_path)

        for file_path in missing_files:
            del index_data["files"][file_path]

        if missing_files:
            self.save(index_data)
            logger.info(f"{len(missing_files)} 個の存在しないファイルをインデックスから削除しました")

        return len(missing_files)

    @staticmethod
    def _create_new_index() -> Dict:
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "files": {}
        }
