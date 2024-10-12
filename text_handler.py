import os
import re
import tempfile
import webbrowser
import markdown
from utils import read_file_with_auto_encoding

def open_text_file(file_path, search_terms, html_font_size):
    try:
        highlighted_html_path = highlight_text_file(file_path, search_terms, html_font_size)
        # デフォルトのブラウザで開く
        webbrowser.open(f'file://{highlighted_html_path}')
    except Exception as e:
        raise Exception(f"テキストファイルを開けませんでした: {str(e)}")

def highlight_text_file(file_path, search_terms, html_font_size):
    try:
        content = read_file_with_auto_encoding(file_path)

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.md':
            # nl2br拡張を使用してマークダウンをHTMLに変換
            content = markdown.markdown(content, extensions=['nl2br'])

        colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']
        for i, term in enumerate(search_terms):
            color = colors[i % len(colors)]
            content = re.sub(
                f'({re.escape(term.strip())})',
                f'<span style="background-color: {color};">\\1</span>',
                content,
                flags=re.IGNORECASE
            )

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
                    line-height: 1.0; 
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
            <div id="content">{'<pre>' if file_extension == '.txt' else ''}{content}{'</pre>' if file_extension == '.txt' else ''}</div>
            <script>
                var currentFontSize = {html_font_size};

                function changeFontSize(delta) {{
                    currentFontSize += delta;
                    if (currentFontSize < 8) currentFontSize = 8;  // 最小フォントサイズ
                    if (currentFontSize > 32) currentFontSize = 32;  // 最大フォントサイズ
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
    except ValueError as e:
        raise ValueError(f"ファイルの読み込みに失敗しました: {file_path} - {str(e)}")
