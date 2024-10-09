import os
import re
import tempfile
from typing import List, Tuple, Optional

import markdown
from PyQt5.QtCore import QObject, pyqtSignal

from utils import read_file_with_auto_encoding

class TextHandler(QObject):
    progress_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()

    def read_text_file(self, file_path: str) -> str:
        try:
            return read_file_with_auto_encoding(file_path)
        except ValueError as e:
            print(f"ファイルの読み込みに失敗しました: {file_path} - {str(e)}")
            return ""

    def search_text(self, content: str, search_terms: List[str], context_length: int) -> List[Tuple[int, str]]:
        results = []
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for term in search_terms:
                if term.lower() in line.lower():
                    start = max(0, i - context_length)
                    end = min(len(lines), i + context_length + 1)
                    context = '\n'.join(lines[start:end])
                    results.append((i + 1, context))
        return results

    def highlight_text(self, content: str, search_terms: List[str]) -> str:
        highlighted = content
        for term in search_terms:
            highlighted = re.sub(
                f'({re.escape(term)})',
                r'<span style="background-color: yellow;">\1</span>',
                highlighted,
                flags=re.IGNORECASE
            )
        return highlighted

    def convert_markdown_to_html(self, content: str) -> str:
        return markdown.markdown(content)

    def create_highlighted_html(self, file_path: str, search_terms: List[str], html_font_size: int) -> Optional[str]:
        try:
            content = self.read_text_file(file_path)
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.md':
                content = self.convert_markdown_to_html(content)
            
            highlighted_content = self.highlight_text(content, search_terms)
            
            html_template = f'''
            <!DOCTYPE html>
            <html lang="ja">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{os.path.basename(file_path)}</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        line-height: 1.6; 
                        padding: 20px; 
                        font-size: {html_font_size}px;
                    }}
                    pre {{ 
                        background-color: #f4f4f4; 
                        padding: 10px; 
                        border-radius: 5px; 
                        white-space: pre-wrap;
                        word-wrap: break-word;
                    }}
                    #content {{
                        max-width: 100%;
                        overflow-x: auto;
                    }}
                    #controls {{
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        background-color: rgba(255, 255, 255, 0.8);
                        padding: 10px;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div id="controls">
                    <button onclick="changeFontSize(1)">文字を大きく</button>
                    <button onclick="changeFontSize(-1)">文字を小さく</button>
                    <button onclick="toggleWordWrap()">文字の折り返し</button>
                </div>
                <h1>{os.path.basename(file_path)}</h1>
                <div id="content">{'<pre>' if file_extension == '.txt' else ''}{highlighted_content}{'</pre>' if file_extension == '.txt' else ''}</div>
                <script>
                    var currentFontSize = {html_font_size};
                    function changeFontSize(delta) {{
                        currentFontSize += delta;
                        if (currentFontSize < 8) currentFontSize = 8;
                        if (currentFontSize > 32) currentFontSize = 32;
                        document.body.style.fontSize = currentFontSize + 'px';
                    }}
                    function toggleWordWrap() {{
                        var content = document.getElementById('content');
                        var pre = content.querySelector('pre');
                        if (pre) {{
                            if (pre.style.whiteSpace === 'pre-wrap') {{
                                pre.style.whiteSpace = 'pre';
                                pre.style.overflowX = 'auto';
                            }} else {{
                                pre.style.whiteSpace = 'pre-wrap';
                                pre.style.overflowX = 'hidden';
                            }}
                        }}
                    }}
                </script>
            </body>
            </html>
            '''

            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
                tmp_file.write(html_template)
                return tmp_file.name
        except Exception as e:
            print(f"HTMLファイルの作成中にエラーが発生しました: {str(e)}")
            return None

    def get_text_file_info(self, file_path: str) -> dict:
        try:
            content = self.read_text_file(file_path)
            return {
                'FileName': os.path.basename(file_path),
                'FileSize': os.path.getsize(file_path),
                'LineCount': len(content.split('\n')),
                'WordCount': len(content.split()),
                'CharCount': len(content)
            }
        except Exception as e:
            print(f"テキストファイル情報の取得中にエラーが発生しました: {str(e)}")
            return {}
