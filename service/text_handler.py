import os
import re
import tempfile
import webbrowser
from typing import List, Optional

import markdown

from utils.helpers import read_file_with_auto_encoding

def open_text_file(file_path: str, search_terms: List[str], html_font_size: int) -> None:
    try:
        highlighted_html_path = highlight_text_file(file_path, search_terms, html_font_size)
        webbrowser.open(f'file://{highlighted_html_path}')
    except Exception as e:
        raise Exception(f"テキストファイルを開けませんでした: {str(e)}")

def highlight_text_file(file_path: str, search_terms: List[str], html_font_size: int) -> str:
    try:
        content = read_file_with_auto_encoding(file_path)
    except ValueError as e:
        raise ValueError(f"ファイルの読み込みに失敗しました: {file_path} - {str(e)}")

    file_extension = os.path.splitext(file_path)[1].lower()
    is_markdown = file_extension == '.md'
    if is_markdown:
        content = markdown.markdown(content, extensions=['nl2br']) # 改行を<br>に変換

    content = highlight_search_terms(content, search_terms)
    html_content = generate_html_content(file_path, content, is_markdown, html_font_size)

    return create_temp_html_file(html_content)

def highlight_search_terms(content: str, search_terms: List[str]) -> str:
    colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
    for i, term in enumerate(search_terms):
        color = colors[i % len(colors)] # 色をループさせる
        content = re.sub(
            f'({re.escape(term.strip())})',
            f'<span style="background-color: {color};">\\1</span>',
            content,
            flags=re.IGNORECASE
        )
    return content

def generate_html_content(file_path: str, content: str, is_markdown: bool, html_font_size: int) -> str:
    return f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(file_path)}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            padding: 20px; 
            font-size: {html_font_size}px;
        }}
        pre {{ 
            background-color: #f4f4f4; 
            padding: 10px; 
            border-radius: 5px; 
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 0.8;
            margin: 0;
        }}
        .markdown-content {{
            line-height: 1.2;
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
    <div id="content">{'<pre>' if not is_markdown else '<div class="markdown-content">'}{content}{'</pre>' if not is_markdown else '</div>'}</div>
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
</html>'''

def create_temp_html_file(html_content: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
        tmp_file.write(html_content)
        return tmp_file.name
