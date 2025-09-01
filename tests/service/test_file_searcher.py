import os
from unittest.mock import patch, MagicMock

import pytest

from constants import SEARCH_TYPE_AND, SEARCH_TYPE_OR
from service.file_searcher import FileSearcher


class TestFileSearcher:
    """FileSearcherクラスのテスト"""
    
    @pytest.fixture
    def sample_directory(self, temp_dir):
        """テスト用ディレクトリ構造の作成"""
        # ルートディレクトリのファイル
        with open(os.path.join(temp_dir, 'root1.txt'), 'w', encoding='utf-8') as f:
            f.write("ルートディレクトリのPythonファイル")
        
        with open(os.path.join(temp_dir, 'root2.txt'), 'w', encoding='utf-8') as f:
            f.write("プログラミングとテストについて")
        
        # サブディレクトリ
        sub_dir = os.path.join(temp_dir, 'subdir')
        os.makedirs(sub_dir)
        
        with open(os.path.join(sub_dir, 'sub1.txt'), 'w', encoding='utf-8') as f:
            f.write("サブディレクトリのPythonテストファイル")
        
        with open(os.path.join(sub_dir, 'sub2.md'), 'w', encoding='utf-8') as f:
            f.write("# Markdownファイル\nPythonの自動テスト")
        
        return temp_dir
    
    def test_init(self, sample_directory, qapp):
        """初期化のテスト"""
        searcher = FileSearcher(
            directory=sample_directory,
            search_terms=['Python', 'テスト'],
            include_subdirs=True,
            search_type=SEARCH_TYPE_AND,
            file_extensions=['.txt', '.md'],
            context_length=50
        )
        
        assert searcher.directory == sample_directory
        assert searcher.search_terms == ['Python', 'テスト']
        assert searcher.include_subdirs == True
        assert searcher.search_type == SEARCH_TYPE_AND
        assert searcher.cancel_flag == False
    
    def test_match_search_terms_and(self, sample_directory, qapp):
        """AND検索のマッチングテスト"""
        searcher = FileSearcher(
            sample_directory, ['Python', 'テスト'], True,
            SEARCH_TYPE_AND, ['.txt'], 50
        )
        
        # 両方含む
        assert searcher.match_search_terms("Pythonのテストコード") == True
        # 片方のみ
        assert searcher.match_search_terms("Pythonのコード") == False
        assert searcher.match_search_terms("テストコード") == False
        # どちらも含まない
        assert searcher.match_search_terms("Javaのコード") == False
    
    def test_match_search_terms_or(self, sample_directory, qapp):
        """OR検索のマッチングテスト"""
        searcher = FileSearcher(
            sample_directory, ['Python', 'テスト'], True,
            SEARCH_TYPE_OR, ['.txt'], 50
        )
        
        # 両方含む
        assert searcher.match_search_terms("Pythonのテストコード") == True
        # 片方のみ
        assert searcher.match_search_terms("Pythonのコード") == True
        assert searcher.match_search_terms("テストコード") == True
        # どちらも含まない
        assert searcher.match_search_terms("Javaのコード") == False
    
    def test_search_text_file(self, sample_directory, qapp):
        """テキストファイル検索のテスト"""
        searcher = FileSearcher(
            sample_directory, ['Python'], True,
            SEARCH_TYPE_OR, ['.txt'], 30
        )
        
        file_path = os.path.join(sample_directory, 'root1.txt')
        result = searcher.search_text(file_path)
        
        assert result is not None
        assert result[0] == file_path
        assert len(result[1]) > 0
        assert 'Python' in result[1][0][1]
    
    @patch('fitz.open')
    def test_search_pdf_file(self, mock_fitz_open, sample_directory, qapp):
        """PDFファイル検索のテスト（モック使用）"""
        # PDFモックの設定
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDFファイルのPythonテスト内容"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)
        mock_doc.close = MagicMock()
        mock_fitz_open.return_value = mock_doc
        
        searcher = FileSearcher(
            sample_directory, ['Python'], True,
            SEARCH_TYPE_OR, ['.pdf'], 30
        )
        
        pdf_path = os.path.join(sample_directory, 'test.pdf')
        result = searcher.search_pdf(pdf_path)
        
        assert result is not None
        assert result[0] == pdf_path
        assert len(result[1]) > 0
        assert result[1][0][0] == 1  # ページ番号
    
    def test_cancel_search(self, sample_directory, qapp):
        """検索キャンセルのテスト"""
        searcher = FileSearcher(
            sample_directory, ['Python'], True,
            SEARCH_TYPE_OR, ['.txt'], 50
        )
        
        assert searcher.cancel_flag == False
        searcher.cancel_search()
        assert searcher.cancel_flag == True
    
    def test_search_with_subdirs(self, sample_directory, qapp):
        """サブディレクトリを含む検索のテスト"""
        results = []
        
        def collect_result(file_path, matches):
            results.append((file_path, matches))
        
        searcher = FileSearcher(
            sample_directory, ['Python'], True,
            SEARCH_TYPE_OR, ['.txt', '.md'], 50
        )
        searcher.result_found.connect(collect_result)
        
        # 検索実行（同期的にテスト）
        searcher.run()
        
        # サブディレクトリのファイルも含まれることを確認
        file_paths = [r[0] for r in results]
        assert any('root1.txt' in p for p in file_paths)
        assert any('sub1.txt' in p for p in file_paths)
        assert any('sub2.md' in p for p in file_paths)
    
    def test_search_without_subdirs(self, sample_directory, qapp):
        """サブディレクトリを除外した検索のテスト"""
        results = []
        
        def collect_result(file_path, matches):
            results.append((file_path, matches))
        
        searcher = FileSearcher(
            sample_directory, ['Python'], False,
            SEARCH_TYPE_OR, ['.txt', '.md'], 50
        )
        searcher.result_found.connect(collect_result)
        
        # 検索実行
        searcher.run()
        
        # ルートディレクトリのファイルのみ含まれることを確認
        file_paths = [r[0] for r in results]
        assert any('root1.txt' in p for p in file_paths)
        assert not any('sub1.txt' in p for p in file_paths)
        assert not any('sub2.md' in p for p in file_paths)
    
    def test_context_extraction(self, temp_dir, qapp):
        """コンテキスト抽出のテスト"""
        # 長いテキストファイルを作成
        long_text = "a" * 100 + " Python " + "b" * 100
        file_path = os.path.join(temp_dir, 'long.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(long_text)
        
        searcher = FileSearcher(
            temp_dir, ['Python'], True,
            SEARCH_TYPE_OR, ['.txt'], 20  # 前後20文字
        )
        
        result = searcher.search_text(file_path)
        assert result is not None
        
        context = result[1][0][1]
        # 前後のコンテキストが含まれることを確認
        assert len(context) > len('Python')
        assert 'Python' in context
        assert 'aaa' in context  # 前のコンテキスト
        assert 'bbb' in context  # 後のコンテキスト
