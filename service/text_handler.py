import os
import re
import sys
import tempfile
import webbrowser
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import markdown
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from utils.helpers import read_file_with_auto_encoding


@dataclass
class FileStats:
    """ファイルの統計情報"""
    char_count: int
    line_count: int
    highlight_count: int


def get_template_directory() -> str:
    """テンプレートディレクトリのパスを取得"""
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた場合
        base_path = sys._MEIPASS
    else:
        # 通常の実行時
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, 'templates')


def create_jinja_environment() -> Environment:
    """Jinja2環境を作成"""
    template_dir = get_template_directory()

    # テンプレートディレクトリが存在しない場合は作成
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
        # デフォルトテンプレートを作成
        create_default_template(template_dir)

    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True
    )


def create_default_template(template_dir: str) -> None:
    """デフォルトテンプレートファイルを作成"""
    default_template = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; font-size: {{ font_size }}px; }
        pre { background-color: #f4f4f4; padding: 10px; border-radius: 5px; }
        .markdown-content { line-height: 1.6; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div id="content">
        {% if is_markdown %}
            <div class="markdown-content">{{ content | safe }}</div>
        {% else %}
            <pre>{{ content }}</pre>
        {% endif %}
    </div>
</body>
</html>'''

    template_path = os.path.join(template_dir, 'text_viewer.html')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(default_template)


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

    # 統計情報を計算
    stats = calculate_file_stats(content, search_terms)

    if is_markdown:
        content = markdown.markdown(content, extensions=['nl2br'])  # 改行を<br>に変換

    content = highlight_search_terms(content, search_terms)
    html_content = generate_html_content(file_path, content, is_markdown, html_font_size, search_terms, stats)

    return create_temp_html_file(html_content)


def calculate_file_stats(content: str, search_terms: List[str]) -> FileStats:
    """ファイルの統計情報を計算"""
    char_count = len(content)
    line_count = content.count('\n') + 1 if content else 0

    # 検索語の一致数を計算
    highlight_count = 0
    for term in search_terms:
        if term.strip():
            highlight_count += len(re.findall(re.escape(term.strip()), content, re.IGNORECASE))

    return FileStats(
        char_count=char_count,
        line_count=line_count,
        highlight_count=highlight_count
    )


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


def generate_html_content(
        file_path: str,
        content: str,
        is_markdown: bool,
        html_font_size: int,
        search_terms: Optional[List[str]] = None,
        stats: Optional[FileStats] = None
) -> str:
    """外部テンプレートを使用してHTMLコンテンツを生成する"""
    try:
        env = create_jinja_environment()
        template = env.get_template('text_viewer.html')

        # ファイルタイプの判定
        file_extension = os.path.splitext(file_path)[1].lower()
        file_type = get_file_type_display_name(file_extension)

        # テンプレート変数を準備
        template_vars = {
            'title': os.path.basename(file_path),
            'file_path': file_path,
            'file_type': file_type,
            'content': content,
            'is_markdown': is_markdown,
            'font_size': html_font_size,
            'search_terms': search_terms or [],
            'stats': stats
        }

        return template.render(**template_vars)

    except TemplateNotFound as e:
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {e}")
    except Exception as e:
        raise RuntimeError(f"HTMLテンプレートの処理中にエラーが発生しました: {e}")


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
        '.pdf': 'PDFファイル',
        '.py': 'Pythonファイル',
        '.js': 'JavaScriptファイル',
        '.html': 'HTMLファイル',
        '.css': 'CSSファイル',
        '.json': 'JSONファイル',
        '.xml': 'XMLファイル',
        '.yaml': 'YAMLファイル',
        '.yml': 'YAMLファイル'
    }
    return file_type_map.get(file_extension.lower(), '不明なファイル')


def validate_template_file() -> bool:
    """テンプレートファイルの存在を確認"""
    template_dir = get_template_directory()
    template_path = os.path.join(template_dir, 'text_viewer.html')
    return os.path.exists(template_path)


def get_available_templates() -> List[str]:
    """利用可能なテンプレートファイルの一覧を取得"""
    template_dir = get_template_directory()
    if not os.path.exists(template_dir):
        return []

    templates = []
    for file in os.listdir(template_dir):
        if file.endswith('.html'):
            templates.append(file)

    return templates
