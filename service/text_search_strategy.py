import logging
from typing import List, Optional, Tuple

from service.search_matcher import SearchMatcher
from utils.helpers import read_file_with_auto_encoding

logger = logging.getLogger(__name__)


class TextSearchStrategy:
    """テキストファイル検索戦略"""

    def __init__(self, matcher: SearchMatcher):
        self.matcher = matcher

    def search(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        """テキストファイルを検索"""
        results = []

        try:
            content = read_file_with_auto_encoding(file_path)

            if not self.matcher.match_search_terms(content):
                return None

            for search_term in self.matcher.search_terms:
                contexts = self.matcher.extract_contexts_with_line_numbers(content, search_term)
                results.extend(contexts)

        except UnicodeDecodeError as e:
            logger.error(f"ファイルのデコードエラー: {file_path} - {e}")
        except ValueError as e:
            logger.error(f"ファイルの読み込みに失敗しました: {file_path} - {e}")

        return (file_path, results) if results else None
