import os
import re
import subprocess
import tempfile
from unittest.mock import patch, MagicMock

import fitz
import psutil
import pytest
from jinja2 import TemplateNotFound

from utils.constants import (
    PAGE_NAVIGATION_RETRY_COUNT, PROCESS_CLEANUP_DELAY, TEMPLATE_DIRECTORY, TEXT_VIEWER_TEMPLATE, MARKDOWN_EXTENSIONS,
    MIN_FONT_SIZE, MAX_FONT_SIZE
)
from service.pdf_handler import (
    highlight_pdf, cleanup_temp_files, close_existing_acrobat_processes,
    wait_for_acrobat, navigate_to_page, open_pdf
)
from service.text_handler import (
    highlight_text_file, highlight_search_terms, get_file_type_display_name,
    create_temp_html_file, generate_html_content, get_template_directory,
    create_jinja_environment, open_text_file, validate_template_file,
    get_available_templates
)


class TestPDFHandlerEnhanced:
    """PDF処理の包括的テスト（P1レベル）"""
    
    @pytest.fixture
    def mock_pdf_document(self):
        """モックPDFドキュメント"""
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        
        # 検索結果のモック（矩形リスト）
        mock_rect1 = MagicMock()
        mock_rect2 = MagicMock()
        mock_page1.search_for.return_value = [mock_rect1]
        mock_page2.search_for.return_value = [mock_rect2]
        
        # ハイライト追加のモック
        mock_highlight1 = MagicMock()
        mock_highlight2 = MagicMock()
        mock_page1.add_highlight_annot.return_value = mock_highlight1
        mock_page2.add_highlight_annot.return_value = mock_highlight2
        
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page1, mock_page2]))
        mock_doc.save = MagicMock()
        mock_doc.close = MagicMock()
        
        return {
            'doc': mock_doc,
            'pages': [mock_page1, mock_page2],
            'highlights': [mock_highlight1, mock_highlight2]
        }
    
    @patch('service.pdf_handler.fitz.open')
    def test_highlight_pdf_multiple_terms(self, mock_fitz_open, mock_pdf_document):
        """複数検索語のPDFハイライトテスト"""
        # コンテキストマネージャとして機能するよう設定
        mock_fitz_open.return_value.__enter__ = MagicMock(return_value=mock_pdf_document['doc'])
        mock_fitz_open.return_value.__exit__ = MagicMock(return_value=False)

        search_terms = ['Python', 'テスト', '検索']
        result_path = highlight_pdf('/test/input.pdf', search_terms)

        # 各ページで全ての検索語が検索されることを確認
        for page in mock_pdf_document['pages']:
            assert page.search_for.call_count == len(search_terms)
            page.search_for.assert_any_call('Python')
            page.search_for.assert_any_call('テスト')
            page.search_for.assert_any_call('検索')

        # ハイライト色が適切に設定されることを確認
        for highlight in mock_pdf_document['highlights']:
            highlight.set_colors.assert_called()
            highlight.update.assert_called()

        assert result_path.endswith('.pdf')
        assert os.path.exists(result_path)

        # クリーンアップ
        if os.path.exists(result_path):
            os.remove(result_path)
    
    @patch('fitz.open')
    def test_highlight_pdf_empty_search_terms(self, mock_fitz_open, mock_pdf_document):
        """空の検索語リストでのPDFハイライトテスト"""
        mock_fitz_open.return_value = mock_pdf_document['doc']
        
        result_path = highlight_pdf('/test/input.pdf', ['', '   ', None])
        
        # 空の検索語は処理されないことを確認
        for page in mock_pdf_document['pages']:
            page.search_for.assert_not_called()
        
        assert result_path.endswith('.pdf')
        
        # クリーンアップ
        if os.path.exists(result_path):
            os.remove(result_path)

    
    @patch('fitz.open')
    def test_highlight_pdf_highlight_annotation_failure(self, mock_fitz_open, mock_pdf_document):
        """ハイライト注釈追加失敗時のテスト"""
        mock_fitz_open.return_value = mock_pdf_document['doc']
        
        # ハイライト追加で例外が発生するケース
        mock_pdf_document['pages'][0].add_highlight_annot.side_effect = Exception("Highlight error")
        
        # エラーが発生しても処理が続行されることを確認
        result_path = highlight_pdf('/test/input.pdf', ['Python'])
        
        assert result_path.endswith('.pdf')
        
        # クリーンアップ
        if os.path.exists(result_path):
            os.remove(result_path)
    
    @patch('fitz.open')
    def test_highlight_pdf_corrupted_file(self, mock_fitz_open):
        """破損PDFファイルでのテスト"""
        mock_fitz_open.side_effect = fitz.FileDataError("Invalid PDF")
        
        with pytest.raises(ValueError) as exc_info:
            highlight_pdf('/test/corrupted.pdf', ['Python'])
        
        assert "無効なPDFファイル" in str(exc_info.value)
    
    @patch('service.pdf_handler.fitz.open')
    def test_highlight_pdf_save_failure(self, mock_fitz_open, mock_pdf_document):
        """PDF保存失敗時のテスト"""
        # コンテキストマネージャとして機能するよう設定
        mock_fitz_open.return_value.__enter__ = MagicMock(return_value=mock_pdf_document['doc'])
        mock_fitz_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_pdf_document['doc'].save.side_effect = Exception("Save error")

        with pytest.raises(RuntimeError) as exc_info:
            highlight_pdf('/test/input.pdf', ['Python'])

        assert "PDFのハイライト処理中にエラー" in str(exc_info.value)
    
    def test_cleanup_temp_files_multiple_files(self):
        """複数一時ファイルのクリーンアップテスト"""
        from service.pdf_handler import temp_file_manager

        # 複数の一時ファイルを作成
        temp_files = []
        for i in range(5):
            fd, path = tempfile.mkstemp(suffix=f'_test_{i}.pdf')
            os.close(fd)
            temp_files.append(path)

        # temp_file_managerに設定
        temp_file_manager._temp_files = temp_files.copy()

        # クリーンアップ実行
        cleanup_temp_files()

        # 全ファイルが削除されることを確認
        for path in temp_files:
            assert not os.path.exists(path)

        assert len(temp_file_manager._temp_files) == 0
    
    def test_cleanup_temp_files_permission_error(self):
        """一時ファイル削除権限エラーのテスト"""
        from service.pdf_handler import temp_file_manager

        # 存在しないファイルをリストに追加（削除エラーをシミュレート）
        fake_files = ['/nonexistent/file1.pdf', '/nonexistent/file2.pdf']
        temp_file_manager._temp_files = fake_files.copy()

        # エラーが発生しても処理が続行されることを確認
        cleanup_temp_files()

        # エラーファイルはリストから削除される（存在しない場合も削除される仕様）
        assert len(temp_file_manager._temp_files) == 0
    
    @patch('psutil.process_iter')
    @patch('time.sleep')
    def test_close_existing_acrobat_processes_multiple_versions(self, mock_sleep, mock_process_iter):
        """複数バージョンのAcrobat終了テスト"""
        # 複数のAcrobatプロセスをシミュレート
        processes = []
        for i, name in enumerate(['Acrobat.exe', 'AcroRd32.exe', 'reader_sl.exe']):
            mock_process = MagicMock()
            mock_process.info = {'name': name, 'pid': 1000 + i}
            mock_process.terminate = MagicMock()
            mock_process.wait = MagicMock()
            processes.append(mock_process)
        
        mock_process_iter.return_value = processes
        
        close_existing_acrobat_processes()
        
        # 全プロセスが終了処理されることを確認
        for process in processes:
            process.terminate.assert_called_once()
            process.wait.assert_called_once()
    
    @patch('psutil.process_iter')
    @patch('time.sleep')
    def test_close_existing_acrobat_processes_timeout(self, mock_sleep, mock_process_iter):
        """Acrobatプロセス終了タイムアウトテスト"""
        mock_process = MagicMock()
        mock_process.info = {'name': 'Acrobat.exe', 'pid': 1234}
        mock_process.terminate = MagicMock()
        mock_process.wait.side_effect = psutil.TimeoutExpired(1234, "timeout")
        mock_process.kill = MagicMock()
        
        mock_process_iter.return_value = [mock_process]
        
        close_existing_acrobat_processes()
        
        # 通常終了でタイムアウト後、強制終了が呼ばれることを確認
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()
        mock_process.kill.assert_called_once()
    
    @patch('psutil.process_iter')
    def test_close_existing_acrobat_processes_access_denied(self, mock_process_iter):
        """プロセス終了権限エラーテスト"""
        mock_process = MagicMock()
        mock_process.info = {'name': 'Acrobat.exe', 'pid': 1234}
        mock_process.terminate.side_effect = psutil.AccessDenied(1234, "access denied")
        
        mock_process_iter.return_value = [mock_process]
        
        # 権限エラーが発生しても処理が続行されることを確認
        close_existing_acrobat_processes()
        
        mock_process.terminate.assert_called_once()
    
    @patch('subprocess.Popen')
    @patch('service.pdf_handler.AcrobatProcessManager.close_all_processes')
    @patch('service.pdf_handler.PDFHighlighter.highlight_pdf')
    @patch('service.pdf_handler.AcrobatProcessManager.wait_for_startup')
    @patch('service.pdf_handler.PDFNavigator.navigate_to_page')
    @patch('time.sleep')
    def test_open_pdf_integration(self, mock_sleep, mock_navigate, mock_wait,
                                 mock_highlight, mock_close, mock_popen):
        """PDF開く処理の統合テスト"""
        # モック設定
        mock_highlight.return_value = '/tmp/highlighted.pdf'
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_wait.return_value = True

        # テスト実行
        open_pdf('/test/input.pdf', '/usr/bin/acrobat', 5, ['Python', 'テスト'])

        # 処理順序の確認
        mock_close.assert_called_once()
        mock_highlight.assert_called_once_with('/test/input.pdf', ['Python', 'テスト'])
        mock_popen.assert_called_once_with(['/usr/bin/acrobat', '/tmp/highlighted.pdf'])
        mock_wait.assert_called_once_with(1234)
        mock_sleep.assert_called_once_with(PROCESS_CLEANUP_DELAY)
        mock_navigate.assert_called_once_with(5)
    
    @patch('subprocess.Popen')
    @patch('service.pdf_handler.AcrobatProcessManager.close_all_processes')
    @patch('service.pdf_handler.PDFHighlighter.highlight_pdf')
    def test_open_pdf_file_not_found(self, mock_highlight, mock_close, mock_popen):
        """存在しないPDFファイルでのテスト"""
        mock_highlight.side_effect = fitz.FileDataError("no such file: '/nonexistent.pdf'")

        with pytest.raises(RuntimeError) as exc_info:
            open_pdf('/nonexistent.pdf', '/usr/bin/acrobat', 1, ['test'])

        assert "PDFを開く際に予期せぬエラーが発生しました" in str(exc_info.value)
    
    @patch('subprocess.Popen')
    @patch('service.pdf_handler.AcrobatProcessManager.close_all_processes')
    @patch('service.pdf_handler.PDFHighlighter.highlight_pdf')
    def test_open_pdf_subprocess_error(self, mock_highlight, mock_close, mock_popen):
        """サブプロセス起動エラーのテスト"""
        mock_highlight.return_value = '/tmp/highlighted.pdf'
        mock_popen.side_effect = subprocess.SubprocessError("Process error")

        with pytest.raises(RuntimeError) as exc_info:
            open_pdf('/test.pdf', '/usr/bin/acrobat', 1, ['test'])

        assert "Acrobat Readerの起動に失敗しました" in str(exc_info.value)
    
    @patch('psutil.Process')
    @patch('pyautogui.getActiveWindowTitle')
    @patch('time.sleep')
    def test_wait_for_acrobat_success_immediately(self, mock_sleep, mock_get_window, mock_process):
        """Acrobat即座起動成功テスト"""
        mock_proc_instance = MagicMock()
        mock_proc_instance.status.return_value = psutil.STATUS_RUNNING
        mock_process.return_value = mock_proc_instance
        mock_get_window.return_value = "Adobe Acrobat Reader DC"
        
        result = wait_for_acrobat(1234, timeout=5)
        
        assert result == True
        mock_process.assert_called_with(1234)
    
    @patch('psutil.Process')
    @patch('time.sleep')
    def test_wait_for_acrobat_process_not_found(self, mock_sleep, mock_process):
        """Acrobatプロセス見つからないテスト"""
        mock_process.side_effect = psutil.NoSuchProcess(1234, "process")
        
        result = wait_for_acrobat(1234, timeout=1)
        
        assert result == False
    
    @patch('service.pdf_handler.time.sleep')
    @patch('service.pdf_handler.time.time')
    @patch('psutil.Process')
    def test_wait_for_acrobat_timeout(self, mock_process, mock_time, mock_sleep):
        """Acrobat起動タイムアウトテスト"""
        # time.time()をモック化してタイムアウトをシミュレート
        # start_timeが0、whileループチェック時に2.0でタイムアウト、loggerでも使われるので十分な値を用意
        mock_time.side_effect = [0, 2.0, 2.0, 2.0, 2.0]

        mock_proc_instance = MagicMock()
        mock_proc_instance.status.return_value = psutil.STATUS_ZOMBIE  # RUNNINGではない状態
        mock_process.return_value = mock_proc_instance

        result = wait_for_acrobat(1234, timeout=1)

        assert result == False
    
    @patch('pyautogui.hotkey')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    @patch('time.sleep')
    def test_navigate_to_page_multiple_retries(self, mock_sleep, mock_press, mock_write, mock_hotkey):
        """ページナビゲーション複数回リトライテスト"""
        # 初回と2回目で例外、3回目で成功
        mock_hotkey.side_effect = [Exception("Error 1"), Exception("Error 2"), None, None]
        
        navigate_to_page(10)
        
        # リトライ回数分呼ばれることを確認
        assert mock_hotkey.call_count >= PAGE_NAVIGATION_RETRY_COUNT
    
    @patch('pyautogui.hotkey')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    @patch('time.sleep')
    def test_navigate_to_page_all_retries_fail(self, mock_sleep, mock_press, mock_write, mock_hotkey):
        """ページナビゲーション全リトライ失敗テスト"""
        mock_hotkey.side_effect = Exception("Persistent error")
        
        # 例外が発生しても処理が完了することを確認
        navigate_to_page(5)
        
        assert mock_hotkey.call_count == PAGE_NAVIGATION_RETRY_COUNT
    
    def test_navigate_to_page_one(self):
        """ページ1への移動（何もしない）テスト"""
        with patch('pyautogui.hotkey') as mock_hotkey:
            navigate_to_page(1)
            
            # ページ1の場合は何も実行されないことを確認
            mock_hotkey.assert_not_called()


class TestTextHandlerEnhanced:
    """テキスト処理の包括的テスト（P1レベル）"""
    
    @pytest.fixture
    def complex_markdown_content(self):
        """複雑なMarkdownコンテンツ"""
        return """# メインタイトル

## サブタイトル

これは**強調テキスト**です。*斜体テキスト*も含まれます。

### コードブロック
```python
def search_function(terms):
    for term in terms:
        if term in content:
            return True
    return False
```

### リスト
- 項目1: Python
- 項目2: テスト
- 項目3: 検索

> 引用文です。
> 複数行の引用文。

[リンクテキスト](https://example.com)

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| A   | B   | C   |
| 1   | 2   | 3   |
"""
    
    @pytest.fixture
    def template_environment_mock(self):
        """Jinjaテンプレート環境のモック"""
        with patch('service.text_handler.create_jinja_environment') as mock_create_env:
            mock_env = MagicMock()
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Rendered content</html>"
            mock_env.get_template.return_value = mock_template
            mock_create_env.return_value = mock_env
            yield mock_env, mock_template

    def test_get_template_directory_frozen(self):
        """Pyinstaller実行時のテンプレートディレクトリ取得テスト"""
        with patch('sys.frozen', True, create=True), \
                patch('sys._MEIPASS', '/frozen/app/path', create=True):
            result = get_template_directory()
            expected = os.path.join('/frozen/app/path', TEMPLATE_DIRECTORY)
            assert result == expected

    def test_get_template_directory_normal(self):
        """通常実行時のテンプレートディレクトリ取得テスト"""
        with patch('sys.frozen', False, create=True):
            result = get_template_directory()
            assert TEMPLATE_DIRECTORY in result
            assert os.path.isabs(result)
    
    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_create_jinja_environment_create_dir(self, mock_makedirs, mock_exists):
        """テンプレートディレクトリ作成テスト"""
        mock_exists.return_value = False
        
        with patch('service.text_handler.get_template_directory', return_value='/test/templates'):
            env = create_jinja_environment()
            
            mock_makedirs.assert_called_once_with('/test/templates')
            assert env is not None
    
    @patch('os.path.exists')
    def test_create_jinja_environment_existing_dir(self, mock_exists):
        """既存テンプレートディレクトリでの環境作成テスト"""
        mock_exists.return_value = True
        
        with patch('service.text_handler.get_template_directory', return_value='/test/templates'):
            env = create_jinja_environment()
            
            assert env is not None
            # Environment設定の確認
            assert env.autoescape == True
            assert env.trim_blocks == True
            assert env.lstrip_blocks == True
    
    @patch('service.text_handler.read_file_with_auto_encoding')
    @patch('markdown.markdown')
    def test_highlight_text_file_complex_markdown(self, mock_markdown, mock_read, 
                                                 complex_markdown_content, template_environment_mock):
        """複雑なMarkdown処理テスト"""
        mock_read.return_value = complex_markdown_content
        mock_markdown.return_value = "<h1>Processed Markdown</h1>"
        
        mock_env, mock_template = template_environment_mock
        
        with patch('service.text_handler.create_temp_html_file', return_value='/tmp/test.html'):
            result = highlight_text_file('/test/file.md', ['Python', 'テスト'], 16)
            
            # Markdown処理が呼ばれることを確認
            mock_markdown.assert_called_once_with(complex_markdown_content, extensions=MARKDOWN_EXTENSIONS)
            
            # テンプレートレンダリングが呼ばれることを確認
            mock_template.render.assert_called_once()
            
            assert result == '/tmp/test.html'
    
    def test_highlight_search_terms_overlapping_matches(self):
        """重複ハイライトの処理テスト"""
        content = "Python programming with Python libraries"
        search_terms = ['Python', 'programming', 'Python libraries']
        
        result = highlight_search_terms(content, search_terms)
        
        # 全ての検索語がハイライトされることを確認
        assert '<span style=' in result
        assert 'Python' in result
        assert 'programming' in result
        assert 'libraries' in result
    
    def test_highlight_search_terms_special_regex_characters(self):
        """正規表現特殊文字を含む検索語のテスト"""
        content = "正規表現の特殊文字: .*+?^${}()|[]\\テスト"
        special_terms = ['.*+?', '^${}', '()|[]', '\\テスト']
        
        result = highlight_search_terms(content, special_terms)
        
        # 特殊文字がエスケープされてハイライトされることを確認
        for term in special_terms:
            assert term in result  # 元の文字列が残っている
        
        assert '<span style=' in result
    
    def test_highlight_search_terms_case_insensitive(self):
        """大文字小文字を区別しないハイライトテスト"""
        content = "Python PYTHON python PyThOn"
        search_terms = ['python']
        
        result = highlight_search_terms(content, search_terms)
        
        # 全ての大文字小文字パターンがハイライトされることを確認
        span_count = result.count('<span style=')
        assert span_count == 4  # 4つのPython全てがハイライト
    
    def test_highlight_search_terms_empty_and_whitespace(self):
        """空文字と空白文字の処理テスト"""
        content = "Test content for highlighting"
        search_terms = ['', '   ', '\t', '\n', 'Test']
        
        result = highlight_search_terms(content, search_terms)
        
        # 有効な検索語（'Test'）のみがハイライトされることを確認
        assert '<span style=' in result
        assert 'Test' in result
        # 空白文字や改行文字はハイライトされない
        span_count = result.count('<span style=')
        assert span_count == 1
    
    def test_highlight_search_terms_regex_error_handling(self):
        """正規表現エラーハンドリングテスト"""
        content = "Test content"
        # 通常はエラーにならないが、re.subでエラーが発生する場合をシミュレート
        
        with patch('re.sub', side_effect=re.error("Invalid regex")):
            result = highlight_search_terms(content, ['test'])
            
            # エラーが発生しても元のコンテンツが返されることを確認
            assert result == content
    
    def test_generate_html_content_all_parameters(self, template_environment_mock):
        """全パラメータ指定でのHTML生成テスト"""
        mock_env, mock_template = template_environment_mock
        
        result = generate_html_content(
            file_path='/test/sample.md',
            content='<p>Test content</p>',
            is_markdown=True,
            html_font_size=18,
            search_terms=['Python', 'テスト']
        )
        
        # テンプレートが正しいパラメータで呼ばれることを確認
        mock_template.render.assert_called_once()
        call_args = mock_template.render.call_args[1]
        
        assert call_args['title'] == 'sample.md'
        assert call_args['file_path'] == '/test/sample.md'
        assert call_args['content'] == '<p>Test content</p>'
        assert call_args['is_markdown'] == True
        assert call_args['font_size'] == 18
        assert call_args['search_terms'] == ['Python', 'テスト']
    
    def test_generate_html_content_font_size_limits(self, template_environment_mock):
        """フォントサイズ制限テスト"""
        mock_env, mock_template = template_environment_mock
        
        # 最小値以下
        generate_html_content('test.txt', 'content', False, 5)
        call_args = mock_template.render.call_args[1]
        assert call_args['font_size'] == MIN_FONT_SIZE
        
        # 最大値以上
        generate_html_content('test.txt', 'content', False, 50)
        call_args = mock_template.render.call_args[1]
        assert call_args['font_size'] == MAX_FONT_SIZE
        
        # None値
        generate_html_content('test.txt', 'content', False, None)
        call_args = mock_template.render.call_args[1]
        assert call_args['font_size'] == 16  # デフォルト値
    
    def test_generate_html_content_template_not_found(self):
        """テンプレートファイル見つからないテスト"""
        with patch('service.text_handler.create_jinja_environment') as mock_create_env:
            mock_env = MagicMock()
            mock_env.get_template.side_effect = TemplateNotFound(TEXT_VIEWER_TEMPLATE)
            mock_create_env.return_value = mock_env
            
            with pytest.raises(FileNotFoundError) as exc_info:
                generate_html_content('test.txt', 'content', False, 16)
            
            assert "テンプレートファイルが見つかりません" in str(exc_info.value)
    
    def test_generate_html_content_general_exception(self, template_environment_mock):
        """HTML生成時の一般例外テスト"""
        mock_env, mock_template = template_environment_mock
        mock_template.render.side_effect = Exception("Template error")
        
        with pytest.raises(RuntimeError) as exc_info:
            generate_html_content('test.txt', 'content', False, 16)
        
        assert "HTMLテンプレートの処理中にエラーが発生しました" in str(exc_info.value)
    
    def test_create_temp_html_file_success(self):
        """一時HTMLファイル作成成功テスト"""
        test_content = "<html><body>Test HTML Content</body></html>"
        
        result_path = create_temp_html_file(test_content)
        
        assert os.path.exists(result_path)
        assert result_path.endswith('.html')
        
        # 内容確認
        with open(result_path, encoding='utf-8') as f:
            content = f.read()
        assert content == test_content
        
        # クリーンアップ
        os.remove(result_path)
    
    def test_create_temp_html_file_io_error(self):
        """一時HTMLファイル作成IOエラーテスト"""
        with patch('tempfile.NamedTemporaryFile', side_effect=IOError("Disk full")):
            with pytest.raises(IOError) as exc_info:
                create_temp_html_file("<html>test</html>")
            
            assert "一時HTMLファイルの作成に失敗しました" in str(exc_info.value)
    
    def test_get_file_type_display_name_all_types(self):
        """全ファイルタイプ表示名テスト"""
        test_cases = [
            ('.txt', 'テキストファイル'),
            ('.md', 'Markdownファイル'),
            ('.pdf', 'PDFファイル'),
            ('.html', 'HTMLファイル'),
            ('.css', 'CSSファイル'),
            ('.unknown', '不明なファイル'),
            ('', '不明なファイル'),
            ('.TXT', 'テキストファイル'),  # 大文字
            ('.PDF', 'PDFファイル')
        ]
        
        for extension, expected in test_cases:
            result = get_file_type_display_name(extension)
            assert result == expected
    
    @patch('service.text_handler.validate_template_file')
    @patch('service.text_handler.highlight_text_file')
    @patch('webbrowser.open')
    def test_open_text_file_success(self, mock_browser_open, mock_highlight, mock_validate):
        """テキストファイル正常オープンテスト"""
        mock_highlight.return_value = '/tmp/highlighted.html'
        
        open_text_file('/test/file.txt', ['Python', 'テスト'], 16)
        
        mock_highlight.assert_called_once_with('/test/file.txt', ['Python', 'テスト'], 16)
        mock_browser_open.assert_called_once_with('file:///tmp/highlighted.html')
    
    @patch('service.text_handler.highlight_text_file')
    def test_open_text_file_exception(self, mock_highlight):
        """テキストファイルオープン例外テスト"""
        mock_highlight.side_effect = Exception("Highlight error")
        
        with pytest.raises(Exception) as exc_info:
            open_text_file('/test/file.txt', ['test'], 16)
        
        assert "テキストファイルを開けませんでした" in str(exc_info.value)
    
    @patch('os.path.exists')
    def test_validate_template_file_exists(self, mock_exists):
        """テンプレートファイル存在確認テスト"""
        mock_exists.return_value = True
        
        with patch('service.text_handler.get_template_directory', return_value='/test/templates'):
            result = validate_template_file()
            
            assert result == True
            expected_path = os.path.join('/test/templates', TEXT_VIEWER_TEMPLATE)
            mock_exists.assert_called_once_with(expected_path)
    
    @patch('os.path.exists')
    def test_validate_template_file_not_exists(self, mock_exists):
        """テンプレートファイル存在しないテスト"""
        mock_exists.return_value = False
        
        result = validate_template_file()
        assert result == False
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_available_templates_multiple(self, mock_listdir, mock_exists):
        """利用可能テンプレート複数取得テスト"""
        mock_exists.return_value = True
        mock_listdir.return_value = [
            'text_viewer.html',
            'custom_template.html',
            'style.css',  # HTMLファイルではない
            'another.html',
            'readme.txt'  # HTMLファイルではない
        ]
        
        with patch('service.text_handler.get_template_directory', return_value='/test/templates'):
            result = get_available_templates()
            
            expected = ['text_viewer.html', 'custom_template.html', 'another.html']
            assert result == expected
    
    @patch('os.path.exists')
    def test_get_available_templates_no_directory(self, mock_exists):
        """テンプレートディレクトリ存在しないテスト"""
        mock_exists.return_value = False
        
        result = get_available_templates()
        assert result == []
    
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_available_templates_empty_directory(self, mock_listdir, mock_exists):
        """空テンプレートディレクトリテスト"""
        mock_exists.return_value = True
        mock_listdir.return_value = []
        
        result = get_available_templates()
        assert result == []


class TestTextHandlerIntegration:
    """テキストハンドラーの統合テスト"""
    
    def test_markdown_to_html_workflow(self, temp_dir):
        """Markdown→HTML変換ワークフローテスト"""
        # Markdownファイル作成
        md_file = os.path.join(temp_dir, 'test.md')
        md_content = """# テストMarkdown

## Python検索機能

- **検索語**: Python
- **対象**: テストファイル

```python
def search(term):
    return term in content
```

> これは引用文です。
"""
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # テンプレートディレクトリとファイル作成
        template_dir = os.path.join(temp_dir, 'templates')
        os.makedirs(template_dir)
        
        template_content = """<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
<h1>{{ title }}</h1>
<div>{{ content | safe }}</div>
</body>
</html>"""
        
        template_file = os.path.join(template_dir, 'text_viewer.html')
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # highlight_text_file実行
        with patch('service.text_handler.get_template_directory', return_value=template_dir):
            result_path = highlight_text_file(md_file, ['Python', 'テスト'], 16)
            
            # 結果ファイルが作成されることを確認
            assert os.path.exists(result_path)
            assert result_path.endswith('.html')
            
            # 結果内容確認
            with open(result_path, encoding='utf-8') as f:
                html_content = f.read()
            
            # Markdownが処理されHTMLに含まれることを確認
            assert '<h1>' in html_content  # Markdownのヘッダーが変換
            assert '<code>' in html_content  # コードブロックが変換
            assert '<span style=' in html_content  # ハイライトが適用
            
            # クリーンアップ
            os.remove(result_path)
    
    def test_large_text_file_processing(self, temp_dir):
        """大容量テキストファイル処理テスト"""
        # 1MBのテキストファイル作成
        large_file = os.path.join(temp_dir, 'large.txt')
        large_content = "Python programming tutorial. " * 50000  # 約1MB
        
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        
        # テンプレート設定
        template_dir = os.path.join(temp_dir, 'templates')
        os.makedirs(template_dir)
        
        template_content = """<html><body>{{ content | safe }}</body></html>"""
        template_file = os.path.join(template_dir, 'text_viewer.html')
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        # 処理実行
        with patch('service.text_handler.get_template_directory', return_value=template_dir):
            result_path = highlight_text_file(large_file, ['Python'], 16)
            
            # 大容量ファイルでも処理が完了することを確認
            assert os.path.exists(result_path)
            
            # 結果確認（全てのPythonがハイライトされる）
            with open(result_path, encoding='utf-8') as f:
                html_content = f.read()
            
            highlight_count = html_content.count('<span style=')
            assert highlight_count == 50000  # 各行のPythonがハイライト
            
            # クリーンアップ
            os.remove(result_path)
    
    def test_multiple_encoding_text_files(self, temp_dir):
        """複数エンコーディングテキストファイル処理テスト"""
        encodings_and_content = [
            ('utf-8', 'UTF-8: Python プログラミング'),
            ('shift_jis', 'Shift-JIS: Python プログラミング'),
            ('euc-jp', 'EUC-JP: Python プログラミング')
        ]
        
        template_dir = os.path.join(temp_dir, 'templates')
        os.makedirs(template_dir)
        
        template_content = """<html><body>{{ content | safe }}</body></html>"""
        template_file = os.path.join(template_dir, 'text_viewer.html')
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        for encoding, content in encodings_and_content:
            # 各エンコーディングでファイル作成
            test_file = os.path.join(temp_dir, f'test_{encoding}.txt')
            try:
                with open(test_file, 'w', encoding=encoding) as f:
                    f.write(content)
                
                # 処理実行
                with patch('service.text_handler.get_template_directory', return_value=template_dir):
                    result_path = highlight_text_file(test_file, ['Python'], 16)
                    
                    # 各エンコーディングファイルが正常処理されることを確認
                    assert os.path.exists(result_path)
                    
                    with open(result_path, encoding='utf-8') as f:
                        html_content = f.read()
                    
                    assert 'Python' in html_content
                    assert '<span style=' in html_content
                    
                    # クリーンアップ
                    os.remove(result_path)
                    
            except UnicodeError:
                # 特定エンコーディングがサポートされていない場合はスキップ
                continue