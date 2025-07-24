import os
import json
import shutil
import tempfile
import time
import pytest
from unittest.mock import patch, MagicMock, mock_open
from PyQt5.QtCore import QCoreApplication, QTimer
from PyQt5.QtWidgets import QApplication

from service.file_searcher import FileSearcher
from service.indexed_file_searcher import SmartFileSearcher, SearchMode
from service.search_indexer import SearchIndexer
from service.file_opener import FileOpener
from service.text_handler import highlight_text_file
from service.pdf_handler import highlight_pdf
from utils.config_manager import ConfigManager
from utils.helpers import read_file_with_auto_encoding, normalize_path
from constants import (
    SEARCH_TYPE_AND, SEARCH_TYPE_OR, SUPPORTED_FILE_EXTENSIONS,
    DEFAULT_CONTEXT_LENGTH, DEFAULT_FONT_SIZE
)


class TestSearchWorkflowIntegration:
    """検索ワークフロー全体の統合テスト"""
    
    @pytest.fixture
    def integration_setup(self, temp_dir):
        """統合テスト用の完全セットアップ"""
        # テストディレクトリ構造作成
        setup = {
            'root_dir': temp_dir,
            'sub_dir': os.path.join(temp_dir, 'subdir'),
            'files': {},
            'config_file': os.path.join(temp_dir, 'test_config.ini'),
            'index_file': os.path.join(temp_dir, 'test_index.json')
        }
        
        # サブディレクトリ作成
        os.makedirs(setup['sub_dir'])
        
        # テストファイル群作成
        test_files = [
            ('python_basic.txt', 'Python基礎プログラミング入門', temp_dir),
            ('python_advanced.md', '# Python上級技術\n\n高度なPython開発手法', temp_dir),
            ('java_tutorial.txt', 'Java言語でのプログラミング学習', temp_dir),
            ('web_development.md', '# Webプログラミング\n\nPythonとJavaScriptでのWeb開発', temp_dir),
            ('sub_python.txt', 'サブディレクトリのPythonファイル処理', setup['sub_dir']),
            ('sub_data.json', '{"language": "Python", "framework": "Django"}', setup['sub_dir'])
        ]
        
        for filename, content, directory in test_files:
            file_path = os.path.join(directory, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            setup['files'][filename] = file_path
        
        # 設定ファイル作成
        config_content = f"""[FileTypes]
extensions = .txt,.md,.json

[WindowSettings]
window_width = 1200
window_height = 800
font_size = 14

[SearchSettings]
context_length = 100

[UISettings]
html_font_size = 16

[IndexSettings]
index_file_path = {setup['index_file']}
use_index_search = True

[Directories]
list = {temp_dir}
last_directory = {temp_dir}
"""
        
        with open(setup['config_file'], 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return setup
    
    def test_end_to_end_traditional_search_workflow(self, integration_setup, qapp):
        """エンドツーエンド従来検索ワークフローテスト"""
        setup = integration_setup
        
        # ConfigManager作成
        config_manager = ConfigManager(setup['config_file'])
        
        # 検索結果収集
        search_results = []
        
        def collect_results(file_path, matches):
            search_results.append((file_path, matches))
        
        # FileSearcher作成・実行
        searcher = FileSearcher(
            directory=setup['root_dir'],
            search_terms=['Python'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_OR,
            file_extensions=config_manager.get_file_extensions(),
            context_length=config_manager.get_context_length()
        )
        
        searcher.result_found.connect(collect_results)
        searcher.run()
        
        # 結果検証
        assert len(search_results) >= 4  # Python含むファイルが複数見つかる
        
        # 各結果にPythonが含まれることを確認
        for file_path, matches in search_results:
            assert len(matches) > 0
            for position, context in matches:
                assert 'Python' in context or 'python' in context.lower()
        
        # サブディレクトリのファイルも含まれることを確認
        found_files = [result[0] for result in search_results]
        assert any('sub_python.txt' in f for f in found_files)
        assert any('sub_data.json' in f for f in found_files)
    
    def test_end_to_end_index_search_workflow(self, integration_setup, qapp):
        """エンドツーエンドインデックス検索ワークフローテスト"""
        setup = integration_setup
        
        # ConfigManager作成
        config_manager = ConfigManager(setup['config_file'])
        
        # インデックス作成
        indexer = SearchIndexer(setup['index_file'])
        indexer.create_index([setup['root_dir']], include_subdirs=True)
        
        # インデックス検索実行
        search_results = []
        
        def collect_results(file_path, matches):
            search_results.append((file_path, matches))
        
        index_searcher = SmartFileSearcher(
            directory=setup['root_dir'],
            search_terms=['Python', 'プログラミング'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_AND,
            file_extensions=config_manager.get_file_extensions(),
            context_length=config_manager.get_context_length(),
            use_index=True,
            index_file_path=setup['index_file'],
            search_mode=SearchMode.INDEX_ONLY
        )
        
        index_searcher.result_found.connect(collect_results)
        index_searcher.run()
        
        # 結果検証
        assert len(search_results) >= 2  # AND検索で両方含むファイル
        
        # 結果がインデックスから正しく取得されることを確認
        for file_path, matches in search_results:
            assert os.path.exists(file_path)
            assert len(matches) > 0
    
    def test_search_result_consistency_traditional_vs_index(self, integration_setup, qapp):
        """従来検索とインデックス検索の結果整合性テスト"""
        setup = integration_setup
        
        # ConfigManager作成
        config_manager = ConfigManager(setup['config_file'])
        
        # インデックス作成
        indexer = SearchIndexer(setup['index_file'])
        indexer.create_index([setup['root_dir']], include_subdirs=True)
        
        # 共通検索パラメータ
        search_params = {
            'directory': setup['root_dir'],
            'search_terms': ['Python'],
            'include_subdirs': True,
            'search_type': SEARCH_TYPE_OR,
            'file_extensions': config_manager.get_file_extensions(),
            'context_length': config_manager.get_context_length()
        }
        
        # 従来検索実行
        traditional_results = []
        traditional_searcher = FileSearcher(**search_params)
        traditional_searcher.result_found.connect(
            lambda f, m: traditional_results.append((f, len(m)))
        )
        traditional_searcher.run()
        
        # インデックス検索実行
        index_results = []
        index_searcher = SmartFileSearcher(
            use_index=True,
            index_file_path=setup['index_file'],
            search_mode=SearchMode.INDEX_ONLY,
            **search_params
        )
        index_searcher.result_found.connect(
            lambda f, m: index_results.append((f, len(m)))
        )
        index_searcher.run()
        
        # 結果整合性確認
        traditional_files = {normalize_path(f) for f, _ in traditional_results}
        index_files = {normalize_path(f) for f, _ in index_results}
        
        # 両方の検索方法で同じファイルが見つかることを確認
        common_files = traditional_files.intersection(index_files)
        assert len(common_files) >= 3  # 最低3ファイルは共通して見つかる
    
    def test_file_opening_integration_workflow(self, integration_setup):
        """ファイルオープン統合ワークフローテスト"""
        setup = integration_setup
        
        # ConfigManager作成
        config_manager = ConfigManager(setup['config_file'])
        
        # FileOpener作成
        file_opener = FileOpener(config_manager)
        
        # テキストファイルオープンテスト
        txt_file = setup['files']['python_basic.txt']
        
        with patch('service.file_opener.open_text_file') as mock_open_text:
            file_opener.open_file(txt_file, 1, ['Python'])
            
            mock_open_text.assert_called_once_with(
                txt_file, ['Python'], config_manager.get_html_font_size()
            )
            assert file_opener._last_opened_file == txt_file
        
        # Markdownファイルオープンテスト
        md_file = setup['files']['python_advanced.md']
        
        with patch('service.file_opener.open_text_file') as mock_open_text:
            file_opener.open_file(md_file, 1, ['Python', '上級'])
            
            mock_open_text.assert_called_once_with(
                md_file, ['Python', '上級'], config_manager.get_html_font_size()
            )
    
    def test_search_cancellation_workflow(self, integration_setup, qapp):
        """検索キャンセルワークフローテスト"""
        setup = integration_setup
        
        # 大量のダミーファイル作成（検索時間を延長）
        large_dir = os.path.join(setup['root_dir'], 'large_dataset')
        os.makedirs(large_dir)
        
        for i in range(100):
            dummy_file = os.path.join(large_dir, f'dummy_{i}.txt')
            with open(dummy_file, 'w') as f:
                f.write(f'Dummy content {i} with Python references')
        
        # ConfigManager作成
        config_manager = ConfigManager(setup['config_file'])
        
        # 検索開始と即座キャンセル
        searcher = FileSearcher(
            directory=setup['root_dir'],
            search_terms=['Python'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_OR,
            file_extensions=config_manager.get_file_extensions(),
            context_length=config_manager.get_context_length()
        )
        
        # 検索開始
        searcher.start()
        
        # 少し待ってからキャンセル
        QTimer.singleShot(100, searcher.cancel_search)
        
        # 検索完了まで待機
        searcher.wait(5000)  # 最大5秒待機
        
        # キャンセルフラグが設定されることを確認
        assert searcher.cancel_flag == True


class TestConfigurationChangeIntegration:
    """設定変更影響の統合テスト"""
    
    @pytest.fixture
    def config_setup(self, temp_dir):
        """設定テスト用セットアップ"""
        config_file = os.path.join(temp_dir, 'config_test.ini')
        
        # 初期設定作成
        initial_config = """[FileTypes]
extensions = .txt,.md

[WindowSettings]
font_size = 12

[SearchSettings]
context_length = 50

[UISettings]
html_font_size = 14

[IndexSettings]
use_index_search = False
"""
        
        with open(config_file, 'w') as f:
            f.write(initial_config)
        
        return {
            'config_file': config_file,
            'temp_dir': temp_dir
        }
    
    def test_file_extensions_change_impact(self, config_setup):
        """ファイル拡張子変更の影響テスト"""
        setup = config_setup
        
        # 複数形式のテストファイル作成
        test_files = {
            'test.txt': 'Text file content',
            'test.md': '# Markdown content',
            'test.py': 'Python script content',
            'test.json': '{"data": "json content"}'
        }
        
        for filename, content in test_files.items():
            file_path = os.path.join(setup['temp_dir'], filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        # 初期設定での検索
        config_manager1 = ConfigManager(setup['config_file'])
        initial_extensions = config_manager1.get_file_extensions()
        assert '.txt' in initial_extensions
        assert '.md' in initial_extensions
        assert '.py' not in initial_extensions
        
        # 拡張子設定変更
        config_manager1.set_file_extensions(['.txt', '.md', '.py', '.json'])
        
        # 新しい設定で再読み込み
        config_manager2 = ConfigManager(setup['config_file'])
        new_extensions = config_manager2.get_file_extensions()
        
        assert '.py' in new_extensions
        assert '.json' in new_extensions
        assert len(new_extensions) == 4
    
    def test_font_size_change_propagation(self, config_setup):
        """フォントサイズ変更の波及テスト"""
        setup = config_setup
        
        config_manager = ConfigManager(setup['config_file'])
        
        # 初期フォントサイズ確認
        assert config_manager.get_font_size() == 12
        assert config_manager.get_html_font_size() == 14
        
        # フォントサイズ変更
        config_manager.set_font_size(18)
        config_manager.set_html_font_size(20)
        
        # 設定が永続化されることを確認
        config_manager2 = ConfigManager(setup['config_file'])
        assert config_manager2.get_font_size() == 18
        assert config_manager2.get_html_font_size() == 20
        
        # FileOpenerでの設定反映確認
        file_opener = FileOpener(config_manager2)
        test_file = os.path.join(setup['temp_dir'], 'test.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        with patch('service.file_opener.open_text_file') as mock_open:
            file_opener._open_text_file(test_file, ['test'])
            
            # 新しいフォントサイズが使用されることを確認  
            mock_open.assert_called_with(test_file, ['test'], 20)
    
    def test_context_length_change_impact(self, config_setup):
        """コンテキスト長変更の影響テスト"""
        setup = config_setup
        
        # テストファイル作成
        test_file = os.path.join(setup['temp_dir'], 'context_test.txt')
        long_content = 'A' * 100 + ' Python ' + 'B' * 100  # 前後100文字ずつ
        with open(test_file, 'w') as f:
            f.write(long_content)
        
        config_manager = ConfigManager(setup['config_file'])
        
        # 初期コンテキスト長での検索
        initial_context_length = config_manager.get_context_length()
        assert initial_context_length == 50
        
        # コンテキスト長変更
        config_manager.set_context_length(30)
        
        # 新しい設定での検索確認
        config_manager2 = ConfigManager(setup['config_file'])
        assert config_manager2.get_context_length() == 30
    
    def test_index_search_toggle_impact(self, config_setup):
        """インデックス検索切り替えの影響テスト"""
        setup = config_setup
        
        config_manager = ConfigManager(setup['config_file'])
        
        # 初期状態確認（インデックス検索無効）
        assert config_manager.get_use_index_search() == False
        
        # インデックス検索有効化
        config_manager.set_use_index_search(True)
        
        # 設定永続化確認
        config_manager2 = ConfigManager(setup['config_file'])
        assert config_manager2.get_use_index_search() == True
        
        # インデックスファイルパス設定
        index_path = os.path.join(setup['temp_dir'], 'custom_index.json')
        config_manager2.set_index_file_path(index_path)
        
        # 設定反映確認
        config_manager3 = ConfigManager(setup['config_file'])
        assert config_manager3.get_index_file_path() == index_path


class TestErrorRecoveryIntegration:
    """エラー復旧統合テスト"""
    
    @pytest.fixture
    def error_test_setup(self, temp_dir):
        """エラーテスト用セットアップ"""
        return {
            'temp_dir': temp_dir,
            'config_file': os.path.join(temp_dir, 'error_config.ini'),
            'index_file': os.path.join(temp_dir, 'error_index.json'),
            'test_files': {}
        }
    
    def test_corrupted_config_recovery(self, error_test_setup):
        """破損設定ファイルからの復旧テスト"""
        setup = error_test_setup
        
        # 破損設定ファイル作成
        with open(setup['config_file'], 'w') as f:
            f.write("Invalid INI content [[[broken")
        
        # ConfigManagerが破損ファイルを処理できることを確認
        config_manager = ConfigManager(setup['config_file'])
        
        # デフォルト値が使用されることを確認
        assert isinstance(config_manager.get_file_extensions(), list)
        assert config_manager.get_font_size() >= 8  # 最小値以上
        assert config_manager.get_context_length() > 0
        
        # 新しい設定を保存して復旧
        config_manager.set_font_size(16)
        
        # 復旧後の設定が正常に動作することを確認
        config_manager2 = ConfigManager(setup['config_file'])
        assert config_manager2.get_font_size() == 16
    
    def test_corrupted_index_recovery(self, error_test_setup):
        """破損インデックスからの復旧テスト"""
        setup = error_test_setup
        
        # テストファイル作成
        test_file = os.path.join(setup['temp_dir'], 'recovery_test.txt')
        with open(test_file, 'w') as f:
            f.write('Recovery test content with Python')
        
        # 破損インデックスファイル作成
        with open(setup['index_file'], 'w') as f:
            f.write("Invalid JSON content {{{broken")
        
        # SmartFileSearcherがフォールバックすることを確認
        results = []
        
        def collect_results(file_path, matches):
            results.append((file_path, matches))
        
        searcher = SmartFileSearcher(
            directory=setup['temp_dir'],
            search_terms=['Python'],
            include_subdirs=False,
            search_type=SEARCH_TYPE_OR,
            file_extensions=['.txt'],
            context_length=100,
            use_index=True,
            index_file_path=setup['index_file'],
            search_mode=SearchMode.FALLBACK
        )
        
        searcher.result_found.connect(collect_results)
        searcher.run()
        
        # フォールバック検索で結果が得られることを確認
        assert len(results) >= 1
        assert 'recovery_test.txt' in results[0][0]
    
    def test_missing_template_recovery(self, error_test_setup):
        """テンプレートファイル欠損からの復旧テスト"""
        setup = error_test_setup
        
        # テストファイル作成
        test_file = os.path.join(setup['temp_dir'], 'template_test.txt')
        with open(test_file, 'w') as f:
            f.write('Template test content')
        
        # 存在しないテンプレートディレクトリを指定
        fake_template_dir = os.path.join(setup['temp_dir'], 'nonexistent_templates')
        
        with patch('service.text_handler.get_template_directory', return_value=fake_template_dir):
            # テンプレートファイル不存在でもエラーハンドリングされることを確認
            try:
                highlight_text_file(test_file, ['test'], 16)
                assert False, "Should have raised an exception"
            except (FileNotFoundError, Exception) as e:
                # 適切な例外が発生することを確認
                assert "テンプレート" in str(e) or "ファイル" in str(e)
    
    def test_disk_space_error_handling(self, error_test_setup):
        """ディスク容量不足エラーハンドリングテスト"""
        setup = error_test_setup
        
        # ディスク容量不足をシミュレート
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            config_manager = ConfigManager(setup['config_file'])
            
            # 設定保存時のエラーが適切に処理されることを確認
            try:
                config_manager.set_font_size(18)  # 内部でsave_config()が呼ばれる
                # エラーが発生しても例外が伝播しないことを確認
            except OSError:
                pytest.fail("OSError should be handled internally")
    
    def test_network_file_access_error_recovery(self, error_test_setup):
        """ネットワークファイルアクセスエラー復旧テスト"""
        setup = error_test_setup
        
        # ネットワークファイルパスをシミュレート
        network_path = '//server/share/test.txt'
        
        with patch('utils.helpers.is_network_file', return_value=True), \
             patch('socket.create_connection', side_effect=OSError("Network error")):
            
            # ネットワークエラーでアクセス不可と判定されることを確認
            from utils.helpers import check_file_accessibility
            result = check_file_accessibility(network_path)
            assert result == False
        
        # FileSearcherがネットワークエラーを適切に処理することを確認
        searcher = FileSearcher(
            directory=os.path.dirname(network_path),
            search_terms=['test'],
            include_subdirs=False,
            search_type=SEARCH_TYPE_OR,
            file_extensions=['.txt'],
            context_length=100
        )
        
        # エラーが発生しても検索処理が完了することを確認
        with patch.object(searcher, 'search_file', return_value=None):
            searcher.run()  # 例外が発生しないことを確認


class TestCrossModuleIntegration:
    """モジュール間連携統合テスト"""
    
    @pytest.fixture
    def cross_module_setup(self, temp_dir):
        """モジュール間テスト用セットアップ"""
        setup = {
            'temp_dir': temp_dir,
            'config_file': os.path.join(temp_dir, 'cross_config.ini'),
            'index_file': os.path.join(temp_dir, 'cross_index.json'),
            'template_dir': os.path.join(temp_dir, 'templates'),
            'files': {}
        }
        
        # テンプレートディレクトリとファイル作成
        os.makedirs(setup['template_dir'])
        template_content = """<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
<div>{{ content | safe }}</div>
</body>
</html>"""
        
        with open(os.path.join(setup['template_dir'], 'text_viewer.html'), 'w') as f:
            f.write(template_content)
        
        # 設定ファイル作成
        config_content = f"""[FileTypes]
extensions = .txt,.md

[WindowSettings]
font_size = 14

[SearchSettings]
context_length = 80

[UISettings]
html_font_size = 16

[IndexSettings]
index_file_path = {setup['index_file']}
use_index_search = True
"""
        
        with open(setup['config_file'], 'w') as f:
            f.write(config_content)
        
        # テストファイル作成
        test_files = [
            ('integration_test.txt', 'Integration test with Python programming'),
            ('module_test.md', '# Module Test\n\nPython integration testing'),
        ]
        
        for filename, content in test_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            setup['files'][filename] = file_path
        
        return setup
    
    def test_config_to_searcher_integration(self, cross_module_setup):
        """ConfigManager → FileSearcher連携テスト"""
        setup = cross_module_setup
        
        # ConfigManagerから設定読み込み
        config_manager = ConfigManager(setup['config_file'])
        
        # 設定値を使用してFileSearcher作成
        searcher = FileSearcher(
            directory=setup['temp_dir'],
            search_terms=['Python'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_OR,
            file_extensions=config_manager.get_file_extensions(),
            context_length=config_manager.get_context_length()
        )
        
        # 設定値が正しく反映されることを確認
        assert searcher.file_extensions == ['.txt', '.md']
        assert searcher.context_length == 80
        
        # 検索実行
        results = []
        searcher.result_found.connect(lambda f, m: results.append((f, m)))
        searcher.run()
        
        # 設定された拡張子のファイルのみが検索されることを確認
        assert len(results) == 2  # .txtと.mdファイル
    
    def test_searcher_to_file_opener_integration(self, cross_module_setup):
        """FileSearcher → FileOpener連携テスト"""
        setup = cross_module_setup
        
        config_manager = ConfigManager(setup['config_file'])
        
        # 検索実行
        searcher = FileSearcher(
            directory=setup['temp_dir'],
            search_terms=['Python'],
            include_subdirs=False,
            search_type=SEARCH_TYPE_OR,
            file_extensions=['.txt'],
            context_length=100
        )
        
        search_results = []
        searcher.result_found.connect(lambda f, m: search_results.append((f, m)))
        searcher.run()
        
        # 検索結果からファイルオープン
        assert len(search_results) > 0
        file_path, matches = search_results[0]
        position = matches[0][0]
        
        file_opener = FileOpener(config_manager)
        
        with patch('service.file_opener.open_text_file') as mock_open:
            file_opener.open_file(file_path, position, ['Python'])
            
            # FileOpenerが正しいパラメータで呼ばれることを確認
            mock_open.assert_called_once_with(
                file_path, ['Python'], config_manager.get_html_font_size()
            )
    
    def test_indexer_to_searcher_integration(self, cross_module_setup):
        """SearchIndexer → SmartFileSearcher連携テスト"""
        setup = cross_module_setup
        
        config_manager = ConfigManager(setup['config_file'])
        
        # インデックス作成
        indexer = SearchIndexer(setup['index_file'])
        indexer.create_index([setup['temp_dir']])
        
        # インデックス内容確認
        stats = indexer.get_index_stats()
        assert stats['files_count'] == 2
        
        # インデックス検索実行
        index_searcher = SmartFileSearcher(
            directory=setup['temp_dir'],
            search_terms=['Python'],
            include_subdirs=False,
            search_type=SEARCH_TYPE_OR,
            file_extensions=config_manager.get_file_extensions(),
            context_length=config_manager.get_context_length(),
            use_index=True,
            index_file_path=setup['index_file'],
            search_mode=SearchMode.INDEX_ONLY
        )
        
        index_results = []
        index_searcher.result_found.connect(lambda f, m: index_results.append((f, m)))
        index_searcher.run()
        
        # インデックスから正しく結果が取得されることを確認
        assert len(index_results) == 2
        for file_path, matches in index_results:
            assert 'Python' in matches[0][1]  # コンテキストにPythonが含まれる
    
    def test_config_to_text_handler_integration(self, cross_module_setup):
        """ConfigManager → TextHandler連携テスト"""
        setup = cross_module_setup
        
        config_manager = ConfigManager(setup['config_file'])
        
        # TextHandlerでの設定使用確認
        test_file = setup['files']['module_test.md']
        
        with patch('service.text_handler.get_template_directory', 
                  return_value=setup['template_dir']):
            result_path = highlight_text_file(
                test_file, 
                ['Python'], 
                config_manager.get_html_font_size()
            )
            
            # HTMLファイルが作成されることを確認
            assert os.path.exists(result_path)
            assert result_path.endswith('.html')
            
            # 内容確認
            with open(result_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Markdownが処理されていることを確認
            assert '<h1>' in html_content
            assert 'Python' in html_content
            assert '<span style=' in html_content  # ハイライト
            
            # クリーンアップ
            os.remove(result_path)
    
    def test_full_stack_integration(self, cross_module_setup, qapp):
        """フルスタック統合テスト"""
        setup = cross_module_setup
        
        # 全モジュール連携フロー
        # 1. 設定読み込み
        config_manager = ConfigManager(setup['config_file'])
        
        # 2. インデックス作成
        indexer = SearchIndexer(setup['index_file'])
        indexer.create_index([setup['temp_dir']])
        
        # 3. インデックス検索実行
        searcher = SmartFileSearcher(
            directory=setup['temp_dir'],
            search_terms=['Python', 'integration'],
            include_subdirs=False,
            search_type=SEARCH_TYPE_AND,
            file_extensions=config_manager.get_file_extensions(),
            context_length=config_manager.get_context_length(),
            use_index=True,
            index_file_path=setup['index_file']
        )
        
        search_results = []
        searcher.result_found.connect(lambda f, m: search_results.append((f, m)))
        searcher.run()
        
        # 4. ファイルオープン準備
        file_opener = FileOpener(config_manager)
        
        # 5. 全体フロー検証
        assert len(search_results) >= 1
        
        for file_path, matches in search_results:
            # ファイルが存在することを確認
            assert os.path.exists(file_path)
            
            # マッチ内容の確認
            assert len(matches) > 0
            position, context = matches[0]
            assert 'Python' in context
            assert 'integration' in context
            
            # ファイルオープンの確認
            with patch('service.file_opener.open_text_file') as mock_open:
                file_opener.open_file(file_path, position, ['Python', 'integration'])
                
                mock_open.assert_called_once_with(
                    file_path, 
                    ['Python', 'integration'], 
                    config_manager.get_html_font_size()
                )
        
        # インデックス統計確認
        stats = indexer.get_index_stats()
        assert stats['files_count'] >= 2
        assert stats['total_size_mb'] > 0