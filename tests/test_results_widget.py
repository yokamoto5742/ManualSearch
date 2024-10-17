import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from unittest.mock import MagicMock, patch
from results_widget import ResultsWidget


@pytest.fixture
def app(qtbot):
    return QApplication([])


@pytest.fixture
def config_manager():
    mock_config = MagicMock()
    mock_config.get_filename_font_size.return_value = 12
    mock_config.get_result_detail_font_size.return_value = 10
    mock_config.get_html_font_size.return_value = 14
    mock_config.get_file_extensions.return_value = ['.txt', '.py']
    mock_config.get_context_length.return_value = 50
    return mock_config


@pytest.fixture
def results_widget(qtbot, config_manager):
    widget = ResultsWidget(config_manager)
    qtbot.addWidget(widget)
    return widget


def test_init(results_widget, config_manager):
    assert results_widget.config_manager == config_manager
    assert results_widget.results_list is not None
    assert results_widget.result_display is not None
    assert results_widget.filename_font.pointSize() == 12
    assert results_widget.result_detail_font.pointSize() == 10
    assert results_widget.html_font_size == 14


def test_perform_search(results_widget, qtbot):
    with patch('results_widget.FileSearcher') as mock_searcher:
        results_widget.perform_search('test_dir', ['test'], True, 'normal')

        assert mock_searcher.called
        assert results_widget.progress_dialog is not None
        assert results_widget.progress_dialog.isVisible()


def test_add_result(results_widget, qtbot):
    results_widget.add_result('test_file.txt', [(1, 'test context')])

    assert results_widget.results_list.count() == 1
    item = results_widget.results_list.item(0)
    assert item.text() == 'test_file.txt (行: 1, 一致: 1)'


def test_show_result(results_widget, qtbot):
    results_widget.add_result('test_file.txt', [(1, 'test context')])
    item = results_widget.results_list.item(0)

    with qtbot.waitSignal(results_widget.result_selected):
        results_widget.results_list.itemClicked.emit(item)

    assert 'test_file.txt' in results_widget.result_display.toPlainText()
    assert 'test context' in results_widget.result_display.toPlainText()


def test_clear_results(results_widget, qtbot):
    results_widget.add_result('test_file.txt', [(1, 'test context')])
    assert results_widget.results_list.count() == 1

    results_widget.clear_results()
    assert results_widget.results_list.count() == 0
    assert results_widget.result_display.toPlainText() == ''


def test_get_selected_file_info(results_widget, qtbot):
    results_widget.add_result('test_file.txt', [(1, 'test context')])
    item = results_widget.results_list.item(0)
    results_widget.results_list.itemClicked.emit(item)

    file_path, position = results_widget.get_selected_file_info()
    assert file_path == 'test_file.txt'
    assert position == 1
