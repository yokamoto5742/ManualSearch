import tempfile
import re
from typing import List, Tuple, Optional

import PyPDF2
import fitz
from PyQt5.QtCore import QObject, pyqtSignal

class PDFHandler(QObject):
    progress_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def extract_text_from_pdf(self, file_path: str) -> List[str]:
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = len(reader.pages)
                text_content = []

                for i, page in enumerate(reader.pages):
                    text_content.append(page.extract_text())
                    self.progress_updated.emit(int((i + 1) / total_pages * 100))

                return text_content
        except Exception as e:
            print(f"PDFファイルの読み込み中にエラーが発生しました: {str(e)}")
            return []

    def search_pdf(self, file_path: str, search_terms: List[str], context_length: int) -> List[Tuple[int, str]]:
        results = []
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    for term in search_terms:
                        for match in re.finditer(re.escape(term), text, re.IGNORECASE):
                            start = max(0, match.start() - context_length)
                            end = min(len(text), match.end() + context_length)
                            context = text[start:end]
                            results.append((page_num + 1, context))
                    if len(results) >= 100:
                        break
        except Exception as e:
            print(f"PDFの検索中にエラーが発生しました: {file_path} - {str(e)}")
        return results

    def highlight_pdf(self, pdf_path: str, search_terms: List[str]) -> Optional[str]:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_path = tmp_file.name

            doc = fitz.open(pdf_path)
            colors = [
                (1, 1, 0),
                (0.5, 1, 0.5),
                (0.5, 0.7, 1),
                (1, 0.6, 0.4),
                (1, 0.7, 0.7)
            ]

            for page in doc:
                for i, term in enumerate(search_terms):
                    text_instances = page.search_for(term)
                    for inst in text_instances:
                        highlight = page.add_highlight_annot(inst)
                        highlight.set_colors(stroke=colors[i % len(colors)])
                        highlight.update()

            doc.save(tmp_path)
            doc.close()

            return tmp_path
        except Exception as e:
            print(f"PDFのハイライト中にエラーが発生しました: {str(e)}")
            return None

    def get_pdf_metadata(self, file_path: str) -> dict:
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                metadata = reader.metadata
                return {
                    'Title': metadata.get('/Title', ''),
                    'Author': metadata.get('/Author', ''),
                    'Subject': metadata.get('/Subject', ''),
                    'Creator': metadata.get('/Creator', ''),
                    'Producer': metadata.get('/Producer', ''),
                    'CreationDate': metadata.get('/CreationDate', ''),
                    'ModDate': metadata.get('/ModDate', ''),
                    'Pages': len(reader.pages)
                }
        except Exception as e:
            print(f"PDFメタデータの取得中にエラーが発生しました: {str(e)}")
            return {}

    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
        try:
            merger = PyPDF2.PdfMerger()
            for pdf in pdf_paths:
                merger.append(pdf)
            merger.write(output_path)
            merger.close()
            return True
        except Exception as e:
            print(f"PDFの結合中にエラーが発生しました: {str(e)}")
            return False

    def split_pdf(self, input_path: str, output_dir: str) -> List[str]:
        try:
            with open(input_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                output_paths = []
                for i in range(len(reader.pages)):
                    writer = PyPDF2.PdfWriter()
                    writer.add_page(reader.pages[i])
                    output_path = f"{output_dir}/page_{i+1}.pdf"
                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)
                    output_paths.append(output_path)
                return output_paths
        except Exception as e:
            print(f"PDFの分割中にエラーが発生しました: {str(e)}")
            return []
