import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open
from service.pdf_handler import (
    highlight_pdf, cleanup_temp_files, close_existing_acrobat_processes,
    wait_for_acrobat, navigate_to_page
)
from service.text_handler import (
    highlight_text_file, highlight_search_terms, get_file_type_display_name,
    create_temp_html_file
)


class TestPDFHandler:
    """PDFハンドラーのテスト"""
    
    @patch('fitz.open')
    def test_highlight_pdf(self, mock_fitz_open):
        """PDFハイライト機能のテスト"""
        # モックの設定
        mock_doc = MagicMock()
        mock_page = MagicMock()
        
        # search_forメソッドの戻り値（矩形のリスト）
        mock_rect = MagicMock()
        mock_page.search_for.return_value = [mock_rect]
        
        # add_highlight_annotメソッド
        mock_highlight = MagicMock()
        mock_page.add_highlight_annot.return_value = mock_highlight
        
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.save = MagicMock()
        mock_doc.close = MagicMock()
        
        mock_fitz_open.return_value = mock_doc
        
        # テスト実行
        result_path = highlight_pdf('/test/input.pdf', ['Python', 'テスト'])
        
        # 検証
        assert result_path.endswith('.pdf')
        assert os.path.exists(result_path)
        
        # メソッド呼び出しの確認
        assert mock_page.search_for.call_count == 2  # 2つの検索語
        mock_page.add_highlight_annot.assert_called()
        mock_highlight.set_colors.assert_called()
        mock_highlight.update.assert_called()
        mock_doc.save.assert_called_once()
        mock_doc.close.assert_called_once()
        
        # クリーンアップ
        if os.path.exists(result_path):
            os.remove(result_path)
    
    def test_cleanup_temp_files(self):
        """一時ファイルクリーンアップのテスト"""
        # 一時ファイルを作成
        temp_files = []
        for i in range(3):
            fd, path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            temp_files.append(path)
            
        # グローバル変数に追加（実際のコードの動作を模倣）
        import service.pdf_handler
        service.pdf_handler._temp_files = temp_files.copy()
        
        # クリーンアップ実行
        cleanup_temp_files()
        
        # ファイルが削除されたことを確認
        for path in temp_files:
            assert not os.path.exists(path)
        
        # リストが空になったことを確認
        assert len(service.pdf_handler._temp_files) == 0
    
    @patch('psutil.process_iter')
    @patch('time.sleep')
    def test_close_existing_acrobat_processes(self, mock_sleep, mock_process_iter):
        """Acrobatプロセス終了のテスト"""
        # モックプロセスの作成
        mock_process = MagicMock()
        mock_process.info = {'name': 'Acrobat.exe', 'pid': 1234}
        mock_process.terminate = MagicMock()
        mock_process.wait = MagicMock()
        
        mock_process_iter.return_value = [mock_process]
        
        # テスト実行
        close_existing_acrobat_processes()
        
        # 検証
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        mock_sleep.assert_called()
    
    @patch('psutil.Process')
    @patch('pyautogui.getActiveWindowTitle')
    @patch('time.sleep')
    def test_wait_for_acrobat(self, mock_sleep, mock_get_window, mock_process):
        """Acrobat起動待機のテスト"""
        # プロセスが実行中
        mock_proc_instance = MagicMock()
        mock_proc_instance.status.return_value = 'running'
        mock_process.return_value = mock_proc_instance
        
        # アクティブウィンドウのタイトル
        mock_get_window.return_value = "Adobe Acrobat"
        
        # テスト実行
        result = wait_for_acrobat(1234, timeout=1)
        
        assert result == True
        mock_process.assert_called_with(1234)
    
    @patch('pyautogui.hotkey')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    @patch('time.sleep')
    def test_navigate_to_page(self, mock_sleep, mock_press, mock_write, mock_hotkey):
        """ページナビゲーションのテスト"""
        # ページ1の場合（何もしない）
        navigate_to_page(1)
        mock_hotkey.assert_not_called()
        
        # ページ5に移動
        navigate_to_page(5)
        
        # キー操作の確認
        mock_hotkey.assert_any_call('ctrl', 'shift', 'n')
        mock_hotkey.assert_any_call('ctrl', 'a')
        mock_write.assert_called_with('5')
        mock_press.assert_called_with('enter')


class TestTextHandler:
    """テキストハンドラーのテスト"""
    
    def test_highlight_search_terms(self):
        """検索語ハイライトのテスト"""
        content = "PythonプログラミングとPythonテストについて学習"
        search_terms = ['Python', 'テスト']
        
        result = highlight_search_terms(content, search_terms)
        
        # ハイライトタグが追加されていることを確認
        assert '<span style=' in result
        assert 'background-color:' in result
        assert result.count('<span') == 3  # Python x2 + テスト x1
    
    def test_get_file_type_display_name(self):
        """ファイルタイプ表示名のテスト"""
        assert get_file_type_display_name('.txt') == 'テキストファイル'
        assert get_file_type_display_name('.md') == 'Markdownファイル'
        assert get_file_type_display_name('.pdf') == 'PDFファイル'
        assert get_file_type_display_name('.xyz') == '不明なファイル'
    
    def test_create_temp_html_file(self):
        """一時HTMLファイル作成のテスト"""
        html_content = "<html><body>テストHTML</body></html>"
        
        temp_path = create_temp_html_file(html_content)
        
        # ファイルが作成されたことを確認
        assert os.path.exists(temp_path)
        assert temp_path.endswith('.html')
        
        # 内容を確認
        with open(temp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == html_content
        
        # クリーンアップ
        os.remove(temp_path)
    
    @patch('utils.helpers.read_file_with_auto_encoding')
    @patch('markdown.markdown')
    @patch('service.text_handler.create_jinja_environment')
    def test_highlight_text_file(self, mock_env, mock_markdown, mock_read_file):
        """テキストファイルハイライト処理のテスト"""
        # モックの設定
        mock_read_file.return_value = "テストファイルの内容"
        mock_markdown.return_value = "<p>Markdownの内容</p>"
        
        # Jinjaテンプレートのモック
        mock_template = MagicMock()
        mock_template.render.return_value = "<html>レンダリング結果</html>"
        mock_env_instance = MagicMock()
        mock_env_instance.get_template.return_value = mock_template
        mock_env.return_value = mock_env_instance
        
        # テキストファイルのテスト
        with patch('service.text_handler.create_temp_html_file') as mock_create_html:
            mock_create_html.return_value = '/tmp/test.html'
            
            result = highlight_text_file('/test/file.txt', ['テスト'], 16)
            
            assert result == '/tmp/test.html'
            mock_read_file.assert_called_once_with('/test/file.txt')
            mock_template.render.assert_called_once()
            
        # Markdownファイルのテスト
        mock_read_file.reset_mock()
        with patch('service.text_handler.create_temp_html_file') as mock_create_html:
            mock_create_html.return_value = '/tmp/test_md.html'
            
            result = highlight_text_file('/test/file.md', ['テスト'], 16)
            
            assert result == '/tmp/test_md.html'
            mock_markdown.assert_called()
    
    def test_highlight_search_terms_edge_cases(self):
        """検索語ハイライトのエッジケーステスト"""
        # 空の検索語
        content = "テスト内容"
        result = highlight_search_terms(content, ['', '  '])
        assert result == content  # 変更されない
        
        # 特殊文字を含む検索語
        content = "正規表現の特殊文字 (.*?) をテスト"
        result = highlight_search_terms(content, ['(.*?)'])
        assert '<span' in result  # エスケープされてハイライトされる
        
        # 大文字小文字を区別しない
        content = "Python PYTHON python"
        result = highlight_search_terms(content, ['python'])
        assert result.count('<span') == 3
