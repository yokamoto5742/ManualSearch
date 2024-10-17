import pytest
from unittest.mock import MagicMock, patch
import os
from PyQt5.QtWidgets import QMessageBox
from file_opener import FileOpener


@pytest.fixture
def config_manager_mock():
    config_manager = MagicMock()
    config_manager.get_acrobat_path.return_value = r"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe"
    config_manager.get_html_font_size.return_value = 14
    return config_manager


@pytest.fixture
def file_opener(config_manager_mock):
    return FileOpener(config_manager_mock)


def test_open_file_non_existent(file_opener):
    with patch('os.path.exists', return_value=False), \
            patch.object(QMessageBox, 'warning') as mock_warning:
        file_opener.open_file('non_existent.pdf', 1, ['test'])
        mock_warning.assert_called_once_with(None, "エラー", "ファイルが存在しません。")


def test_open_file_unsupported_extension(file_opener):
    with patch('os.path.exists', return_value=True), \
            patch.object(QMessageBox, 'warning') as mock_warning:
        file_opener.open_file('test.docx', 1, ['test'])
        mock_warning.assert_called_once_with(None, "エラー", "サポートされていないファイル形式です。")


@patch('file_opener.open_pdf')
@patch('file_opener.wait_for_acrobat')
@patch('file_opener.navigate_to_page')
@patch('file_opener.highlight_pdf')
def test_open_pdf_file(mock_highlight_pdf, mock_navigate, mock_wait, mock_open_pdf, file_opener):
    mock_highlight_pdf.return_value = 'highlighted.pdf'
    with patch('subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process

        file_opener.open_pdf_file('test.pdf', 1, ['test'])

        mock_highlight_pdf.assert_called_once_with('test.pdf', ['test'])
        mock_popen.assert_called_once()
        mock_wait.assert_called_once_with(12345)
        mock_navigate.assert_called_once_with(1)


@patch('file_opener.open_text_file')
def test_open_text_file(mock_open_text, file_opener):
    file_opener.open_text_file('test.txt', ['test'])
    mock_open_text.assert_called_once_with('test.txt', ['test'], 14)


@patch('os.startfile')
def test_open_folder(mock_startfile, file_opener):
    file_opener.open_folder('C:\\test_folder')
    mock_startfile.assert_called_once_with('C:\\test_folder')


def test_open_folder_error(file_opener):
    with patch('os.startfile', side_effect=Exception("テストエラー")), \
            patch.object(QMessageBox, 'warning') as mock_warning:
        file_opener.open_folder('C:\\test_folder')
        mock_warning.assert_called_once_with(None, "エラー", "フォルダを開けませんでした: テストエラー")
