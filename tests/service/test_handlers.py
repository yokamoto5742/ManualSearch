import os
import subprocess
import tempfile
from unittest.mock import patch, MagicMock

import fitz
import psutil
import pytest

from utils.constants import (
    PAGE_NAVIGATION_RETRY_COUNT, PROCESS_CLEANUP_DELAY
)
from service.pdf_handler import (
    PDFHighlighter, temp_file_manager, AcrobatProcessManager,
    PDFNavigator, open_pdf
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
        result_path = PDFHighlighter.highlight_pdf('/test/input.pdf', search_terms)

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

        result_path = PDFHighlighter.highlight_pdf('/test/input.pdf', ['', '   ', None])

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
        result_path = PDFHighlighter.highlight_pdf('/test/input.pdf', ['Python'])

        assert result_path.endswith('.pdf')
        
        # クリーンアップ
        if os.path.exists(result_path):
            os.remove(result_path)
    
    @patch('fitz.open')
    def test_highlight_pdf_corrupted_file(self, mock_fitz_open):
        """破損PDFファイルでのテスト"""
        mock_fitz_open.side_effect = fitz.FileDataError("Invalid PDF")

        with pytest.raises(ValueError) as exc_info:
            PDFHighlighter.highlight_pdf('/test/corrupted.pdf', ['Python'])

        assert "無効なPDFファイル" in str(exc_info.value)
    
    @patch('service.pdf_handler.fitz.open')
    def test_highlight_pdf_save_failure(self, mock_fitz_open, mock_pdf_document):
        """PDF保存失敗時のテスト"""
        # コンテキストマネージャとして機能するよう設定
        mock_fitz_open.return_value.__enter__ = MagicMock(return_value=mock_pdf_document['doc'])
        mock_fitz_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_pdf_document['doc'].save.side_effect = Exception("Save error")

        with pytest.raises(RuntimeError) as exc_info:
            PDFHighlighter.highlight_pdf('/test/input.pdf', ['Python'])

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
        temp_file_manager.cleanup_all()

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
        temp_file_manager.cleanup_all()

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

        AcrobatProcessManager.close_all_processes()

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

        AcrobatProcessManager.close_all_processes()

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
        AcrobatProcessManager.close_all_processes()

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

        result = AcrobatProcessManager.wait_for_startup(1234, timeout=5)

        assert result == True
        mock_process.assert_called_with(1234)
    
    @patch('psutil.Process')
    @patch('time.sleep')
    def test_wait_for_acrobat_process_not_found(self, mock_sleep, mock_process):
        """Acrobatプロセス見つからないテスト"""
        mock_process.side_effect = psutil.NoSuchProcess(1234, "process")

        result = AcrobatProcessManager.wait_for_startup(1234, timeout=1)

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

        result = AcrobatProcessManager.wait_for_startup(1234, timeout=1)

        assert result == False
    
    @patch('pyautogui.hotkey')
    @patch('pyautogui.write')
    @patch('pyautogui.press')
    @patch('time.sleep')
    def test_navigate_to_page_multiple_retries(self, mock_sleep, mock_press, mock_write, mock_hotkey):
        """ページナビゲーション複数回リトライテスト"""
        # 初回と2回目で例外、3回目で成功
        mock_hotkey.side_effect = [Exception("Error 1"), Exception("Error 2"), None, None]

        PDFNavigator.navigate_to_page(10)

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
        PDFNavigator.navigate_to_page(5)

        assert mock_hotkey.call_count == PAGE_NAVIGATION_RETRY_COUNT
    
    def test_navigate_to_page_one(self):
        """ページ1への移動（何もしない）テスト"""
        with patch('pyautogui.hotkey') as mock_hotkey:
            PDFNavigator.navigate_to_page(1)

            # ページ1の場合は何も実行されないことを確認
            mock_hotkey.assert_not_called()

