import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from service.file_opener import FileOpener
from utils.constants import (
    FILE_HANDLER_MAPPING, ERROR_MESSAGES, PROCESS_CLEANUP_DELAY
)


class TestFileOpener:
    """FileOpenerクラスのP0レベル包括テスト"""
    
    @pytest.fixture
    def config_manager_mock(self):
        """ConfigManagerのモック"""
        mock_config = MagicMock()
        mock_config.find_available_acrobat_path.return_value = r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe'
        mock_config.get_html_font_size.return_value = 16
        return mock_config
    
    @pytest.fixture
    def file_opener(self, config_manager_mock):
        """FileOpenerインスタンス"""
        return FileOpener(config_manager_mock)
    
    @pytest.fixture
    def sample_files(self, temp_dir):
        """テスト用ファイル群"""
        files = {}
        
        # PDFファイル（模擬）
        pdf_path = os.path.join(temp_dir, 'sample.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%test pdf content')
        files['pdf'] = pdf_path
        
        # テキストファイル
        txt_path = os.path.join(temp_dir, 'sample.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Sample text content for testing')
        files['txt'] = txt_path
        
        # Markdownファイル
        md_path = os.path.join(temp_dir, 'sample.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write('# Sample Markdown\n\nTest content')
        files['md'] = md_path
        
        return files

    def test_init_basic_properties(self, file_opener, config_manager_mock):
        """初期化時の基本プロパティテスト"""
        assert file_opener.config_manager == config_manager_mock
        assert file_opener.acrobat_path == r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe'
        assert file_opener._last_opened_file == ""
        assert file_opener.SUPPORTED_EXTENSIONS == FILE_HANDLER_MAPPING

    def test_supported_extensions_mapping(self, file_opener):
        """サポート拡張子マッピングのテスト"""
        expected_mapping = {
            '.pdf': '_open_pdf_file',
            '.txt': '_open_text_file',
            '.md': '_open_text_file'
        }
        assert file_opener.SUPPORTED_EXTENSIONS == expected_mapping

    # =============================================================================
    # open_file() メソッドのテスト
    # =============================================================================
    
    def test_open_file_nonexistent_file(self, file_opener):
        """存在しないファイルのテスト"""
        with patch.object(file_opener, '_show_error') as mock_show_error:
            file_opener.open_file('/nonexistent/file.txt', 1, ['test'])
            
            mock_show_error.assert_called_once_with(ERROR_MESSAGES['FILE_NOT_FOUND'])

    def test_open_file_unsupported_extension(self, file_opener, temp_dir):
        """サポートされていない拡張子のテスト"""
        unsupported_file = os.path.join(temp_dir, 'test.xyz')
        with open(unsupported_file, 'w') as f:
            f.write('test content')
        
        with patch.object(file_opener, '_show_error') as mock_show_error:
            file_opener.open_file(unsupported_file, 1, ['test'])
            
            mock_show_error.assert_called_once_with(ERROR_MESSAGES['UNSUPPORTED_FORMAT'])

    @patch('service.file_opener.temp_file_manager.cleanup_all')
    @patch('time.sleep')
    def test_open_file_same_pdf_twice(self, mock_sleep, mock_cleanup, file_opener, sample_files):
        """同じPDFファイルを2回開く場合のテスト"""
        pdf_path = sample_files['pdf']
        
        # 最初の呼び出し
        with patch.object(file_opener, '_open_pdf_file') as mock_open_pdf:
            file_opener.open_file(pdf_path, 1, ['test'])
            file_opener.open_file(pdf_path, 2, ['test'])  # 同じファイルを再度開く
            
            assert mock_open_pdf.call_count == 2
            mock_cleanup.assert_called()
            mock_sleep.assert_called_with(PROCESS_CLEANUP_DELAY)

    def test_open_file_pdf_success(self, file_opener, sample_files):
        """PDFファイル正常オープンのテスト"""
        pdf_path = sample_files['pdf']

        with patch.object(file_opener, '_open_pdf_file') as mock_open_pdf:
            file_opener.open_file(pdf_path, 1, ['test'])

            mock_open_pdf.assert_called_once_with(pdf_path, 1, ['test'], True)
            assert file_opener._last_opened_file == pdf_path

    def test_open_file_text_success(self, file_opener, sample_files):
        """テキストファイル正常オープンのテスト"""
        txt_path = sample_files['txt']
        
        with patch.object(file_opener, '_open_text_file') as mock_open_text:
            file_opener.open_file(txt_path, 1, ['test'])
            
            mock_open_text.assert_called_once_with(txt_path, ['test'])
            assert file_opener._last_opened_file == txt_path

    def test_open_file_markdown_success(self, file_opener, sample_files):
        """Markdownファイル正常オープンのテスト"""
        md_path = sample_files['md']
        
        with patch.object(file_opener, '_open_text_file') as mock_open_text:
            file_opener.open_file(md_path, 1, ['test'])
            
            mock_open_text.assert_called_once_with(md_path, ['test'])
            assert file_opener._last_opened_file == md_path

    @patch('service.file_opener.temp_file_manager.cleanup_all')
    def test_open_file_exception_handling(self, mock_cleanup, file_opener, sample_files):
        """ファイルオープン中の例外処理テスト"""
        pdf_path = sample_files['pdf']
        
        with patch.object(file_opener, '_open_pdf_file', side_effect=Exception("Test error")), \
             patch.object(file_opener, '_show_error') as mock_show_error:
            
            file_opener.open_file(pdf_path, 1, ['test'])
            
            mock_show_error.assert_called_once()
            mock_cleanup.assert_called_once()

    # =============================================================================
    # _open_pdf_file() メソッドのテスト
    # =============================================================================
    
    def test_open_pdf_file_accessibility_check_fail(self, file_opener, sample_files):
        """PDFアクセシビリティチェック失敗のテスト"""
        pdf_path = sample_files['pdf']
        
        with patch.object(file_opener, '_check_pdf_accessibility', return_value=False), \
             patch.object(file_opener, '_show_error') as mock_show_error, \
             pytest.raises(IOError):
            
            file_opener._open_pdf_file(pdf_path, 1, ['test'])

    def test_open_pdf_file_acrobat_not_found(self, file_opener, sample_files):
        """Adobe Acrobatが見つからない場合のテスト"""
        pdf_path = sample_files['pdf']
        file_opener.acrobat_path = '/nonexistent/acrobat.exe'
        
        with patch.object(file_opener, '_check_pdf_accessibility', return_value=True), \
             patch.object(file_opener, '_show_error') as mock_show_error, \
             pytest.raises(FileNotFoundError):
            
            file_opener._open_pdf_file(pdf_path, 1, ['test'])

    @patch('service.file_opener.open_pdf')
    @patch('os.path.exists')
    def test_open_pdf_file_success(self, mock_exists, mock_open_pdf, file_opener, sample_files):
        """PDF正常オープンのテスト"""
        pdf_path = sample_files['pdf']
        mock_exists.return_value = True

        with patch.object(file_opener, '_check_pdf_accessibility', return_value=True):
            file_opener._open_pdf_file(pdf_path, 1, ['test'])

            mock_open_pdf.assert_called_once_with(pdf_path, file_opener.acrobat_path, 1, ['test'], True)

    @patch('service.file_opener.open_pdf')  
    @patch('os.path.exists')
    def test_open_pdf_file_subprocess_error(self, mock_exists, mock_open_pdf, file_opener, sample_files):
        """PDF開く際のサブプロセスエラーテスト"""
        pdf_path = sample_files['pdf']
        mock_exists.return_value = True
        mock_open_pdf.side_effect = subprocess.SubprocessError("Process failed")
        
        with patch.object(file_opener, '_check_pdf_accessibility', return_value=True), \
             patch.object(file_opener, '_show_error') as mock_show_error, \
             pytest.raises(subprocess.SubprocessError):
            
            file_opener._open_pdf_file(pdf_path, 1, ['test'])

    # =============================================================================
    # _check_pdf_accessibility() メソッドのテスト
    # =============================================================================
    
    def test_check_pdf_accessibility_valid_pdf(self, file_opener, sample_files):
        """有効なPDFファイルのアクセシビリティチェック"""
        pdf_path = sample_files['pdf']
        
        result = file_opener._check_pdf_accessibility(pdf_path)
        assert result == True

    def test_check_pdf_accessibility_invalid_pdf(self, file_opener, temp_dir):
        """無効なPDFファイルのアクセシビリティチェック"""
        invalid_pdf_path = os.path.join(temp_dir, 'invalid.pdf')
        with open(invalid_pdf_path, 'w') as f:
            f.write('This is not a PDF file')
        
        result = file_opener._check_pdf_accessibility(invalid_pdf_path)
        assert result == False

    def test_check_pdf_accessibility_nonexistent_file(self, file_opener):
        """存在しないPDFファイルのアクセシビリティチェック"""
        result = file_opener._check_pdf_accessibility('/nonexistent/file.pdf')
        assert result == False

    def test_check_pdf_accessibility_io_error(self, file_opener, sample_files):
        """IOエラー発生時のアクセシビリティチェック"""
        pdf_path = sample_files['pdf']
        
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = file_opener._check_pdf_accessibility(pdf_path)
            assert result == False

    # =============================================================================
    # _open_text_file() メソッドのテスト
    # =============================================================================
    
    @patch('service.file_opener.open_text_file')
    def test_open_text_file_success(self, mock_open_text, file_opener, sample_files):
        """テキストファイル正常オープンのテスト"""
        txt_path = sample_files['txt']
        
        file_opener._open_text_file(txt_path, ['test'])
        
        mock_open_text.assert_called_once_with(txt_path, ['test'], 16)

    @patch('service.file_opener.open_text_file')
    def test_open_text_file_io_error(self, mock_open_text, file_opener, sample_files):
        """テキストファイルIOエラーのテスト"""
        txt_path = sample_files['txt']
        mock_open_text.side_effect = IOError("File access denied")
        
        with patch.object(file_opener, '_show_error') as mock_show_error, \
             pytest.raises(IOError):
            
            file_opener._open_text_file(txt_path, ['test'])

    @patch('service.file_opener.open_text_file')
    def test_open_text_file_value_error(self, mock_open_text, file_opener, sample_files):
        """テキストファイル処理エラーのテスト"""
        txt_path = sample_files['txt']
        mock_open_text.side_effect = ValueError("Encoding error")
        
        with patch.object(file_opener, '_show_error') as mock_show_error, \
             pytest.raises(ValueError):
            
            file_opener._open_text_file(txt_path, ['test'])

    # =============================================================================
    # open_folder() メソッドのテスト
    # =============================================================================
    
    @patch('os.startfile')
    def test_open_folder_success(self, mock_startfile, file_opener, temp_dir):
        """フォルダ正常オープンのテスト"""
        file_opener.open_folder(temp_dir)
        
        mock_startfile.assert_called_once_with(temp_dir)

    @patch('os.startfile')
    def test_open_folder_not_found(self, mock_startfile, file_opener):
        """存在しないフォルダのテスト"""
        mock_startfile.side_effect = FileNotFoundError()
        
        with patch.object(file_opener, '_show_error') as mock_show_error:
            file_opener.open_folder('/nonexistent/folder')
            
            mock_show_error.assert_called_once_with(ERROR_MESSAGES['FOLDER_NOT_FOUND'])

    @patch('os.startfile')
    def test_open_folder_os_error(self, mock_startfile, file_opener, temp_dir):
        """フォルダオープンOSエラーのテスト"""
        mock_startfile.side_effect = OSError("Access denied")
        
        with patch.object(file_opener, '_show_error') as mock_show_error:
            file_opener.open_folder(temp_dir)
            
            mock_show_error.assert_called_once()

    @patch('os.startfile')
    def test_open_folder_general_exception(self, mock_startfile, file_opener, temp_dir):
        """フォルダオープン一般例外のテスト"""
        mock_startfile.side_effect = Exception("Unexpected error")
        
        with patch.object(file_opener, '_show_error') as mock_show_error:
            file_opener.open_folder(temp_dir)
            
            mock_show_error.assert_called_once()

    # =============================================================================
    # cleanup_resources() メソッドのテスト
    # =============================================================================
    
    @patch('service.file_opener.temp_file_manager.cleanup_all')
    def test_cleanup_resources_success(self, mock_cleanup, file_opener):
        """リソースクリーンアップ成功のテスト"""
        file_opener._last_opened_file = "/some/file.pdf"
        
        file_opener.cleanup_resources()
        
        mock_cleanup.assert_called_once()
        assert file_opener._last_opened_file == ""

    @patch('service.file_opener.temp_file_manager.cleanup_all')
    def test_cleanup_resources_exception(self, mock_cleanup, file_opener):
        """リソースクリーンアップ例外のテスト"""
        mock_cleanup.side_effect = Exception("Cleanup failed")
        
        # 例外が発生してもクラッシュしないことを確認
        file_opener.cleanup_resources()
        
        mock_cleanup.assert_called_once()

    # =============================================================================
    # _show_error() メソッドのテスト
    # =============================================================================
    
    @patch('PyQt5.QtWidgets.QMessageBox.warning')
    def test_show_error_static_method(self, mock_warning):
        """静的エラー表示メソッドのテスト"""
        FileOpener._show_error("Test error message")
        
        mock_warning.assert_called_once_with(None, "エラー", "Test error message")

    # =============================================================================
    # 統合テスト
    # =============================================================================
    
    def test_file_type_detection_integration(self, file_opener, sample_files):
        """ファイル形式検出の統合テスト"""
        test_cases = [
            (sample_files['pdf'], '_open_pdf_file'),
            (sample_files['txt'], '_open_text_file'),
            (sample_files['md'], '_open_text_file')
        ]
        
        for file_path, expected_method in test_cases:
            with patch.object(file_opener, expected_method) as mock_method:
                file_opener.open_file(file_path, 1, ['test'])
                mock_method.assert_called_once()

    @patch('service.file_opener.temp_file_manager.cleanup_all')
    def test_same_file_reopening_integration(self, mock_cleanup, file_opener, sample_files):
        """同一ファイル再オープンの統合テスト"""
        pdf_path = sample_files['pdf']
        
        with patch.object(file_opener, '_open_pdf_file'):
            # 初回オープン
            file_opener.open_file(pdf_path, 1, ['test'])
            assert file_opener._last_opened_file == pdf_path
            
            # 同じファイルを再オープン
            file_opener.open_file(pdf_path, 2, ['different_terms'])
            
            # クリーンアップが呼ばれることを確認
            mock_cleanup.assert_called()

    def test_multiple_file_types_handling(self, file_opener, sample_files):
        """複数ファイル形式の処理テスト"""
        files_and_methods = [
            (sample_files['pdf'], '_open_pdf_file'),
            (sample_files['txt'], '_open_text_file'),
            (sample_files['md'], '_open_text_file')
        ]
        
        last_files = []
        
        for file_path, method_name in files_and_methods:
            with patch.object(file_opener, method_name):
                file_opener.open_file(file_path, 1, ['test'])
                last_files.append(file_opener._last_opened_file)
        
        # 各ファイルが正しく記録されることを確認
        expected_files = [sample_files['pdf'], sample_files['txt'], sample_files['md']]
        assert last_files == expected_files


class TestFileOpenerEdgeCases:
    """FileOpenerのエッジケーステスト"""
    
    @pytest.fixture
    def file_opener_edge(self):
        """エッジケーステスト用FileOpener"""
        mock_config = MagicMock()
        mock_config.find_available_acrobat_path.return_value = None  # Noneを返す（空のパスになる）
        mock_config.get_html_font_size.return_value = 0  # 無効なフォントサイズ
        return FileOpener(mock_config)

    def test_empty_acrobat_path(self, file_opener_edge, temp_dir):
        """空のAcrobatパスでのテスト"""
        pdf_path = os.path.join(temp_dir, 'test.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\ntest')
        
        with patch.object(file_opener_edge, '_check_pdf_accessibility', return_value=True), \
             patch.object(file_opener_edge, '_show_error') as mock_show_error, \
             pytest.raises(FileNotFoundError):
            
            file_opener_edge._open_pdf_file(pdf_path, 1, ['test'])

    def test_zero_font_size(self, file_opener_edge, temp_dir):
        """フォントサイズが0の場合のテスト"""
        txt_path = os.path.join(temp_dir, 'test.txt')
        with open(txt_path, 'w') as f:
            f.write('test content')
        
        with patch('service.file_opener.open_text_file') as mock_open_text:
            file_opener_edge._open_text_file(txt_path, ['test'])
            
            # フォントサイズ0でも処理が続行されることを確認
            mock_open_text.assert_called_once_with(txt_path, ['test'], 0)

    def test_large_position_value(self, temp_dir):
        """大きなposition値でのテスト"""
        pdf_path = os.path.join(temp_dir, 'test.pdf')
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\ntest')

        # 有効なAcrobatパスを持つFileOpenerを作成
        mock_config = MagicMock()
        mock_config.find_available_acrobat_path.return_value = r'C:\Program Files\Adobe\Acrobat.exe'
        mock_config.get_html_font_size.return_value = 16
        file_opener = FileOpener(mock_config)

        large_position = 999999

        with patch.object(file_opener, '_check_pdf_accessibility', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch('service.file_opener.open_pdf') as mock_open_pdf:

            file_opener._open_pdf_file(pdf_path, large_position, ['test'])

            # 大きなposition値でも正常に処理されることを確認
            mock_open_pdf.assert_called_once_with(pdf_path, r'C:\Program Files\Adobe\Acrobat.exe', large_position, ['test'], True)

    def test_empty_search_terms(self, file_opener_edge, temp_dir):
        """空の検索語リストでのテスト"""
        txt_path = os.path.join(temp_dir, 'test.txt')
        with open(txt_path, 'w') as f:
            f.write('test content')
        
        with patch('service.file_opener.open_text_file') as mock_open_text:
            file_opener_edge._open_text_file(txt_path, [])
            
            # 空の検索語でも処理が続行されることを確認
            mock_open_text.assert_called_once_with(txt_path, [], 0)

    def test_unicode_file_paths(self, file_opener_edge, temp_dir):
        """Unicode文字を含むファイルパスのテスト"""
        unicode_filename = os.path.join(temp_dir, 'テスト_файл_测试.txt')
        with open(unicode_filename, 'w', encoding='utf-8') as f:
            f.write('Unicode test content')
        
        with patch('service.file_opener.open_text_file') as mock_open_text:
            file_opener_edge._open_text_file(unicode_filename, ['test'])
            
            mock_open_text.assert_called_once_with(unicode_filename, ['test'], 0)

    def test_special_characters_in_search_terms(self, file_opener_edge, temp_dir):
        """検索語に特殊文字が含まれる場合のテスト"""
        txt_path = os.path.join(temp_dir, 'special.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Special characters: !@#$%^&*()')
        
        special_terms = ['!@#$%', '^&*()', '正規表現[.*]', 'タブ\t文字']
        
        with patch('service.file_opener.open_text_file') as mock_open_text:
            file_opener_edge._open_text_file(txt_path, special_terms)
            
            mock_open_text.assert_called_once_with(txt_path, special_terms, 0)