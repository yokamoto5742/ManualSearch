import os
from unittest.mock import patch, MagicMock

import pytest

from service.search_indexer import SearchIndexer


class TestSearchIndexer:
    """SearchIndexerクラスのテスト"""
    
    @pytest.fixture
    def indexer(self, temp_dir):
        """テスト用のSearchIndexerインスタンス"""
        index_path = os.path.join(temp_dir, 'test_index.json')
        return SearchIndexer(index_path)
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """テスト用のサンプルファイル群"""
        files = []
        
        # テキストファイル1
        txt1_path = os.path.join(temp_dir, 'doc1.txt')
        with open(txt1_path, 'w', encoding='utf-8') as f:
            f.write("Pythonプログラミングの基礎について学習します。")
        files.append(txt1_path)
        
        # テキストファイル2
        txt2_path = os.path.join(temp_dir, 'doc2.txt')
        with open(txt2_path, 'w', encoding='utf-8') as f:
            f.write("テスト駆動開発とPythonの活用方法について説明します。")
        files.append(txt2_path)
        
        # Markdownファイル
        md_path = os.path.join(temp_dir, 'doc3.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Pythonテスト\n\n自動テストの重要性について")
        files.append(md_path)
        
        return files
    
    def test_init(self, indexer):
        """初期化のテスト"""
        assert indexer.storage.index_file_path.endswith('test_index.json')
        assert 'version' in indexer.index_data
        assert 'files' in indexer.index_data
        assert indexer.index_data['version'] == '1.0'
    
    def test_is_supported_file(self, indexer):
        """サポートファイル判定のテスト"""
        assert indexer._is_supported_file('test.txt') == True
        assert indexer._is_supported_file('test.md') == True
        assert indexer._is_supported_file('test.pdf') == True
        assert indexer._is_supported_file('test.doc') == False
        assert indexer._is_supported_file('test.exe') == False
    
    def test_create_index(self, indexer, temp_dir, sample_files):
        """インデックス作成のテスト"""
        # インデックス作成
        indexer.create_index([temp_dir])
        
        # インデックスが作成されたことを確認
        assert len(indexer.index_data['files']) == 3
        
        # 各ファイルがインデックスに含まれることを確認
        for file_path in sample_files:
            assert file_path in indexer.index_data['files']
            file_info = indexer.index_data['files'][file_path]
            assert 'content' in file_info
            assert 'mtime' in file_info
            assert 'size' in file_info
            assert 'hash' in file_info
    
    def test_search_in_index_and(self, indexer, temp_dir, sample_files):
        """AND検索のテスト"""
        indexer.create_index([temp_dir])
        
        # 両方のキーワードを含むファイルを検索
        results = indexer.search_in_index(['Python', 'テスト'])
        assert len(results) >= 1
        
        # 結果の検証
        found_files = [result[0] for result in results]
        assert any('doc3.md' in f for f in found_files)
    
    def test_search_in_index_or(self, indexer, temp_dir, sample_files):
        """OR検索のテスト"""
        indexer.create_index([temp_dir])
        
        # いずれかのキーワードを含むファイルを検索
        results = indexer.search_in_index(['プログラミング', 'テスト'], 'OR')
        assert len(results) >= 2
        
        # 全てのファイルが検索結果に含まれることを確認
        found_files = [result[0] for result in results]
        assert any('doc1.txt' in f for f in found_files)
        assert any('doc2.txt' in f or 'doc3.md' in f for f in found_files)
    
    def test_update_file_detection(self, indexer, temp_dir):
        """ファイル更新検出のテスト"""
        file_path = os.path.join(temp_dir, 'update_test.txt')
        
        # 初回作成
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("初期内容")
        
        indexer.create_index([temp_dir])
        initial_mtime = indexer.index_data['files'][file_path]['mtime']
        
        # ファイルを更新
        import time
        time.sleep(0.1)  # mtimeが変わるように少し待つ
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("更新された内容")
        
        # 更新が必要と判定されることを確認
        assert indexer._should_update_file(file_path) == True
    
    def test_remove_missing_files(self, indexer, temp_dir):
        """存在しないファイルの削除テスト"""
        # ダミーのファイル情報を追加
        indexer.index_data['files'] = {
            '/non/existent/file1.txt': {'content': 'dummy'},
            '/non/existent/file2.txt': {'content': 'dummy'},
            os.path.join(temp_dir, 'existing.txt'): {'content': 'exists'}
        }
        
        # 存在するファイルを作成
        with open(os.path.join(temp_dir, 'existing.txt'), 'w') as f:
            f.write("exists")
        
        # クリーンアップ実行
        removed_count = indexer.remove_missing_files()
        
        assert removed_count == 2
        assert len(indexer.index_data['files']) == 1
    
    def test_get_index_stats(self, indexer, temp_dir, sample_files):
        """インデックス統計情報取得のテスト"""
        indexer.create_index([temp_dir])
        
        stats = indexer.get_index_stats()
        
        assert stats['files_count'] == 3
        assert stats['total_size_mb'] > 0
        assert stats['created_at'] is not None
        assert stats['last_updated'] is not None
        assert stats['index_file_size_mb'] >= 0
    
    @patch('service.content_extractor.fitz.open')
    def test_extract_pdf_content(self, mock_fitz_open, indexer):
        """PDF内容抽出のテスト（モック使用）"""
        # PDFドキュメントのモック
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDFのテスト内容"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

        # コンテキストマネージャとして機能するよう設定
        mock_fitz_open.return_value.__enter__ = MagicMock(return_value=mock_doc)
        mock_fitz_open.return_value.__exit__ = MagicMock(return_value=False)

        content = indexer.content_extractor._extract_pdf_content('test.pdf')

        assert content == "PDFのテスト内容\n"
    
    def test_match_search_terms(self, indexer):
        """検索語マッチングのテスト"""
        content = "Pythonプログラミングとテスト手法について"
        
        # AND検索
        assert indexer._match_search_terms(content, ['Python', 'テスト'], 'AND') == True
        assert indexer._match_search_terms(content, ['Python', 'Java'], 'AND') == False
        
        # OR検索
        assert indexer._match_search_terms(content, ['Python', 'Java'], 'OR') == True
        assert indexer._match_search_terms(content, ['Java', 'C++'], 'OR') == False
        
        # 大文字小文字を区別しない
        assert indexer._match_search_terms(content, ['python', 'テスト'], 'AND') == True
