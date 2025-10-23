import logging
from typing import List, Optional, Tuple

import fitz

from service.search_matcher import SearchMatcher
from utils.constants import MAX_SEARCH_RESULTS_PER_FILE

logger = logging.getLogger(__name__)


class PDFSearchStrategy:
    def __init__(self, matcher: SearchMatcher):
        self.matcher = matcher

    def search(self, file_path: str) -> Optional[Tuple[str, List[Tuple[int, str]]]]:
        results = []

        try:
            with fitz.open(file_path) as doc:
                page_count = len(doc)
                for page_num in range(page_count):
                    page = doc[page_num]
                    try:
                        text = page.get_text()  # type: ignore
                    except AttributeError:
                        # Fallback for different PyMuPDF versions
                        try:
                            text = page.get_text("text")  # type: ignore
                        except Exception:
                            text = ""

                    if not self.matcher.match_search_terms(text):
                        continue

                    for search_term in self.matcher.search_terms:
                        contexts = self.matcher.extract_contexts(text, search_term)
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
