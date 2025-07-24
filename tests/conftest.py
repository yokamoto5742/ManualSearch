import os
import tempfile
import shutil
import warnings
import psutil
import gc
from pathlib import Path
import pytest
from PyQt5.QtWidgets import QApplication

# PyQt5とSwig関連の警告を抑制
warnings.filterwarnings("ignore", category=DeprecationWarning, module=".*_bootstrap.*")
warnings.filterwarnings("ignore", "builtin type.*has no __module__ attribute", DeprecationWarning)

# 環境変数でQt関連のログレベルを設定
os.environ.setdefault('QT_LOGGING_RULES', '*.debug=false;qt.qpa.*=false')

# メモリ使用量追跡用グローバル変数
_initial_memory = None


def pytest_configure(config):
    """pytest設定時の初期化"""
    global _initial_memory
    _initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
    print(f"Initial memory usage: {_initial_memory:.2f}MB")


def pytest_unconfigure(config):
    """pytest終了時のクリーンアップ"""
    global _initial_memory
    if _initial_memory:
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_diff = final_memory - _initial_memory
        print(f"Final memory usage: {final_memory:.2f}MB (diff: {memory_diff:+.2f}MB)")


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
    try:
        shutil.rmtree(temp_path)
    except (OSError, PermissionError) as e:
        print(f"Warning: Failed to remove temp directory {temp_path}: {e}")


@pytest.fixture
def large_temp_dir():
    """大容量テスト用の一時ディレクトリ"""
    temp_path = tempfile.mkdtemp(prefix='large_test_')
    yield temp_path
    try:
        shutil.rmtree(temp_path)
    except (OSError, PermissionError) as e:
        print(f"Warning: Failed to remove large temp directory {temp_path}: {e}")


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
font_size = 14

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
def enhanced_config_file(temp_dir):
    """強化された設定ファイル（統合テスト用）"""
    config_path = os.path.join(temp_dir, 'enhanced_config.ini')
    config_content = f"""[FileTypes]
extensions = .pdf,.txt,.md,.py,.json

[WindowSettings]
window_width = 1200
window_height = 900
window_x = 100
window_y = 100
font_size = 16

[SearchSettings]
context_length = 150

[UISettings]
filename_font_size = 15
result_detail_font_size = 15
html_font_size = 18

[Paths]
acrobat_path = C:\\Program Files\\Adobe\\Acrobat DC\\Acrobat\\Acrobat.exe

[Directories]
list = {temp_dir}
last_directory = {temp_dir}

[PDFSettings]
timeout = 45
cleanup_temp_files = true
max_temp_files = 15

[IndexSettings]
index_file_path = {temp_dir}/enhanced_index.json
use_index_search = True
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
統合テストでの検索機能確認用のファイルです。
大容量テストでも使用される可能性があります。
パフォーマンステストでの基準ファイルとして活用。
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
- 統合テスト

### コード例
```python
def test_function():
    return "テスト"
```

### 特殊文字テスト
正規表現: `.*+?^${}()|[]\\`

### パフォーマンステスト用コンテンツ
このセクションはパフォーマンステストでの負荷生成に使用されます。
""" + "\n大容量コンテンツ: " + "A" * 1000

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

    yield md_path


@pytest.fixture
def sample_json_file(temp_dir):
    """テスト用のJSONファイルを作成"""
    json_path = os.path.join(temp_dir, 'sample.json')
    content = """{
    "language": "Python",
    "framework": "PyQt5",
    "testing": {
        "unit": "pytest",
        "integration": "manual",
        "performance": "custom"
    },
    "features": [
        "search",
        "index",
        "highlight",
        "integration"
    ],
    "large_data": """ + '"' + "test_data " * 100 + '"' + """
}"""

    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(content)

    yield json_path


@pytest.fixture
def sample_pdf_mock_content():
    """PDFファイルのモックコンテンツ（強化版）"""
    return {
        1: "これはPDFの1ページ目です。Pythonプログラミングについて詳しく説明します。統合テスト用のコンテンツも含まれています。",
        2: "2ページ目にはテスト手法について記載されています。パフォーマンステストの重要性も述べています。",
        3: "3ページ目では自動化テストの重要性について述べています。大容量データの処理方法も解説。",
        4: "4ページ目は統合テストの実装例を示しています。エラーハンドリングの手法も説明。",
        5: "5ページ目はパフォーマンス最適化のテクニックについて。メモリ使用量の監視方法も含む。"
    }


@pytest.fixture
def template_directory(temp_dir):
    """テンプレートディレクトリとファイルを作成"""
    template_dir = os.path.join(temp_dir, 'templates')
    os.makedirs(template_dir)

    # 基本テンプレート
    basic_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; font-size: {{ font_size }}px; }
        .highlight { background-color: yellow; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <div>{{ content | safe }}</div>
</body>
</html>"""

    with open(os.path.join(template_dir, 'text_viewer.html'), 'w', encoding='utf-8') as f:
        f.write(basic_template)

    # カスタムテンプレート
    custom_template = """<!DOCTYPE html>
<html>
<head><title>Custom - {{ title }}</title></head>
<body>
<div class="custom-content">{{ content | safe }}</div>
</body>
</html>"""

    with open(os.path.join(template_dir, 'custom_template.html'), 'w', encoding='utf-8') as f:
        f.write(custom_template)

    yield template_dir


@pytest.fixture
def performance_dataset(large_temp_dir):
    """パフォーマンステスト用データセット"""
    dataset_info = {
        'directory': large_temp_dir,
        'files': [],
        'total_size': 0
    }

    # 様々なサイズのファイルを作成
    file_configs = [
        ('small', 100, 50),  # 小ファイル: 100個、各50行
        ('medium', 20, 1000),  # 中ファイル: 20個、各1000行
        ('large', 5, 10000),  # 大ファイル: 5個、各10000行
    ]

    for size_type, count, lines in file_configs:
        for i in range(count):
            filename = f'{size_type}_file_{i:03d}.txt'
            file_path = os.path.join(large_temp_dir, filename)

            # コンテンツ生成
            content_lines = []
            for line_num in range(lines):
                if line_num % 10 == 0:
                    content_lines.append(f'Line {line_num}: Python programming content with search keywords')
                elif line_num % 7 == 0:
                    content_lines.append(f'Line {line_num}: Integration testing methodology and best practices')
                else:
                    content_lines.append(f'Line {line_num}: General content for performance testing purposes')

            content = '\n'.join(content_lines)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            file_size = os.path.getsize(file_path)
            dataset_info['files'].append({
                'path': file_path,
                'size': file_size,
                'lines': lines,
                'type': size_type
            })
            dataset_info['total_size'] += file_size

    print(f"Performance dataset created: {len(dataset_info['files'])} files, "
          f"{dataset_info['total_size'] / 1024 / 1024:.1f}MB total")

    yield dataset_info


@pytest.fixture
def memory_monitor():
    """メモリ使用量監視用フィクスチャ"""

    class MemoryMonitor:
        def __init__(self):
            self.process = psutil.Process()
            self.start_memory = None
            self.peak_memory = None
            self.measurements = []

        def start(self):
            gc.collect()
            self.start_memory = self.process.memory_info().rss / 1024 / 1024
            self.peak_memory = self.start_memory
            self.measurements = [self.start_memory]

        def sample(self):
            current_memory = self.process.memory_info().rss / 1024 / 1024
            self.measurements.append(current_memory)
            self.peak_memory = max(self.peak_memory, current_memory)
            return current_memory

        def get_stats(self):
            if not self.measurements:
                return {}

            return {
                'start_memory': self.start_memory,
                'peak_memory': self.peak_memory,
                'current_memory': self.measurements[-1],
                'memory_growth': self.measurements[-1] - self.start_memory,
                'measurements': self.measurements
            }

    return MemoryMonitor()


@pytest.fixture(autouse=True)
def test_cleanup():
    """各テスト後の自動クリーンアップ"""
    yield
    # ガベージコレクション実行
    gc.collect()

    # 一時ファイルクリーンアップ（PDF handler関連）
    try:
        import service.pdf_handler
        if hasattr(service.pdf_handler, '_temp_files'):
            for temp_file in service.pdf_handler._temp_files[:]:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    service.pdf_handler._temp_files.remove(temp_file)
                except (OSError, ValueError):
                    continue
    except ImportError:
        pass


# パフォーマンステスト用のカスタムマーカー関数
def pytest_runtest_setup(item):
    """テスト実行前のセットアップ"""
    if 'performance' in item.keywords:
        # パフォーマンステスト前のメモリクリーンアップ
        gc.collect()

    if 'large_dataset' in item.keywords:
        # 大容量テスト用のメモリ確認
        available_memory = psutil.virtual_memory().available / 1024 / 1024 / 1024  # GB
        if available_memory < 2.0:  # 2GB未満の場合
            pytest.skip("Insufficient memory for large dataset test")


def pytest_runtest_teardown(item):
    """テスト実行後のクリーンアップ"""
    if 'performance' in item.keywords or 'memory' in item.keywords:
        # パフォーマンステスト後の詳細クリーンアップ
        gc.collect()

        # メモリ使用量レポート
        current_memory = psutil.Process().memory_info().rss / 1024 / 1024
        if hasattr(item, '_memory_start'):
            memory_diff = current_memory - item._memory_start
            if memory_diff > 50:  # 50MB以上の差がある場合警告
                print(f"Warning: Memory increase of {memory_diff:.1f}MB in test {item.name}")


# コレクションフック（テスト収集時）
def pytest_collection_modifyitems(config, items):
    """テスト収集時の設定変更"""
    # スローテストのマーキング
    for item in items:
        if 'performance' in item.keywords or 'large_dataset' in item.keywords:
            item.add_marker(pytest.mark.slow)

        if 'integration' in item.keywords:
            # 統合テストには適切なタイムアウトを設定
            item.add_marker(pytest.mark.timeout(180))  # 3分


# カスタムアサーション（テスト支援用）
def assert_memory_within_limit(memory_usage_mb, limit_mb, test_name=""):
    """メモリ使用量制限アサーション"""
    assert memory_usage_mb <= limit_mb, (
        f"Memory usage exceeded limit in {test_name}: "
        f"{memory_usage_mb:.2f}MB > {limit_mb}MB"
    )


def assert_execution_time_within_limit(execution_time, limit_seconds, test_name=""):
    """実行時間制限アサーション"""
    assert execution_time <= limit_seconds, (
        f"Execution time exceeded limit in {test_name}: "
        f"{execution_time:.2f}s > {limit_seconds}s"
    )