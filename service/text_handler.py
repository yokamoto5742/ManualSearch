import os
import re
import tempfile
import webbrowser
from typing import List

import markdown
from jinja2 import Environment, BaseLoader

from utils.helpers import read_file_with_auto_encoding


class StringTemplateLoader(BaseLoader):
    """文字列からテンプレートを読み込むカスタムローダー"""

    def __init__(self, template_string: str):
        self.template_string = template_string

    def get_source(self, environment, template):
        return self.template_string, None, lambda: True


# HTMLテンプレート定数
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            padding: 20px; 
            font-size: {{ font_size }}px;
            line-height: 1.6;
            color: #333;
        }
        pre { 
            background-color: #f4f4f4; 
            padding: 10px; 
            border-radius: 5px; 
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 0.8;
            margin: 0;
            border: 1px solid #ddd;
        }
        .markdown-content {
            line-height: 1.2;
        }
        #content {
            max-width: 100%;
            overflow-x: auto;
        }
        #controls {
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        #controls button {
            margin: 0 5px;
            padding: 5px 10px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        #controls button:hover {
            background-color: #0056b3;
        }
        .file-info {
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-left: 4px solid #007bff;
        }
    </style>
</head>
<body>
    <div id="controls">
        <button onclick="changeFontSize(1)">文字を大きく</button>
        <button onclick="changeFontSize(-1)">文字を小さく</button>
        <button onclick="toggleWordWrap()">文字の折り返し</button>
    </div>

    <div class="file-info">
        <h1>{{ title }}</h1>
        <p>ファイルパス: {{ file_path }}</p>
        <p>ファイルタイプ: {{ file_type }}</p>
    </div>

    <div id="content">
        {% if is_markdown %}
            <div class="markdown-content">{{ content | safe }}</div>
        {% else %}
            <pre>{{ content }}</pre>
        {% endif %}
    </div>

    <script>
        var currentFontSize = {{ font_size }};

        function changeFontSize(delta) {
            currentFontSize += delta;
            if (currentFontSize < 8) currentFontSize = 8;
            if (currentFontSize > 32) currentFontSize = 32;
            document.body.style.fontSize = currentFontSize + 'px';
        }

        function toggleWordWrap() {
            var content = document.getElementById('content');
            var pre = content.querySelector('pre');
            if (pre) {
                if (pre.style.whiteSpace === 'pre-wrap') {
                    pre.style.whiteSpace = 'pre';
                    pre.style.overflowX = 'auto';
                } else {
                    pre.style.whiteSpace = 'pre-wrap';
                    pre.style.overflowX = 'hidden';
                }
            }
        }

        // 検索語のハイライト効果を追加
        function highlightSearchTerms() {
            var highlights = document.querySelectorAll('span[style*="background-color"]');
            highlights.forEach(function(highlight) {
                highlight.style.transition = 'all 0.3s ease';
                highlight.addEventListener('mouseenter', function() {
                    this.style.transform = 'scale(1.05)';
                });
                highlight.addEventListener('mouseleave', function() {
                    this.style.transform = 'scale(1)';
                });
            });
        }

        // ページ読み込み時にハイライト効果を適用
        document.addEventListener('DOMContentLoaded', highlightSearchTerms);
    </script>
</body>
</html>'''


def open_text_file(file_path: str, search_terms: List[str], html_font_size: int) -> None:
    """テキストファイルを開いてブラウザで表示する"""
    try:
        highlighted_html_path = highlight_text_file(file_path, search_terms, html_font_size)
        webbrowser.open(f'file://{highlighted_html_path}')
    except Exception as e:
        raise Exception(f"テキストファイルを開けませんでした: {str(e)}")


def highlight_text_file(file_path: str, search_terms: List[str], html_font_size: int) -> str:
    """テキストファイルにハイライトを適用してHTMLファイルを生成する"""
    try:
        content = read_file_with_auto_encoding(file_path)
    except ValueError as e:
        raise ValueError(f"ファイルの読み込みに失敗しました: {file_path} - {str(e)}")

    file_extension = os.path.splitext(file_path)[1].lower()
    is_markdown = file_extension == '.md'

    if is_markdown:
        content = markdown.markdown(content, extensions=['nl2br'])  # 改行を<br>に変換

    content = highlight_search_terms(content, search_terms)
    html_content = generate_html_content(file_path, content, is_markdown, html_font_size)

    return create_temp_html_file(html_content)


def highlight_search_terms(content: str, search_terms: List[str]) -> str:
    """検索語をハイライトする"""
    colors = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']

    for i, term in enumerate(search_terms):
        if not term.strip():
            continue

        color = colors[i % len(colors)]  # 色をループさせる
        try:
            content = re.sub(
                f'({re.escape(term.strip())})',
                f'<span style="background-color: {color}; padding: 2px; border-radius: 2px;">\\1</span>',
                content,
                flags=re.IGNORECASE
            )
        except re.error as e:
            print(f"ハイライト処理でエラーが発生しました: {term} - {e}")
            continue

    return content


def generate_html_content(file_path: str, content: str, is_markdown: bool, html_font_size: int) -> str:
    """Jinja2テンプレートを使用してHTMLコンテンツを生成する"""
    # テンプレートローダーを作成
    loader = StringTemplateLoader(HTML_TEMPLATE)
    env = Environment(loader=loader)

    # テンプレートをレンダリング
    template = env.get_template('template')

    # ファイルタイプの判定
    file_extension = os.path.splitext(file_path)[1].lower()
    file_type_map = {
        '.txt': 'テキストファイル',
        '.md': 'Markdownファイル',
        '.pdf': 'PDFファイル'
    }

    return template.render(
        title=os.path.basename(file_path),
        file_path=file_path,
        file_type=file_type_map.get(file_extension, '不明なファイル'),
        content=content,
        is_markdown=is_markdown,
        font_size=html_font_size
    )


def create_temp_html_file(html_content: str) -> str:
    """一時HTMLファイルを作成する"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write(html_content)
            return tmp_file.name
    except IOError as e:
        raise IOError(f"一時HTMLファイルの作成に失敗しました: {e}")


def get_file_type_display_name(file_extension: str) -> str:
    """ファイル拡張子から表示名を取得する"""
    file_type_map = {
        '.txt': 'テキストファイル',
        '.md': 'Markdownファイル',
        '.pdf': 'PDFファイル'
    }
    return file_type_map.get(file_extension.lower(), '不明なファイル')
