import pytest
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import Qt, QRect
from unittest.mock import MagicMock, patch
from gui import MainWindow
from config_manager import ConfigManager


@pytest.fixture
def app(qtbot):
    test_app = QApplication([])
    return test_app


@pytest.fixture
def mock_config_manager():
    config = ConfigManager()
    config.get_window_geometry = MagicMock(return_value=(100, 100, 800, 600))
    config.get_font_size = MagicMock(return_value=12)
    config.get_directories = MagicMock(return_value=["/test/dir1", "/test/dir2"])
    config.get_last_directory = MagicMock(return_value="/test/dir1")
    config.get_file_extensions = MagicMock(return_value=[".txt", ".pdf"])
    config.get_context_length = MagicMock(return_value=50)
    config.get_acrobat_path = MagicMock(return_value="/path/to/acrobat")
    config.get_html_font_size = MagicMock(return_value=16)
    return config


@pytest.fixture
def main_window(qtbot, mock_config_manager):
    window = MainWindow(mock_config_manager)
    qtbot.addWidget(window)
    return window


def test_window_initialization(main_window):
    assert main_window.windowTitle() == "マニュアル検索アプリ"
    assert main_window.geometry().getRect() == (100, 100, 800, 600)


@patch('gui.FileSearcher')
def test_start_search(mock_file_searcher, main_window, qtbot):
    main_window.search_input.setText("test1,test2")
    main_window.dir_combo.setCurrentText("/test/dir1")

    mock_searcher = MagicMock()
    mock_file_searcher.return_value = mock_searcher

    qtbot.mouseClick(main_window.findChild(QPushButton, "検索"), Qt.LeftButton)

    mock_file_searcher.assert_called_once()
    mock_searcher.start.assert_called_once()


@patch('gui.open_pdf')
def test_open_pdf_file(mock_open_pdf, main_window, qtbot):
    main_window.current_file_path = "/test/file.pdf"
    main_window.current_position = 5
    main_window.search_input.setText("test")

    qtbot.mouseClick(main_window.open_file_button, Qt.LeftButton)

    mock_open_pdf.assert_called_once_with(
        "/test/file.pdf",
        "/path/to/acrobat",
        5,
        ["test"]
    )


@patch('gui.open_text_file')
def test_open_text_file(mock_open_text_file, main_window, qtbot):
    main_window.current_file_path = "/test/file.txt"
    main_window.search_input.setText("test")

    qtbot.mouseClick(main_window.open_file_button, Qt.LeftButton)

    mock_open_text_file.assert_called_once_with(
        "/test/file.txt",
        ["test"],
        16
    )


def test_highlight_content(main_window):
    main_window.search_input.setText("test,example")
    main_window.search_term_colors = {"test": "yellow", "example": "lightgreen"}
    highlighted = main_window.highlight_content("This is a test example.")
    assert '<span style="background-color: yellow;">test</span>' in highlighted
    assert '<span style="background-color: lightgreen;">example</span>' in highlighted

# 他のメソッドに対するテストも同様に追加できます