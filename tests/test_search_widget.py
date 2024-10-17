import pytest
from PyQt5.QtWidgets import QApplication, QPushButton
from PyQt5.QtCore import Qt
from search_widget import SearchWidget

@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def search_widget(qapp, qtbot):
    widget = SearchWidget(None)  # config_managerはNoneとして渡す
    qtbot.addWidget(widget)
    return widget

def test_search_widget_initialization(search_widget):
    assert search_widget.search_input.placeholderText() == "検索語を入力 ( , または 、区切りで複数語検索)"
    assert search_widget.search_type_combo.count() == 2
    assert search_widget.search_type_combo.itemText(0) == "AND検索(複数語のすべてを含む)"
    assert search_widget.search_type_combo.itemText(1) == "OR検索(複数語のいずれかを含む)"

def test_get_search_terms(search_widget):
    search_widget.search_input.setText("テスト1,テスト2、テスト3")
    assert search_widget.get_search_terms() == ["テスト1", "テスト2", "テスト3"]

    search_widget.search_input.setText("  スペース  ,  前後  、  両方  ")
    assert search_widget.get_search_terms() == ["スペース", "前後", "両方"]

def test_get_search_type(search_widget):
    search_widget.search_type_combo.setCurrentIndex(0)
    assert search_widget.get_search_type() == 'AND'

    search_widget.search_type_combo.setCurrentIndex(1)
    assert search_widget.get_search_type() == 'OR'

def test_search_requested_signal(search_widget, qtbot):
    with qtbot.waitSignal(search_widget.search_requested, timeout=1000):
        search_widget.search_input.setText("テスト")
        qtbot.keyClick(search_widget.search_input, Qt.Key_Return)

    with qtbot.waitSignal(search_widget.search_requested, timeout=1000):
        search_button = search_widget.findChild(QPushButton)
        qtbot.mouseClick(search_button, Qt.LeftButton)
