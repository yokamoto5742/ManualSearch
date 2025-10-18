import logging
import os

import fitz

from utils.helpers import read_file_with_auto_encoding

logger = logging.getLogger(__name__)


class ContentExtractor:
    @staticmethod
    def extract_text_content(file_path: str) -> str:
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.pdf':
            return ContentExtractor._extract_pdf_content(file_path)
        else:
            return ContentExtractor._extract_text_file_content(file_path)

    @staticmethod
    def _extract_pdf_content(file_path: str) -> str:
        content = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    content += page.get_text() + "\n"
        except Exception as e:
            logger.error(f"PDF読み込みエラー: {file_path} - {e}")

        return content

    @staticmethod
    def _extract_text_file_content(file_path: str) -> str:
        try:
            return read_file_with_auto_encoding(file_path)
        except Exception as e:
            logger.error(f"テキストファイル読み込みエラー: {file_path} - {e}")
            return ""
