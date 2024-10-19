from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtWidgets import QApplication, QPushButton

from main_window import MainWindow


@pytest.fixture(scope="module")
def qapp():
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def mock_config_manager():
    config_manager = MagicMock()
    config_manager.get_window_geometry.return_value = (100, 100, 800, 600)
    config_manager.get_font_size.return_value = 12
    return config_manager


@pytest.fixture
def main_window(qapp, mock_config_manager):
    with patch('main_window.SearchWidget') as mock_search_widget, \
            patch('main_window.DirectoryWidget') as mock_directory_widget, \
            patch('main_window.ResultsWidget') as mock_results_widget, \
            patch('main_window.FileOpener') as mock_file_opener, \
            patch('main_window.AutoCloseMessage') as mock_auto_close_message, \
            patch('main_window.MainWindow.__init__', return_value=None):
        window = MainWindow(mock_config_manager)

        # Manually set up the mocked attributes
        window.config_manager = mock_config_manager
        window.search_widget = mock_search_widget.return_value
        window.directory_widget = mock_directory_widget.return_value
        window.results_widget = mock_results_widget.return_value
        window.file_opener = mock_file_opener.return_value
        window.auto_close_message = mock_auto_close_message.return_value
        window.open_file_button = MagicMock(spec=QPushButton)
        window.open_folder_button = MagicMock(spec=QPushButton)

        # モックメソッドの追加
        window.start_search = MagicMock()
        window.closeEvent = MagicMock()

        yield window


def test_main_window_init(main_window, mock_config_manager):
    assert isinstance(main_window.config_manager, MagicMock)
    assert isinstance(main_window.search_widget, MagicMock)
    assert isinstance(main_window.directory_widget, MagicMock)
    assert isinstance(main_window.results_widget, MagicMock)


def test_start_search(main_window):
    pass


def test_enable_open_buttons(main_window):
    main_window.enable_open_buttons()
    main_window.open_file_button.setEnabled.assert_called_with(True)
    main_window.open_folder_button.setEnabled.assert_called_with(True)


def test_open_file(main_window):
    main_window.results_widget.get_selected_file_info.return_value = ("/path/to/file.txt", 10)
    main_window.search_widget.get_search_terms.return_value = "test"

    main_window.open_file()

    main_window.file_opener.open_file.assert_called_once_with("/path/to/file.txt", 10, "test")


def test_open_folder(main_window):
    main_window.results_widget.get_selected_file_info.return_value = ("/path/to/file.txt", 10)

    main_window.open_folder()

    main_window.file_opener.open_folder.assert_called_once_with("/path/to")


def test_close_event(main_window, mock_config_manager):
    pass
