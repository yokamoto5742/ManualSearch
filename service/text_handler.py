import html
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


def get_template_directory() -> str:
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた場合
        base_path = sys._MEIPASS
    else:
        # 通常の実行時
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, 'templates')


def create_jinja_environment() -> Environment:
    template_dir = get_template_directory()

    if not os.path.exists(template_dir):
        os.makedirs(template_dir)

    return Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True
    )


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
        content = markdown.markdown(content, extensions=['nl2br'])  # 改行を<br>に変換
    else:
        content = html.escape(content)

    content = highlight_search_terms(content, search_terms)

    html_content = generate_html_content(file_path, content, is_markdown, html_font_size, search_terms)

    return create_temp_html_file(html_content)


def highlight_search_terms(content: str, search_terms: List[str]) -> str:
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
) -> str:
    try:
        env = create_jinja_environment()
        template = env.get_template('text_viewer.html')

        file_extension = os.path.splitext(file_path)[1].lower()
        file_type = get_file_type_display_name(file_extension)

        template_vars = {
            'title': os.path.basename(file_path),
            'file_path': file_path,
            'file_type': file_type,
            'content': content,
            'is_markdown': is_markdown,
            'font_size': max(8, min(32, html_font_size or 16)),
            'search_terms': search_terms or [],
        }

        return template.render(**template_vars)

    except TemplateNotFound as e:
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {e}")
    except Exception as e:
        raise RuntimeError(f"HTMLテンプレートの処理中にエラーが発生しました: {e}")


def create_temp_html_file(html_content: str) -> str:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write(html_content)
            return tmp_file.name
    except IOError as e:
        raise IOError(f"一時HTMLファイルの作成に失敗しました: {e}")


def get_file_type_display_name(file_extension: str) -> str:
    file_type_map = {
        '.txt': 'テキストファイル',
        '.md': 'Markdownファイル',
        '.pdf': 'PDFファイル',
        '.html': 'HTMLファイル',
        '.css': 'CSSファイル',
    }
    return file_type_map.get(file_extension.lower(), '不明なファイル')


def validate_template_file() -> bool:
    template_dir = get_template_directory()
    template_path = os.path.join(template_dir, 'text_viewer.html')
    return os.path.exists(template_path)


def get_available_templates() -> List[str]:
    template_dir = get_template_directory()
    if not os.path.exists(template_dir):
        return []

    templates = []
    for file in os.listdir(template_dir):
        if file.endswith('.html'):
            templates.append(file)

    return templates
