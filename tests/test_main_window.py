import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch

from directory_widget import DirectoryWidget
from main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def config_manager():
    mock_config = MagicMock()
    mock_config.get_window_geometry.return_value = (100, 100, 800, 600)
    mock_config.get_font_size.return_value = 12
    mock_config.get_directories.return_value = ["ディレクトリ1", "ディレクトリ2"]
    mock_config.get_last_directory.return_value = "ディレクトリ1"
    return mock_config


@pytest.fixture
def directory_widget(config_manager):
    with patch('directory_widget.QComboBox'):
        return DirectoryWidget(config_manager)


@pytest.fixture
def main_window(app, config_manager, directory_widget, qtbot):
    with patch('main_window.DirectoryWidget', return_value=directory_widget):
        with patch('main_window.SearchWidget'):
            with patch('main_window.ResultsWidget'):
                with patch('main_window.FileOpener'):
                    window = MainWindow(config_manager)
                    qtbot.addWidget(window)
                    return window


def test_main_window_initialization(main_window, config_manager):
    assert main_window.windowTitle() == "マニュアル検索アプリ"
    assert main_window.geometry().getRect() == (100, 100, 800, 600)
    config_manager.get_window_geometry.assert_called_once()
    config_manager.get_font_size.assert_called_once()


def test_directory_widget_initialization(directory_widget, config_manager):
    config_manager.get_directories.assert_called_once()
    config_manager.get_last_directory.assert_called_once()


def test_search_widget_connection(main_window, qtbot):
    with patch.object(main_window, 'start_search') as mock_start_search:
        main_window.search_widget.search_requested.emit()
        mock_start_search.assert_called_once()


def test_results_widget_connection(main_window, qtbot):
    with patch.object(main_window, 'enable_open_buttons') as mock_enable_open_buttons:
        main_window.results_widget.result_selected.emit()
        mock_enable_open_buttons.assert_called_once()


def test_start_search(main_window, qtbot):
    main_window.search_widget.get_search_terms.return_value = "テスト"
    main_window.directory_widget.get_selected_directory.return_value = "/path/to/dir"
    main_window.directory_widget.include_subdirs.return_value = True
    main_window.search_widget.get_search_type.return_value = "全文検索"

    main_window.start_search()

    main_window.results_widget.clear_results.assert_called_once()
    main_window.results_widget.perform_search.assert_called_once_with("/path/to/dir", "テスト", True, "全文検索")
    assert not main_window.open_file_button.isEnabled()
    assert not main_window.open_folder_button.isEnabled()


def test_enable_open_buttons(main_window, qtbot):
    main_window.enable_open_buttons()
    assert main_window.open_file_button.isEnabled()
    assert main_window.open_folder_button.isEnabled()


def test_open_file(main_window, qtbot):
    main_window.results_widget.get_selected_file_info.return_value = ("/path/to/file", 10)
    main_window.search_widget.get_search_terms.return_value = "テスト"

    main_window.open_file()

    main_window.file_opener.open_file.assert_called_once_with("/path/to/file", 10, "テスト")


def test_open_folder(main_window, qtbot):
    main_window.results_widget.get_selected_file_info.return_value = ("/path/to/file", 10)

    main_window.open_folder()

    main_window.file_opener.open_folder.assert_called_once_with("/path/to")


def test_close_event(main_window, qtbot):
    with patch.object(main_window.config_manager, 'set_window_geometry') as mock_set_geometry:
        main_window.close()
        mock_set_geometry.assert_called_once()
