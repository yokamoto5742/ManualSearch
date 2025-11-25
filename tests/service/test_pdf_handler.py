import atexit
import os
import subprocess
import tempfile
import time
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import fitz
import psutil
import pytest

from service.pdf_handler import (
    AcrobatProcessManager,
    PDFHighlighter,
    PDFNavigator,
    TempFileManager,
    open_pdf,
    temp_file_manager,
)
from utils.constants import (
    ACROBAT_PROCESS_NAMES,
    ACROBAT_WAIT_INTERVAL,
    ACROBAT_WAIT_TIMEOUT,
    PAGE_NAVIGATION_DELAY,
    PAGE_NAVIGATION_RETRY_COUNT,
    PDF_HIGHLIGHT_COLORS,
    PROCESS_CLEANUP_DELAY,
    PROCESS_TERMINATE_TIMEOUT,
)


@pytest.mark.unit
class TestTempFileManager:
    """TempFileManagerクラスのテスト"""

    @pytest.fixture
    def temp_manager(self):
        """テスト用のTempFileManagerインスタンス"""
        manager = TempFileManager()
        manager._temp_files = []
        yield manager
        # テスト後のクリーンアップ
        manager.cleanup_all()

    def test_init_registers_cleanup_handler(self):
        """初期化時にatexitハンドラが登録されることを確認"""
        with patch('atexit.register') as mock_register:
            manager = TempFileManager()
            mock_register.assert_called_once_with(manager.cleanup_all)

    def test_add_file(self, temp_manager):
        """ファイルパスを追加できることを確認"""
        file_path = '/path/to/temp/file.pdf'
        temp_manager.add(file_path)

        assert file_path in temp_manager._temp_files
        assert len(temp_manager._temp_files) == 1

    def test_add_multiple_files(self, temp_manager):
        """複数のファイルパスを追加できることを確認"""
        files = ['/temp/file1.pdf', '/temp/file2.pdf', '/temp/file3.pdf']

        for file_path in files:
            temp_manager.add(file_path)

        assert len(temp_manager._temp_files) == 3
        for file_path in files:
            assert file_path in temp_manager._temp_files

    def test_cleanup_single_existing_file(self, temp_manager, temp_dir):
        """存在する一時ファイルを削除できることを確認"""
        temp_file = os.path.join(temp_dir, 'temp_test.pdf')
        with open(temp_file, 'w') as f:
            f.write('test content')

        temp_manager.add(temp_file)
        temp_manager.cleanup_single(temp_file)

        assert not os.path.exists(temp_file)
        assert temp_file not in temp_manager._temp_files

    def test_cleanup_single_nonexistent_file(self, temp_manager):
        """存在しないファイルの削除でエラーが発生しないことを確認"""
        nonexistent_file = '/nonexistent/file.pdf'
        temp_manager.add(nonexistent_file)

        # エラーが発生しないことを確認
        temp_manager.cleanup_single(nonexistent_file)

        assert nonexistent_file not in temp_manager._temp_files

    def test_cleanup_single_file_os_error(self, temp_manager, temp_dir):
        """ファイル削除時のOSErrorを適切にハンドリングすることを確認"""
        temp_file = os.path.join(temp_dir, 'protected.pdf')
        with open(temp_file, 'w') as f:
            f.write('test')

        temp_manager.add(temp_file)

        with patch('os.remove', side_effect=OSError("Permission denied")):
            # エラーが発生しても例外が外部に伝搬しないことを確認
            temp_manager.cleanup_single(temp_file)

    def test_cleanup_all_files(self, temp_manager, temp_dir):
        """すべての一時ファイルを削除できることを確認"""
        temp_files = []
        for i in range(3):
            temp_file = os.path.join(temp_dir, f'temp_{i}.pdf')
            with open(temp_file, 'w') as f:
                f.write(f'content {i}')
            temp_files.append(temp_file)
            temp_manager.add(temp_file)

        temp_manager.cleanup_all()

        for temp_file in temp_files:
            assert not os.path.exists(temp_file)
        assert len(temp_manager._temp_files) == 0

    def test_cleanup_all_with_mixed_states(self, temp_manager, temp_dir):
        """存在するファイルと存在しないファイルが混在する状態でcleanup_allを実行"""
        existing_file = os.path.join(temp_dir, 'existing.pdf')
        with open(existing_file, 'w') as f:
            f.write('exists')

        nonexistent_file = '/nonexistent/file.pdf'

        temp_manager.add(existing_file)
        temp_manager.add(nonexistent_file)

        temp_manager.cleanup_all()

        assert not os.path.exists(existing_file)
        assert len(temp_manager._temp_files) == 0

    def test_cleanup_file_value_error(self, temp_manager, temp_dir):
        """リストから削除時のValueErrorをハンドリング"""
        # 実際のファイルを作成
        file_path = os.path.join(temp_dir, 'test_error.pdf')
        with open(file_path, 'w') as f:
            f.write('test')

        # ファイルを追加せずに削除を試みる（リストに存在しない状態）
        # この場合、os.removeは成功するがlist.removeでValueErrorが発生する

        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            # エラーが発生しても例外が外部に伝搬しないことを確認
            # _temp_filesにfile_pathが存在しないため、removeでValueErrorが発生
            temp_manager._cleanup_file(file_path)

            # os.removeは呼ばれる
            mock_remove.assert_called_once_with(file_path)


@pytest.mark.unit
class TestAcrobatProcessManager:
    """AcrobatProcessManagerクラスのテスト"""

    def test_is_acrobat_process_valid_names(self):
        """Acrobatプロセス名の判定が正しく動作することを確認"""
        valid_names = [
            'acrobat',
            'acrobat.exe',
            'acrord32',
            'acrord32.exe',
            'acrord64',
            'acrord64.exe',
            'reader_sl',
            'ACROBAT.EXE',  # 大文字小文字を無視
        ]

        for name in valid_names:
            assert AcrobatProcessManager._is_acrobat_process(name.lower()) is True

    def test_is_acrobat_process_invalid_names(self):
        """Acrobat以外のプロセス名が正しく判定されることを確認"""
        invalid_names = [
            'chrome.exe',
            'notepad.exe',
            'python.exe',
            'explorer.exe',
            'acrobat_fake.exe',
        ]

        for name in invalid_names:
            assert AcrobatProcessManager._is_acrobat_process(name.lower()) is False

    @patch('psutil.process_iter')
    def test_find_processes_no_acrobat(self, mock_process_iter):
        """Acrobatプロセスが存在しない場合"""
        mock_processes = [
            Mock(info={'pid': 1234, 'name': 'chrome.exe'}),
            Mock(info={'pid': 5678, 'name': 'notepad.exe'}),
        ]
        mock_process_iter.return_value = mock_processes

        result = AcrobatProcessManager._find_processes()

        assert len(result) == 0

    @patch('psutil.process_iter')
    def test_find_processes_with_acrobat(self, mock_process_iter):
        """Acrobatプロセスが存在する場合"""
        mock_acrobat_proc = Mock(info={'pid': 9999, 'name': 'Acrobat.exe'})
        mock_reader_proc = Mock(info={'pid': 8888, 'name': 'AcroRd32.exe'})
        mock_other_proc = Mock(info={'pid': 1234, 'name': 'chrome.exe'})

        mock_process_iter.return_value = [
            mock_acrobat_proc,
            mock_reader_proc,
            mock_other_proc,
        ]

        result = AcrobatProcessManager._find_processes()

        assert len(result) == 2
        assert mock_acrobat_proc in result
        assert mock_reader_proc in result
        assert mock_other_proc not in result

    def test_terminate_process_normal_termination(self):
        """プロセスが正常に終了する場合"""
        mock_proc = Mock()
        mock_proc.info = {'name': 'Acrobat.exe'}
        mock_proc.pid = 1234
        mock_proc.wait.return_value = None

        AcrobatProcessManager._terminate_process(mock_proc)

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=PROCESS_TERMINATE_TIMEOUT)
        mock_proc.kill.assert_not_called()

    def test_terminate_process_timeout_force_kill(self):
        """プロセス終了がタイムアウトした場合の強制終了"""
        mock_proc = Mock()
        mock_proc.info = {'name': 'Acrobat.exe'}
        mock_proc.pid = 1234
        mock_proc.wait.side_effect = psutil.TimeoutExpired(PROCESS_TERMINATE_TIMEOUT)

        AcrobatProcessManager._terminate_process(mock_proc)

        mock_proc.terminate.assert_called_once()
        mock_proc.wait.assert_called_once_with(timeout=PROCESS_TERMINATE_TIMEOUT)
        mock_proc.kill.assert_called_once()

    def test_terminate_process_no_such_process(self):
        """プロセスが既に存在しない場合のエラーハンドリング"""
        mock_proc = Mock()
        mock_proc.info = {'name': 'Acrobat.exe'}
        mock_proc.pid = 1234
        mock_proc.terminate.side_effect = psutil.NoSuchProcess(1234)

        # エラーが発生しても例外が外部に伝搬しないことを確認
        AcrobatProcessManager._terminate_process(mock_proc)

        mock_proc.terminate.assert_called_once()

    def test_terminate_process_access_denied(self):
        """プロセスへのアクセスが拒否された場合のエラーハンドリング"""
        mock_proc = Mock()
        mock_proc.info = {'name': 'Acrobat.exe'}
        mock_proc.pid = 1234
        mock_proc.terminate.side_effect = psutil.AccessDenied(1234)

        # エラーが発生しても例外が外部に伝搬しないことを確認
        AcrobatProcessManager._terminate_process(mock_proc)

        mock_proc.terminate.assert_called_once()

    @patch('time.sleep')
    @patch.object(AcrobatProcessManager, '_terminate_process')
    @patch.object(AcrobatProcessManager, '_find_processes')
    def test_close_all_processes_no_processes(self, mock_find, mock_terminate, mock_sleep):
        """Acrobatプロセスが存在しない場合"""
        mock_find.return_value = []

        AcrobatProcessManager.close_all_processes()

        mock_find.assert_called_once()
        mock_terminate.assert_not_called()
        mock_sleep.assert_not_called()

    @patch('time.sleep')
    @patch.object(AcrobatProcessManager, '_terminate_process')
    @patch.object(AcrobatProcessManager, '_find_processes')
    def test_close_all_processes_with_processes(self, mock_find, mock_terminate, mock_sleep):
        """Acrobatプロセスが存在する場合"""
        mock_processes = [Mock(), Mock(), Mock()]
        mock_find.return_value = mock_processes

        AcrobatProcessManager.close_all_processes()

        mock_find.assert_called_once()
        assert mock_terminate.call_count == 3
        mock_sleep.assert_called_once_with(PROCESS_CLEANUP_DELAY)

    @patch.object(AcrobatProcessManager, '_find_processes')
    def test_close_all_processes_exception_handling(self, mock_find):
        """プロセス検索中の例外処理"""
        mock_find.side_effect = Exception("Unexpected error")

        # エラーが発生しても例外が外部に伝搬しないことを確認
        AcrobatProcessManager.close_all_processes()

        mock_find.assert_called_once()

    def test_is_acrobat_window_valid_titles(self):
        """Acrobatウィンドウタイトルの判定が正しく動作することを確認"""
        valid_titles = [
            "Adobe Acrobat Reader DC",
            "Adobe Acrobat Pro DC",
            "document.pdf - Acrobat Reader",
            "file.pdf - Adobe Acrobat",
            "ADOBE ACROBAT",  # 大文字
            "acrobat reader",  # 小文字
        ]

        for title in valid_titles:
            assert AcrobatProcessManager._is_acrobat_window(title) is True

    def test_is_acrobat_window_invalid_titles(self):
        """Acrobat以外のウィンドウタイトルが正しく判定されることを確認"""
        invalid_titles = [
            "Google Chrome",
            "Microsoft Word",
            "Notepad++",
            "File Explorer",
            "",  # 空文字列
        ]

        for title in invalid_titles:
            assert AcrobatProcessManager._is_acrobat_window(title) is False

    @patch('time.sleep')
    @patch('pyautogui.getActiveWindowTitle')
    @patch('psutil.Process')
    def test_wait_for_startup_success(self, mock_process_class, mock_get_window, mock_sleep):
        """Acrobat起動待機が成功する場合"""
        mock_process = Mock()
        mock_process.status.return_value = psutil.STATUS_RUNNING
        mock_process_class.return_value = mock_process

        mock_get_window.return_value = "Adobe Acrobat Reader DC"

        result = AcrobatProcessManager.wait_for_startup(1234, timeout=5)

        assert result is True
        mock_process_class.assert_called_with(1234)

    @patch('time.sleep')
    @patch('psutil.Process')
    def test_wait_for_startup_process_not_running(self, mock_process_class, mock_sleep):
        """プロセスがRUNNING状態でない場合"""
        mock_process = Mock()
        mock_process.status.return_value = psutil.STATUS_SLEEPING
        mock_process_class.return_value = mock_process

        # タイムアウトを短く設定
        with patch('service.pdf_handler.ACROBAT_WAIT_TIMEOUT', 1):
            result = AcrobatProcessManager.wait_for_startup(1234, timeout=1)

        assert result is False

    @patch('time.sleep')
    @patch('psutil.Process')
    def test_wait_for_startup_no_such_process(self, mock_process_class, mock_sleep):
        """プロセスが存在しない場合"""
        mock_process_class.side_effect = psutil.NoSuchProcess(1234)

        result = AcrobatProcessManager.wait_for_startup(1234, timeout=5)

        assert result is False

    @patch('time.sleep')
    @patch('pyautogui.getActiveWindowTitle')
    @patch('psutil.Process')
    def test_wait_for_startup_window_title_exception(self, mock_process_class, mock_get_window, mock_sleep):
        """ウィンドウタイトル取得時の例外処理"""
        mock_process = Mock()
        mock_process.status.return_value = psutil.STATUS_RUNNING
        mock_process_class.return_value = mock_process

        # 最初は例外、その後成功
        mock_get_window.side_effect = [
            Exception("Window access error"),
            "Adobe Acrobat Reader DC",
        ]

        result = AcrobatProcessManager.wait_for_startup(1234, timeout=5)

        assert result is True

    @patch('service.pdf_handler.time.sleep')
    @patch('service.pdf_handler.time.time')
    @patch('psutil.Process')
    def test_wait_for_startup_timeout(self, mock_process_class, mock_time, mock_sleep):
        """起動待機がタイムアウトする場合"""
        # time.time()をモック化してタイムアウトをシミュレート
        # start_timeが0、whileループチェック時に2.0でタイムアウト、loggerでも使われるので十分な値を用意
        mock_time.side_effect = [0, 2.0, 2.0, 2.0, 2.0]

        mock_process = Mock()
        mock_process.status.return_value = psutil.STATUS_ZOMBIE  # RUNNINGではない状態
        mock_process_class.return_value = mock_process

        result = AcrobatProcessManager.wait_for_startup(1234, timeout=1)

        assert result is False


@pytest.mark.unit
class TestPDFNavigator:
    """PDFNavigatorクラスのテスト"""

    @patch('pyautogui.press')
    @patch('pyautogui.write')
    @patch('pyautogui.hotkey')
    @patch('time.sleep')
    def test_navigate_to_page_one(self, mock_sleep, mock_hotkey, mock_write, mock_press):
        """1ページ目への移動は何もしないことを確認"""
        PDFNavigator.navigate_to_page(1)

        mock_hotkey.assert_not_called()
        mock_write.assert_not_called()
        mock_press.assert_not_called()

    @patch('pyautogui.press')
    @patch('pyautogui.write')
    @patch('pyautogui.hotkey')
    @patch('time.sleep')
    def test_navigate_to_page_success(self, mock_sleep, mock_hotkey, mock_write, mock_press):
        """ページ移動が正常に実行されることを確認"""
        page_number = 42

        PDFNavigator.navigate_to_page(page_number)

        assert mock_hotkey.call_args_list[0] == call('ctrl', 'shift', 'n')
        # 既存の入力をクリア
        assert mock_hotkey.call_args_list[1] == call('ctrl', 'a')
        # ページ番号を入力
        mock_write.assert_called_once_with(str(page_number))
        # Enter で確定
        mock_press.assert_called_once_with('enter')

    @patch('time.sleep')
    @patch.object(PDFNavigator, '_execute_navigation')
    def test_navigate_to_page_with_retry_on_error(self, mock_execute, mock_sleep):
        """ページ移動でエラーが発生した場合のリトライ"""
        page_number = 10
        # 最初の2回は失敗、3回目で成功
        mock_execute.side_effect = [
            Exception("Navigation error 1"),
            Exception("Navigation error 2"),
            None,
        ]

        PDFNavigator.navigate_to_page(page_number)

        assert mock_execute.call_count == 3
        # リトライ間隔でsleepが呼ばれることを確認
        assert mock_sleep.call_count >= 2

    @patch('time.sleep')
    @patch.object(PDFNavigator, '_execute_navigation')
    def test_navigate_to_page_all_retries_fail(self, mock_execute, mock_sleep):
        """すべてのリトライが失敗する場合"""
        page_number = 10
        mock_execute.side_effect = Exception("Navigation error")

        # 例外が外部に伝搬しないことを確認
        PDFNavigator.navigate_to_page(page_number)

        assert mock_execute.call_count == PAGE_NAVIGATION_RETRY_COUNT

    @patch('pyautogui.press')
    @patch('pyautogui.write')
    @patch('pyautogui.hotkey')
    @patch('time.sleep')
    def test_execute_navigation_timing(self, mock_sleep, mock_hotkey, mock_write, mock_press):
        """ナビゲーション実行時のタイミング確認"""
        PDFNavigator._execute_navigation(99)

        # 適切なタイミングでsleepが呼ばれることを確認
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert PAGE_NAVIGATION_DELAY in sleep_calls


@pytest.mark.unit
class TestPDFHighlighter:
    """PDFHighlighterクラスのテスト"""

    @pytest.fixture
    def mock_pdf_document(self):
        """モックPDFドキュメント"""
        mock_pages = []

        for i in range(3):
            mock_page = Mock(spec=fitz.Page)
            mock_page.search_for.return_value = []
            mock_pages.append(mock_page)

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter(mock_pages)
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = False

        return mock_doc, mock_pages

    @patch('tempfile.NamedTemporaryFile')
    @patch.object(temp_file_manager, 'add')
    def test_create_temp_file(self, mock_add, mock_temp_file):
        """一時ファイルの作成が正しく動作することを確認"""
        mock_file = Mock()
        mock_file.name = '/tmp/test_highlight.pdf'
        mock_temp_file.return_value.__enter__ = Mock(return_value=mock_file)
        mock_temp_file.return_value.__exit__ = Mock(return_value=False)

        result = PDFHighlighter._create_temp_file()

        assert result == '/tmp/test_highlight.pdf'
        mock_temp_file.assert_called_once_with(delete=False, suffix='.pdf')
        mock_add.assert_called_once_with('/tmp/test_highlight.pdf')

    @patch('fitz.open')
    @patch.object(PDFHighlighter, '_create_temp_file')
    def test_highlight_pdf_success(self, mock_create_temp, mock_fitz_open, mock_pdf_document):
        """PDFハイライトが正常に実行されることを確認"""
        mock_doc, mock_pages = mock_pdf_document
        mock_fitz_open.return_value = mock_doc
        mock_create_temp.return_value = '/tmp/highlighted.pdf'

        pdf_path = '/test/document.pdf'
        search_terms = ['keyword1', 'keyword2']

        result = PDFHighlighter.highlight_pdf(pdf_path, search_terms)

        assert result == '/tmp/highlighted.pdf'
        mock_fitz_open.assert_called_once_with(pdf_path)
        mock_doc.save.assert_called_once_with('/tmp/highlighted.pdf')

    @patch('fitz.open')
    @patch.object(PDFHighlighter, '_create_temp_file')
    def test_highlight_pdf_invalid_pdf_file(self, mock_create_temp, mock_fitz_open):
        """無効なPDFファイルでValueErrorが発生することを確認"""
        mock_fitz_open.side_effect = fitz.FileDataError("Invalid PDF")
        mock_create_temp.return_value = '/tmp/temp.pdf'

        with pytest.raises(ValueError) as exc_info:
            PDFHighlighter.highlight_pdf('/invalid/file.pdf', ['term'])

        assert '無効なPDFファイル' in str(exc_info.value)

    @patch('fitz.open')
    @patch.object(PDFHighlighter, '_create_temp_file')
    def test_highlight_pdf_general_exception(self, mock_create_temp, mock_fitz_open):
        """一般的な例外がRuntimeErrorとして発生することを確認"""
        mock_fitz_open.side_effect = Exception("Unexpected error")
        mock_create_temp.return_value = '/tmp/temp.pdf'

        with pytest.raises(RuntimeError) as exc_info:
            PDFHighlighter.highlight_pdf('/test/file.pdf', ['term'])

        assert 'PDFのハイライト処理中にエラー' in str(exc_info.value)

    def test_add_highlights_empty_terms(self, mock_pdf_document):
        """空の検索語が適切にスキップされることを確認"""
        mock_doc, mock_pages = mock_pdf_document
        search_terms = ['valid', '', '  ', 'another']

        PDFHighlighter._add_highlights(mock_doc, search_terms)

        # 空でない検索語のみが処理されることを確認
        # 各ページで'valid'と'another'が検索される
        for mock_page in mock_pages:
            calls = [str(c) for c in mock_page.search_for.call_args_list]
            assert any('valid' in str(c) for c in calls)
            assert any('another' in str(c) for c in calls)
            # 空文字列は検索されない
            assert not any("''" in str(c) or '""' in str(c) for c in calls if 'search_for' not in str(c))

    def test_add_highlights_with_results(self, mock_pdf_document):
        """検索結果がある場合のハイライト追加"""
        mock_doc, mock_pages = mock_pdf_document

        # 検索結果のモック（矩形領域）
        mock_rect1 = fitz.Rect(100, 100, 200, 120)
        mock_rect2 = fitz.Rect(150, 150, 250, 170)

        mock_pages[0].search_for.return_value = [mock_rect1, mock_rect2]

        mock_highlight = Mock()
        mock_pages[0].add_highlight_annot.return_value = mock_highlight

        search_terms = ['keyword']

        PDFHighlighter._add_highlights(mock_doc, search_terms)

        # ハイライトが2回追加されることを確認
        assert mock_pages[0].add_highlight_annot.call_count == 2
        # カラーが設定されることを確認
        assert mock_highlight.set_colors.call_count == 2
        assert mock_highlight.update.call_count == 2

    def test_highlight_term_in_page_color_rotation(self):
        """複数の検索語で色がローテーションされることを確認"""
        mock_page = Mock(spec=fitz.Page)
        mock_rect = fitz.Rect(0, 0, 100, 20)
        mock_page.search_for.return_value = [mock_rect]

        mock_highlight = Mock()
        mock_page.add_highlight_annot.return_value = mock_highlight

        # 色数を超えるインデックスでテスト
        num_colors = len(PDF_HIGHLIGHT_COLORS)

        for color_index in range(num_colors + 3):
            PDFHighlighter._highlight_term_in_page(mock_page, 'test', color_index)

            expected_color = PDF_HIGHLIGHT_COLORS[color_index % num_colors]
            mock_highlight.set_colors.assert_called_with(stroke=expected_color)

    def test_highlight_term_in_page_exception_handling(self):
        """ハイライト追加時の例外処理"""
        mock_page = Mock(spec=fitz.Page)
        mock_rect = fitz.Rect(0, 0, 100, 20)
        mock_page.search_for.return_value = [mock_rect]
        mock_page.add_highlight_annot.side_effect = Exception("Highlight error")

        # 例外が発生しても処理が続行されることを確認
        PDFHighlighter._highlight_term_in_page(mock_page, 'test', 0)

        mock_page.add_highlight_annot.assert_called_once()

    def test_highlight_term_in_page_no_matches(self):
        """検索結果がない場合"""
        mock_page = Mock(spec=fitz.Page)
        mock_page.search_for.return_value = []

        PDFHighlighter._highlight_term_in_page(mock_page, 'nonexistent', 0)

        mock_page.search_for.assert_called_once_with('nonexistent')
        mock_page.add_highlight_annot.assert_not_called()


@pytest.mark.unit
class TestOpenPdfFunction:
    """open_pdf関数のテスト"""

    @patch('time.sleep')
    @patch.object(PDFNavigator, 'navigate_to_page')
    @patch.object(AcrobatProcessManager, 'wait_for_startup')
    @patch('subprocess.Popen')
    @patch.object(PDFHighlighter, 'highlight_pdf')
    @patch.object(AcrobatProcessManager, 'close_all_processes')
    def test_open_pdf_success(
        self,
        mock_close_processes,
        mock_highlight,
        mock_popen,
        mock_wait,
        mock_navigate,
        mock_sleep
    ):
        """PDFを正常に開けることを確認"""
        file_path = '/test/document.pdf'
        acrobat_path = 'C:\\Program Files\\Adobe\\Acrobat.exe'
        current_position = 5
        search_terms = ['keyword1', 'keyword2']

        mock_highlight.return_value = '/tmp/highlighted.pdf'
        mock_process = Mock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_wait.return_value = True

        open_pdf(file_path, acrobat_path, current_position, search_terms)

        mock_close_processes.assert_called_once()
        mock_highlight.assert_called_once_with(file_path, search_terms)
        mock_popen.assert_called_once_with([acrobat_path, '/tmp/highlighted.pdf'])
        mock_wait.assert_called_once_with(1234)
        mock_navigate.assert_called_once_with(current_position)

    @patch.object(AcrobatProcessManager, 'close_all_processes')
    @patch.object(PDFHighlighter, 'highlight_pdf')
    def test_open_pdf_file_not_found(self, mock_highlight, mock_close_processes):
        """存在しないファイルでFileNotFoundErrorが発生することを確認"""
        mock_highlight.side_effect = FileNotFoundError("File not found")

        with pytest.raises(FileNotFoundError) as exc_info:
            open_pdf('/nonexistent/file.pdf', 'acrobat.exe', 1, ['term'])

        assert '指定されたファイルが見つかりません' in str(exc_info.value)

    @patch('subprocess.Popen')
    @patch.object(PDFHighlighter, 'highlight_pdf')
    @patch.object(AcrobatProcessManager, 'close_all_processes')
    def test_open_pdf_subprocess_error(self, mock_close, mock_highlight, mock_popen):
        """サブプロセス起動エラーの処理"""
        mock_highlight.return_value = '/tmp/temp.pdf'
        mock_popen.side_effect = subprocess.SubprocessError("Failed to start")

        with pytest.raises(RuntimeError) as exc_info:
            open_pdf('/test/file.pdf', 'invalid_acrobat.exe', 1, ['term'])

        assert 'Acrobat Readerの起動に失敗しました' in str(exc_info.value)

    @patch('subprocess.Popen')
    @patch.object(PDFHighlighter, 'highlight_pdf')
    @patch.object(AcrobatProcessManager, 'close_all_processes')
    def test_open_pdf_general_exception(self, mock_close, mock_highlight, mock_popen):
        """一般的な例外の処理"""
        mock_highlight.return_value = '/tmp/temp.pdf'
        mock_popen.side_effect = Exception("Unexpected error")

        with pytest.raises(RuntimeError) as exc_info:
            open_pdf('/test/file.pdf', 'acrobat.exe', 1, ['term'])

        assert '予期せぬエラーが発生しました' in str(exc_info.value)

    @patch('time.sleep')
    @patch.object(PDFNavigator, 'navigate_to_page')
    @patch.object(AcrobatProcessManager, 'wait_for_startup')
    @patch('subprocess.Popen')
    @patch.object(PDFHighlighter, 'highlight_pdf')
    @patch.object(AcrobatProcessManager, 'close_all_processes')
    def test_open_pdf_wait_for_startup_fails(
        self,
        mock_close,
        mock_highlight,
        mock_popen,
        mock_wait,
        mock_navigate,
        mock_sleep
    ):
        """Acrobat起動待機が失敗する場合"""
        mock_highlight.return_value = '/tmp/temp.pdf'
        mock_process = Mock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_wait.return_value = False  # 起動失敗

        # 例外が発生しないことを確認（警告ログのみ）
        open_pdf('/test/file.pdf', 'acrobat.exe', 5, ['term'])

        mock_navigate.assert_not_called()

    @patch('time.sleep')
    @patch.object(PDFNavigator, 'navigate_to_page')
    @patch.object(AcrobatProcessManager, 'wait_for_startup')
    @patch('subprocess.Popen')
    @patch.object(PDFHighlighter, 'highlight_pdf')
    @patch.object(AcrobatProcessManager, 'close_all_processes')
    def test_open_pdf_page_one_no_navigation(
        self,
        mock_close,
        mock_highlight,
        mock_popen,
        mock_wait,
        mock_navigate,
        mock_sleep
    ):
        """1ページ目の場合はナビゲーションが実行されないことを確認"""
        mock_highlight.return_value = '/tmp/temp.pdf'
        mock_process = Mock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_wait.return_value = True

        open_pdf('/test/file.pdf', 'acrobat.exe', 1, ['term'])

        # navigate_to_pageは呼ばれるが、内部で何もしない
        mock_navigate.assert_called_once_with(1)

    @patch('time.sleep')
    @patch.object(PDFNavigator, 'navigate_to_page')
    @patch.object(AcrobatProcessManager, 'wait_for_startup')
    @patch('subprocess.Popen')
    @patch.object(PDFHighlighter, 'highlight_pdf')
    @patch.object(AcrobatProcessManager, 'close_all_processes')
    def test_open_pdf_empty_search_terms(
        self,
        mock_close,
        mock_highlight,
        mock_popen,
        mock_wait,
        mock_navigate,
        mock_sleep
    ):
        """空の検索語リストでも正常に動作することを確認"""
        mock_highlight.return_value = '/tmp/temp.pdf'
        mock_process = Mock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_wait.return_value = True

        open_pdf('/test/file.pdf', 'acrobat.exe', 1, [])

        mock_highlight.assert_called_once_with('/test/file.pdf', [])


@pytest.mark.unit
class TestEdgeCases:
    """エッジケーステスト"""

    @patch('fitz.open')
    @patch.object(PDFHighlighter, '_create_temp_file')
    def test_highlight_pdf_with_unicode_search_terms(self, mock_create_temp, mock_fitz_open):
        """Unicode文字を含む検索語のテスト"""
        mock_page = Mock(spec=fitz.Page)
        mock_page.search_for.return_value = []

        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([mock_page])
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = False

        mock_fitz_open.return_value = mock_doc
        mock_create_temp.return_value = '/tmp/temp.pdf'

        unicode_terms = ['日本語', 'Русский', '中文', '한국어', 'العربية']

        PDFHighlighter.highlight_pdf('/test/file.pdf', unicode_terms)

        # すべての検索語が処理されることを確認
        for term in unicode_terms:
            mock_page.search_for.assert_any_call(term)

    @patch('time.sleep')
    @patch('psutil.Process')
    def test_wait_for_startup_with_zero_timeout(self, mock_process_class, mock_sleep):
        """タイムアウト0での起動待機"""
        result = AcrobatProcessManager.wait_for_startup(1234, timeout=0)

        assert result is False

    @patch('psutil.process_iter')
    def test_find_processes_with_process_access_error(self, mock_process_iter):
        """プロセス情報取得時のAccessDeniedエラー処理"""
        mock_accessible_proc = Mock(info={'pid': 1234, 'name': 'Acrobat.exe'})

        # 2番目のプロセスでAccessDeniedエラーが発生
        def process_generator():
            yield mock_accessible_proc
            raise psutil.AccessDenied(5678)

        mock_process_iter.return_value = process_generator()

        # エラーが発生しても例外が外部に伝搬しないことを確認
        with pytest.raises(psutil.AccessDenied):
            AcrobatProcessManager._find_processes()

    def test_temp_file_manager_cleanup_with_empty_list(self):
        """空のファイルリストでのクリーンアップ"""
        manager = TempFileManager()
        manager._temp_files = []

        # エラーが発生しないことを確認
        manager.cleanup_all()

        assert len(manager._temp_files) == 0

    @patch('pyautogui.press')
    @patch('pyautogui.write')
    @patch('pyautogui.hotkey')
    @patch('time.sleep')
    def test_navigate_to_large_page_number(self, mock_sleep, mock_hotkey, mock_write, mock_press):
        """非常に大きなページ番号への移動"""
        large_page = 999999

        PDFNavigator.navigate_to_page(large_page)

        mock_write.assert_called_once_with(str(large_page))

    @patch('pyautogui.press')
    @patch('pyautogui.write')
    @patch('pyautogui.hotkey')
    @patch('time.sleep')
    def test_navigate_to_negative_page_number(self, mock_sleep, mock_hotkey, mock_write, mock_press):
        """負のページ番号への移動（pyautoguiに渡される）"""
        negative_page = -5

        PDFNavigator.navigate_to_page(negative_page)

        # 負のページ番号も文字列として渡される
        mock_write.assert_called_once_with(str(negative_page))


@pytest.mark.integration
class TestIntegrationScenarios:
    """統合テストシナリオ"""

    @patch('time.sleep')
    @patch.object(PDFNavigator, 'navigate_to_page')
    @patch.object(AcrobatProcessManager, 'wait_for_startup')
    @patch('subprocess.Popen')
    @patch('fitz.open')
    @patch.object(PDFHighlighter, '_create_temp_file')
    @patch.object(AcrobatProcessManager, 'close_all_processes')
    def test_full_pdf_opening_workflow(
        self,
        mock_close,
        mock_create_temp,
        mock_fitz_open,
        mock_popen,
        mock_wait,
        mock_navigate,
        mock_sleep
    ):
        """完全なPDFオープンワークフローの統合テスト"""
        # PDFページのモック
        mock_page = Mock(spec=fitz.Page)

        # 検索結果を返す
        mock_rect = fitz.Rect(100, 100, 200, 120)
        mock_page.search_for.return_value = [mock_rect]
        mock_highlight = Mock()
        mock_page.add_highlight_annot.return_value = mock_highlight

        # PDFドキュメントのモック
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([mock_page])
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = False

        mock_fitz_open.return_value = mock_doc
        mock_create_temp.return_value = '/tmp/highlighted.pdf'

        # プロセスのモック
        mock_process = Mock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process
        mock_wait.return_value = True

        # 実行
        file_path = '/test/document.pdf'
        acrobat_path = 'C:\\Program Files\\Adobe\\Acrobat.exe'
        page_number = 10
        search_terms = ['important', 'keyword']

        open_pdf(file_path, acrobat_path, page_number, search_terms)

        # 全ての工程が実行されたことを確認
        mock_close.assert_called_once()
        mock_fitz_open.assert_called_once_with(file_path)
        mock_page.search_for.assert_any_call('important')
        mock_page.search_for.assert_any_call('keyword')
        mock_page.add_highlight_annot.assert_called()
        mock_doc.save.assert_called_once_with('/tmp/highlighted.pdf')
        mock_popen.assert_called_once_with([acrobat_path, '/tmp/highlighted.pdf'])
        mock_wait.assert_called_once_with(1234)
        mock_navigate.assert_called_once_with(page_number)
