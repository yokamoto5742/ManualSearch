import re
from typing import List, Tuple

from utils.constants import SEARCH_TYPE_AND, SEARCH_TYPE_OR


class SearchMatcher:
    """検索語マッチング処理を実行。"""

    def __init__(self, search_terms: List[str], search_type: str, context_length: int) -> None:
        """初期化。

        Args:
            search_terms: 検索語リスト
            search_type: 検索タイプ（AND/OR）
            context_length: コンテキスト長
        """
        self.search_terms = search_terms
        self.search_type = search_type
        self.context_length = context_length

    def match_search_terms(self, text: str) -> bool:
        """検索語がテキストにマッチするか判定。

        Args:
            text: 対象テキスト

        Returns:
            マッチした場合True
        """
        text_lower = text.lower()

        if self.search_type == SEARCH_TYPE_AND:
            return all(term.lower() in text_lower for term in self.search_terms)
        elif self.search_type == SEARCH_TYPE_OR:
            return any(term.lower() in text_lower for term in self.search_terms)

        return False

    def extract_contexts(self, text: str, search_term: str) -> List[str]:
        """検索語の周辺コンテキストを抽出"""
        contexts = []

        for match in re.finditer(re.escape(search_term), text, re.IGNORECASE):
            start = max(0, match.start() - self.context_length)
            end = min(len(text), match.end() + self.context_length)
            context = text[start:end]
            contexts.append(context)

        return contexts

    def extract_contexts_with_line_numbers(
        self,
        content: str,
        search_term: str
    ) -> List[Tuple[int, str]]:
        """検索語の周辺コンテキストと行番号を抽出。

        Args:
            content: 対象コンテンツ
            search_term: 検索語

        Returns:
            (行番号、コンテキスト)のタプルリスト
        """
        contexts = []

        for match in re.finditer(re.escape(search_term), content, re.IGNORECASE):
            line_number = content.count('\n', 0, match.start()) + 1
            start = max(0, match.start() - self.context_length)
            end = min(len(content), match.end() + self.context_length)
            context = content[start:end]
            contexts.append((line_number, context))

        return contexts
