import os
import tempfile
import shutil
from pathlib import Path
import pytest
from PyQt5.QtWidgets import QApplication


@pytest.fixture(scope='session')
def qapp():
    """PyQt5アプリケーションのセッションスコープフィクスチャ"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def temp_dir():
    """一時ディレクトリを作成し、テスト終了後に削除"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def temp_config_file(temp_dir):
    """一時的な設定ファイルを作成"""
    config_path = os.path.join(temp_dir, 'test_config.ini')
    config_content = """[FileTypes]
extensions = .pdf,.txt,.md

[WindowSettings]
window_width = 1150
window_height = 900
window_x = 50
window_y = 50

[SearchSettings]
context_length = 100

[UISettings]
filename_font_size = 14
result_detail_font_size = 14
html_font_size = 16

[Paths]
acrobat_path = C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe

[Directories]
list = 
last_directory = 

[PDFSettings]
timeout = 30
cleanup_temp_files = true
max_temp_files = 10

[IndexSettings]
index_file_path = search_index.json
use_index_search = False
"""
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    yield config_path


@pytest.fixture
def sample_text_file(temp_dir):
    """テスト用のテキストファイルを作成"""
    text_path = os.path.join(temp_dir, 'sample.txt')
    content = """これはテストファイルです。
検索対象のテキストが含まれています。
Pythonプログラミングのテストです。
複数行にわたるテキストファイル。
検索キーワード: Python, テスト, プログラミング
"""
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    yield text_path


@pytest.fixture
def sample_markdown_file(temp_dir):
    """テスト用のMarkdownファイルを作成"""
    md_path = os.path.join(temp_dir, 'sample.md')
    content = """# テストドキュメント

## 概要
これはMarkdownファイルのテストです。

## 内容
- Python
- プログラミング
- テスト自動化

### コード例
```python
def test_function():
    return "テスト"
```
"""
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    yield md_path


@pytest.fixture
def mock_pdf_content():
    """PDFファイルのモックコンテンツ"""
    return {
        1: "これはPDFの1ページ目です。Pythonプログラミングについて説明します。",
        2: "2ページ目にはテスト手法について記載されています。",
        3: "3ページ目では自動化テストの重要性について述べています。"
    }
