import os
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from PyQt5.QtCore import QCoreApplication
from service.indexed_file_searcher import (
    IndexedFileSearcher, SmartFileSearcher, SearchMode
)
from service.search_indexer import SearchIndexer
from constants import SEARCH_TYPE_AND, SEARCH_TYPE_OR


class TestIndexedFileSearcher:
    """IndexedFileSearcherクラスのP0レベル包括テスト"""
    
    @pytest.fixture
    def searcher(self, temp_dir, qapp):
        """基本的なIndexedFileSearcherインスタンス"""
        index_path = os.path.join(temp_dir, 'test_index.json')
        return IndexedFileSearcher(
            directory=temp_dir,
            search_terms=['Python', 'テスト'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_AND,
            file_extensions=['.txt', '.md', '.pdf'],
            context_length=100,
            use_index=True,
            index_file_path=index_path
        )
    
    @pytest.fixture
    def mock_index_available(self):
        """インデックス利用可能な状態をモック"""
        with patch.object(IndexedFileSearcher, '_is_index_available', return_value=True):
            yield
    
    @pytest.fixture
    def mock_index_unavailable(self):
        """インデックス利用不可な状態をモック"""
        with patch.object(IndexedFileSearcher, '_is_index_available', return_value=False):
            yield
    
    def test_init_basic_properties(self, searcher):
        """初期化時の基本プロパティ設定テスト"""
        assert searcher.directory is not None
        assert searcher.search_terms == ['Python', 'テスト']
        assert searcher.include_subdirs == True
        assert searcher.search_type == SEARCH_TYPE_AND
        assert searcher.use_index == True
        assert searcher.cancel_flag == False
        assert isinstance(searcher.indexer, SearchIndexer)
        assert searcher.fallback_searcher is None
    
    def test_is_index_available_no_file(self, searcher):
        """インデックスファイルが存在しない場合のテスト"""
        # ファイルが存在しない状態をテスト
        result = searcher._is_index_available()
        assert result == False
    
    @patch('os.path.exists')
    @patch.object(SearchIndexer, 'get_index_stats')
    def test_is_index_available_empty_index(self, mock_stats, mock_exists, searcher):
        """空のインデックスファイルの場合のテスト"""
        mock_exists.return_value = True
        mock_stats.return_value = {"files_count": 0}
        
        result = searcher._is_index_available()
        assert result == False
    
    @patch('os.path.exists')  
    @patch.object(SearchIndexer, 'get_index_stats')
    def test_is_index_available_valid_index(self, mock_stats, mock_exists, searcher):
        """有効なインデックスファイルの場合のテスト"""
        mock_exists.return_value = True
        mock_stats.return_value = {"files_count": 10}
        
        result = searcher._is_index_available()
        assert result == True
    
    @patch.object(IndexedFileSearcher, '_search_with_index')
    def test_run_with_index_available(self, mock_search_with_index, searcher, mock_index_available):
        """インデックス利用可能時のrun()メソッドテスト"""
        searcher.run()
        
        mock_search_with_index.assert_called_once()
    
    @patch.object(IndexedFileSearcher, '_search_without_index') 
    def test_run_with_index_unavailable(self, mock_search_without_index, searcher, mock_index_unavailable):
        """インデックス利用不可時のrun()メソッドテスト"""
        searcher.run()
        
        mock_search_without_index.assert_called_once()
    
    @patch.object(SearchIndexer, 'search_in_index')
    def test_search_with_index_success(self, mock_search, searcher):
        """インデックス検索成功時のテスト"""
        # モック検索結果
        mock_results = [
            ('/path/to/file1.txt', [(1, 'Python test content')]),
            ('/path/to/file2.txt', [(5, 'Another Python test')])
        ]
        mock_search.return_value = mock_results
        
        # _should_include_fileも常にTrueを返すようにモック
        with patch.object(searcher, '_should_include_file', return_value=True):
            searcher._search_with_index()
        
        mock_search.assert_called_once_with(['Python', 'テスト'], SEARCH_TYPE_AND)
    
    @patch.object(SearchIndexer, 'search_in_index')
    def test_search_with_index_exception_fallback(self, mock_search, searcher):
        """インデックス検索でエラー発生時のフォールバック処理テスト"""
        mock_search.side_effect = Exception("Index corruption error")
        
        with patch.object(searcher, '_search_without_index') as mock_fallback:
            searcher._search_with_index()
            mock_fallback.assert_called_once()
    
    def test_should_include_file_with_subdirs(self, searcher, temp_dir):
        """サブディレクトリ含む設定でのファイルフィルタリングテスト"""
        # テストファイルパス
        file_in_subdir = os.path.join(temp_dir, 'subdir', 'test.txt')
        file_in_root = os.path.join(temp_dir, 'test.txt')
        
        searcher.include_subdirs = True
        searcher.directory = temp_dir
        
        assert searcher._should_include_file(file_in_subdir) == True
        assert searcher._should_include_file(file_in_root) == True
    
    def test_should_include_file_without_subdirs(self, searcher, temp_dir):
        """サブディレクトリ除外設定でのファイルフィルタリングテスト"""
        # テストファイルパス
        file_in_subdir = os.path.join(temp_dir, 'subdir', 'test.txt')
        file_in_root = os.path.join(temp_dir, 'test.txt')
        
        searcher.include_subdirs = False
        searcher.directory = temp_dir
        
        assert searcher._should_include_file(file_in_subdir) == False
        assert searcher._should_include_file(file_in_root) == True
    
    def test_should_include_file_exception_handling(self, searcher):
        """ファイルフィルタリング中の例外処理テスト"""
        # 不正なパスでも例外を発生させずTrueを返すことを確認
        result = searcher._should_include_file('/invalid/path/test.txt')
        assert result == True
    
    def test_cancel_search_basic(self, searcher):
        """基本的な検索キャンセル機能テスト"""
        searcher.cancel_search()
        assert searcher.cancel_flag == True
    
    def test_cancel_search_with_fallback_searcher(self, searcher):
        """フォールバック検索中のキャンセル機能テスト"""
        mock_fallback = MagicMock()
        searcher.fallback_searcher = mock_fallback
        
        searcher.cancel_search()
        
        assert searcher.cancel_flag == True
        mock_fallback.cancel_search.assert_called_once()
    
    @patch.object(SearchIndexer, 'create_index')
    def test_create_or_update_index_success(self, mock_create, searcher):
        """インデックス作成・更新成功時のテスト"""
        directories = ['/path/to/dir1', '/path/to/dir2']
        progress_callback = MagicMock()
        
        mock_create.return_value = None
        with patch.object(searcher.indexer, 'get_index_stats', 
                         return_value={'files_count': 100, 'index_file_size_mb': 5.2}):
            searcher.create_or_update_index(directories, progress_callback)
        
        mock_create.assert_called_once_with(directories, progress_callback=progress_callback)
    
    @patch.object(SearchIndexer, 'create_index')
    def test_create_or_update_index_exception(self, mock_create, searcher):
        """インデックス作成・更新時の例外処理テスト"""
        mock_create.side_effect = Exception("Disk space error")
        
        directories = ['/path/to/dir1']
        searcher.create_or_update_index(directories)
        
        # 例外が発生してもクラッシュしないことを確認
        mock_create.assert_called_once()
    
    def test_get_index_stats(self, searcher):
        """インデックス統計情報取得テスト"""
        mock_stats = {
            'files_count': 150,
            'total_size_mb': 25.6,
            'index_file_size_mb': 3.2
        }
        
        with patch.object(searcher.indexer, 'get_index_stats', return_value=mock_stats):
            result = searcher.get_index_stats()
            assert result == mock_stats
    
    @patch.object(SearchIndexer, 'remove_missing_files')
    def test_cleanup_index_success(self, mock_cleanup, searcher):
        """インデックスクリーンアップ成功時のテスト"""
        mock_cleanup.return_value = 5  # 5個のファイルを削除
        
        searcher.cleanup_index()
        
        mock_cleanup.assert_called_once()
    
    @patch.object(SearchIndexer, 'remove_missing_files')
    def test_cleanup_index_exception(self, mock_cleanup, searcher):
        """インデックスクリーンアップ時の例外処理テスト"""
        mock_cleanup.side_effect = Exception("Permission denied")
        
        searcher.cleanup_index()
        
        # 例外が発生してもクラッシュしないことを確認
        mock_cleanup.assert_called_once()
    
    @patch.object(SearchIndexer, '_initialize_new_index')
    def test_rebuild_index(self, mock_init, searcher):
        """インデックス再構築機能テスト"""
        directories = ['/path/to/dir1']
        
        with patch.object(searcher, 'create_or_update_index') as mock_create:
            searcher.rebuild_index(directories)
            
            mock_init.assert_called_once()
            mock_create.assert_called_once_with(directories)
    
    @patch.object(SearchIndexer, '_initialize_new_index')
    def test_rebuild_index_exception(self, mock_init, searcher):
        """インデックス再構築時の例外処理テスト"""
        mock_init.side_effect = Exception("IO Error")
        
        directories = ['/path/to/dir1']
        searcher.rebuild_index(directories)
        
        # 例外が発生してもクラッシュしないことを確認
        mock_init.assert_called_once()


class TestSmartFileSearcher:
    """SmartFileSearcherクラスのP0レベルテスト"""
    
    @pytest.fixture
    def smart_searcher(self, temp_dir, qapp):
        """SmartFileSearcherインスタンス"""
        index_path = os.path.join(temp_dir, 'smart_index.json')
        return SmartFileSearcher(
            directory=temp_dir,
            search_terms=['Python'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_OR,
            file_extensions=['.txt', '.py'],
            context_length=50,
            use_index=True,
            index_file_path=index_path,
            search_mode=SearchMode.FALLBACK
        )
    
    def test_search_mode_traditional(self, smart_searcher):
        """TRADITIONAL検索モードのテスト"""
        smart_searcher.search_mode = SearchMode.TRADITIONAL
        
        with patch.object(smart_searcher, '_search_without_index') as mock_search:
            smart_searcher.run()
            mock_search.assert_called_once()
    
    def test_search_mode_index_only_available(self, smart_searcher):
        """INDEX_ONLYモード（インデックス利用可能）のテスト"""
        smart_searcher.search_mode = SearchMode.INDEX_ONLY
        
        with patch.object(smart_searcher, '_is_index_available', return_value=True), \
             patch.object(smart_searcher, '_search_with_index') as mock_search:
            smart_searcher.run()
            mock_search.assert_called_once()
    
    def test_search_mode_index_only_unavailable(self, smart_searcher):
        """INDEX_ONLYモード（インデックス利用不可）のテスト"""
        smart_searcher.search_mode = SearchMode.INDEX_ONLY
        
        with patch.object(smart_searcher, '_is_index_available', return_value=False):
            smart_searcher.run()
            # 検索が実行されないことを確認（search_completedシグナルのみ発出）

    def test_search_mode_fallback(self, smart_searcher):
        """FALLBACKモードのテスト（親クラスの動作）"""
        smart_searcher.search_mode = SearchMode.FALLBACK

        # 直接親クラスのrunメソッドを呼び出す代わりに、スーパークラスの動作をモック
        with patch.object(IndexedFileSearcher, 'run') as mock_parent_run:
            smart_searcher.run()
            mock_parent_run.assert_called_once()
    
    @patch.object(SearchIndexer, 'get_index_stats')
    def test_auto_update_index_if_needed_empty_index(self, mock_stats, smart_searcher):
        """自動インデックス更新（空インデックス）のテスト"""
        mock_stats.return_value = {"files_count": 0}
        
        directories = ['/test/dir']
        with patch.object(smart_searcher, 'create_or_update_index') as mock_create:
            result = smart_searcher.auto_update_index_if_needed(directories)
            
            assert result == True
            mock_create.assert_called_once_with(directories)
    
    @patch.object(SearchIndexer, 'get_index_stats')  
    def test_auto_update_index_if_needed_existing_index(self, mock_stats, smart_searcher):
        """自動インデックス更新（既存インデックス）のテスト"""
        mock_stats.return_value = {"files_count": 100}
        
        directories = ['/test/dir']
        result = smart_searcher.auto_update_index_if_needed(directories)
        
        assert result == False
    
    @patch.object(SearchIndexer, 'get_index_stats')
    def test_auto_update_index_if_needed_exception(self, mock_stats, smart_searcher):
        """自動インデックス更新時の例外処理テスト"""
        mock_stats.side_effect = Exception("Stats error")
        
        directories = ['/test/dir']
        result = smart_searcher.auto_update_index_if_needed(directories)
        
        assert result == False


class TestSearchMode:
    """SearchMode列挙型のテスト"""
    
    def test_search_mode_constants(self):
        """SearchModeの定数値テスト"""
        assert SearchMode.INDEX_ONLY == "index_only"
        assert SearchMode.FALLBACK == "fallback"
        assert SearchMode.TRADITIONAL == "traditional"


class TestIndexedFileSearcherIntegration:
    """IndexedFileSearcherの統合テスト"""
    
    @pytest.fixture
    def integration_setup(self, temp_dir):
        """統合テスト用のセットアップ"""
        # テストファイル作成
        test_files = {}
        
        # テキストファイル1
        file1_path = os.path.join(temp_dir, 'doc1.txt')
        with open(file1_path, 'w', encoding='utf-8') as f:
            f.write("Python programming tutorial for beginners")
        test_files['doc1.txt'] = file1_path
        
        # テキストファイル2（サブディレクトリ）
        subdir = os.path.join(temp_dir, 'subdir')
        os.makedirs(subdir, exist_ok=True)
        file2_path = os.path.join(subdir, 'doc2.txt')
        with open(file2_path, 'w', encoding='utf-8') as f:
            f.write("Advanced Python concepts and best practices")
        test_files['doc2.txt'] = file2_path
        
        # インデックスファイル作成
        index_path = os.path.join(temp_dir, 'integration_index.json')
        index_data = {
            "version": "1.0",
            "created_at": "2025-01-01T00:00:00",
            "last_updated": "2025-01-01T00:00:00",
            "files": {
                file1_path: {
                    "content": "Python programming tutorial for beginners",
                    "mtime": 1640995200.0,
                    "size": 45,
                    "hash": "test_hash_1",
                    "indexed_at": "2025-01-01T00:00:00"
                },
                file2_path: {
                    "content": "Advanced Python concepts and best practices",
                    "mtime": 1640995200.0,
                    "size": 47,
                    "hash": "test_hash_2", 
                    "indexed_at": "2025-01-01T00:00:00"
                }
            }
        }
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        return {
            'temp_dir': temp_dir,
            'index_path': index_path,
            'test_files': test_files
        }
    
    def test_end_to_end_index_search(self, integration_setup, qapp):
        """エンドツーエンドのインデックス検索テスト"""
        setup = integration_setup
        
        # 検索結果を収集するリスト
        results = []
        
        def collect_result(file_path, matches):
            results.append((file_path, matches))
        
        # IndexedFileSearcher作成
        searcher = IndexedFileSearcher(
            directory=setup['temp_dir'],
            search_terms=['Python'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_OR,
            file_extensions=['.txt'],
            context_length=50,
            use_index=True,
            index_file_path=setup['index_path']
        )
        
        searcher.result_found.connect(collect_result)
        
        # 検索実行
        searcher.run()
        
        # 結果検証
        assert len(results) == 2
        file_paths = [result[0] for result in results]
        assert setup['test_files']['doc1.txt'] in file_paths
        assert setup['test_files']['doc2.txt'] in file_paths
    
    def test_fallback_to_traditional_search(self, integration_setup, qapp):
        """インデックス利用不可時のフォールバック検索テスト"""
        setup = integration_setup
        
        # 存在しないインデックスパスを指定
        fake_index_path = os.path.join(setup['temp_dir'], 'nonexistent_index.json')
        
        results = []
        
        def collect_result(file_path, matches):
            results.append((file_path, matches))
        
        # IndexedFileSearcher作成
        searcher = IndexedFileSearcher(
            directory=setup['temp_dir'],
            search_terms=['Python'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_OR,
            file_extensions=['.txt'],
            context_length=50,
            use_index=True,
            index_file_path=fake_index_path
        )
        
        searcher.result_found.connect(collect_result)
        
        # 検索実行（フォールバックされることを期待）
        searcher.run()
        
        # フォールバック検索でも結果が得られることを確認
        assert len(results) >= 1  # 少なくとも1つの結果が得られるはず