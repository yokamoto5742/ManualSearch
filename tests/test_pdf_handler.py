import pytest
import subprocess
import tempfile
import time
import psutil
import pyautogui
import fitz
from unittest.mock import patch, MagicMock
from pdf_handler import open_pdf, wait_for_acrobat, navigate_to_page, highlight_pdf


@pytest.fixture
def mock_subprocess(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(subprocess, 'Popen', mock)
    return mock


@pytest.fixture
def mock_psutil(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(psutil, 'Process', mock)
    return mock


@pytest.fixture
def mock_pyautogui(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(pyautogui, 'getActiveWindowTitle', mock)
    monkeypatch.setattr(pyautogui, 'hotkey', mock.hotkey)
    monkeypatch.setattr(pyautogui, 'write', mock.write)
    monkeypatch.setattr(pyautogui, 'press', mock.press)
    return mock


@pytest.fixture
def mock_fitz(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(fitz, 'open', mock)
    return mock


def test_open_pdf(mock_subprocess, mock_psutil, mock_pyautogui):
    with patch('pdf_handler.highlight_pdf') as mock_highlight_pdf, \
            patch('pdf_handler.wait_for_acrobat') as mock_wait_for_acrobat, \
            patch('pdf_handler.navigate_to_page') as mock_navigate_to_page:
        mock_highlight_pdf.return_value = '/path/to/highlighted.pdf'
        mock_wait_for_acrobat.return_value = True

        open_pdf('/path/to/file.pdf', '/path/to/acrobat', 5, ['test'])

        mock_highlight_pdf.assert_called_once_with('/path/to/file.pdf', ['test'])
        mock_subprocess.assert_called_once_with(['/path/to/acrobat', '/path/to/highlighted.pdf'])
        mock_wait_for_acrobat.assert_called_once()
        mock_navigate_to_page.assert_called_once_with(5)


def test_wait_for_acrobat(mock_psutil, mock_pyautogui):
    mock_process = mock_psutil.return_value
    mock_process.status.return_value = psutil.STATUS_RUNNING
    mock_pyautogui.return_value = "Acrobat"

    assert wait_for_acrobat(12345, timeout=1)

    mock_psutil.assert_called_with(12345)
    mock_process.status.assert_called()
    mock_pyautogui.assert_called()


def test_navigate_to_page(mock_pyautogui):
    navigate_to_page(10)

    mock_pyautogui.hotkey.assert_called_once_with('ctrl', 'shift', 'n')
    mock_pyautogui.write.assert_called_once_with('10')
    mock_pyautogui.press.assert_called_once_with('enter')


def test_highlight_pdf(mock_fitz):
    mock_doc = MagicMock()
    mock_fitz.return_value = mock_doc
    mock_page = MagicMock()
    mock_doc.__iter__.return_value = [mock_page]
    mock_highlight = MagicMock()
    mock_page.add_highlight_annot.return_value = mock_highlight

    with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
        mock_temp_file.return_value.__enter__.return_value.name = '/path/to/temp.pdf'
        result = highlight_pdf('/path/to/file.pdf', ['test1', 'test2'])

    assert isinstance(result, str)
    assert result == '/path/to/temp.pdf'
    mock_fitz.assert_called_once_with('/path/to/file.pdf')
    mock_page.search_for.assert_any_call('test1')
    mock_page.search_for.assert_any_call('test2')
    mock_doc.save.assert_called()
    mock_doc.close.assert_called()
