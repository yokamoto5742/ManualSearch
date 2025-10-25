import logging
import os

import fitz

from utils.constants import FILE_EXTENSION_PDF
from utils.helpers import read_file_with_auto_encoding

logger = logging.getLogger(__name__)


class ContentExtractor:
    """ファイルからテキストコンテンツを抽出"""

    @staticmethod
    def extract_text_content(file_path: str) -> str:
        """ファイルのテキストコンテンツを抽出

        Args:
            file_path: ファイルパス

        Returns:
            抽出されたテキスト
        """
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == FILE_EXTENSION_PDF:
            return ContentExtractor._extract_pdf_content(file_path)
        else:
            return ContentExtractor._extract_text_file_content(file_path)

    @staticmethod
    def _extract_pdf_content(file_path: str) -> str:
        content = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    try:
                        text = page.get_text()
                    except AttributeError:
                        try:
                            text = page.get_text("text")
                        except Exception:
                            text = ""
                    if text:
                        content += text + "\n"
        except Exception as e:
            logger.error(f"PDF読み込みエラー: {file_path} - {e}")

        return content

    @staticmethod
    def _extract_text_file_content(file_path: str) -> str:
        try:
            result = read_file_with_auto_encoding(file_path)
            return result if result is not None else ""
        except Exception as e:
            logger.error(f"テキストファイル読み込みエラー: {file_path} - {e}")
            return ""
