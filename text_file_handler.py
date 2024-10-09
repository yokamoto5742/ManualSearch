import os
import re
import tempfile
import webbrowser
import markdown
from typing import List
from config_manager import ConfigManager

class TextFileHandler:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.html_font_size = self.config_manager.html_font_size

    def open_text_file(self, file_path: str):
        try:
            search_terms = self.config_manager.get_current_search_terms()
            highlighted_html_path = self.highlight_text_file(file_path, search_terms)
            webbrowser.open(f'file://{highlighted_html_path}')
        except Exception as e:
            raise ValueError(f"テキストファイルを開けませんでした: {str(e)}")

    def highlight_text_file(self, file_path: str, search_terms: List[str]) -> str:
        try:
            content = self.config_manager.read_file_with_auto_encoding(file_path)

            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension == '.md':
                content = markdown.markdown(content)

            colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
            for i, term in enumerate(search_terms):
                color = colors[i % len(colors)]
                content = re.sub(
                    f'({re.escape(term.strip())})',
                    f'<span style="background-color: {color};">\\1</span>',
                    content,
                    flags=re.IGNORECASE
                )

            html_template = self.create_html_template(os.path.basename(file_path), content)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
                tmp_file.write(html_template)
                return tmp_file.name
        except ValueError as e:
            raise ValueError(f"ファイルの読み込みに失敗しました: {file_path} - {str(e)}")

    def create_html_template(self, file_name: str, content: str) -> str:
        return f'''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{file_name}</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    padding: 20px; 
                    font-size: {self.html_font_size}px;
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
            <h1>{file_name}</h1>
            <div id="content">{'<pre>' if file_name.endswith('.txt') else ''}{content}{'</pre>' if file_name.endswith('.txt') else ''}</div>
            <script>
                var currentFontSize = {self.html_font_size};

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
