import pytest
from PyQt5.QtWidgets import QApplication, QListWidgetItem
from unittest.mock import MagicMock
from gui import MainWindow
from PyQt5.QtCore import Qt

@pytest.fixture
def app(qtbot):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

@pytest.fixture
def config_manager():
    # config_managerのモックを作成
    mock = MagicMock()
    mock.get_window_geometry.return_value = (100, 100, 800, 600)
    mock.get_font_size.return_value = 12
    mock.get_directories.return_value = ['/path/to/directory']
    mock.get_last_directory.return_value = '/path/to/directory'
    mock.get_filename_font_size.return_value = 10
    mock.get_result_detail_font_size.return_value = 10
    mock.get_html_font_size.return_value = 10
    mock.get_file_extensions.return_value = ['.txt', '.pdf']
    mock.get_context_length.return_value = 100
    mock.get_acrobat_path.return_value = '/path/to/acrobat'
    return mock

def test_main_window_initialization(qtbot, app, config_manager):
    # MainWindowのインスタンスを作成
    window = MainWindow(config_manager)
    qtbot.addWidget(window)
    window.show()

    # ウィンドウタイトルの確認
    assert window.windowTitle() == "マニュアル検索アプリ"

    # プレースホルダーテキストの確認
    assert window.search_input.placeholderText() == "検索語を入力 ( , または 、区切りで複数語検索)"

    # ディレクトリコンボボックスの項目数の確認
    assert window.dir_combo.count() == len(config_manager.get_directories())

    # サブフォルダを含むチェックボックスの初期状態の確認
    assert window.include_subdirs_checkbox.isChecked() == True

def test_start_search_no_input(qtbot, app, config_manager):
    # 入力がない状態での検索開始のテスト
    window = MainWindow(config_manager)
    qtbot.addWidget(window)
    window.show()

    window.dir_combo.setCurrentText('')
    window.search_input.setText('')
    window.start_search()

    # searcher属性が作成されていないことを確認
    assert not hasattr(window, 'searcher')

def test_start_search_with_input(qtbot, app, config_manager, monkeypatch):
    # 有効な入力での検索開始のテスト
    window = MainWindow(config_manager)
    qtbot.addWidget(window)
    window.show()

    # FileSearcherのモックを作成
    mock_searcher = MagicMock()
    monkeypatch.setattr('gui.FileSearcher', lambda *args, **kwargs: mock_searcher)

    window.dir_combo.setCurrentText('/path/to/directory')
    window.search_input.setText('テスト')
    window.start_search()

    # searcherが開始されたことを確認
    mock_searcher.start.assert_called_once()

def test_add_result(qtbot, app, config_manager):
    # 検索結果の追加のテスト
    window = MainWindow(config_manager)
    qtbot.addWidget(window)
    window.show()

    file_path = '/path/to/file.txt'
    results = [(10, 'これはテストコンテキストです。')]
    window.add_result(file_path, results)

    # リストにアイテムが追加されたことを確認
    assert window.results_list.count() == 1
    item = window.results_list.item(0)
    assert 'file.txt' in item.text()

def test_show_result(qtbot, app, config_manager):
    # 結果の表示のテスト
    window = MainWindow(config_manager)
    qtbot.addWidget(window)
    window.show()

    file_path = '/path/to/file.txt'
    position = 10
    context = 'これはテストコンテキストです。'

    # リストアイテムを作成して結果を表示
    list_item = QListWidgetItem('テストアイテム')
    list_item.setData(Qt.UserRole, (file_path, position, context))
    window.show_result(list_item)

    # 結果表示ウィジェットに正しい内容が表示されているか確認
    assert 'file.txt' in window.result_display.toHtml()
    assert '行: 10' in window.result_display.toHtml()
    assert 'これはテストコンテキストです。' in window.result_display.toHtml()
