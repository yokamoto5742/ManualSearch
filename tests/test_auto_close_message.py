import pytest
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from auto_close_message import AutoCloseMessage


@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def auto_close_message(qapp, qtbot):
    widget = AutoCloseMessage()
    qtbot.addWidget(widget)
    return widget


def test_init(auto_close_message):
    assert auto_close_message.isWindow()
    assert auto_close_message.windowFlags() & Qt.WindowStaysOnTopHint
    assert auto_close_message.windowFlags() & Qt.FramelessWindowHint


def test_show_message(auto_close_message, qtbot):
    message = "テストメッセージ"
    auto_close_message.show_message(message, duration=100)

    assert auto_close_message.isVisible()
    assert auto_close_message.label.text() == message

    qtbot.wait(200)
    assert not auto_close_message.isVisible()


def test_auto_close(auto_close_message, qtbot):
    auto_close_message.show_message("自動で閉じるテスト", duration=50)

    assert auto_close_message.isVisible()

    qtbot.wait(100)
    assert not auto_close_message.isVisible()


def test_parent_centering(qapp, qtbot):
    parent = QWidget()
    parent.setGeometry(100, 100, 300, 300)

    auto_close_message = AutoCloseMessage(parent)
    auto_close_message.show_message("親ウィジェットの中心に表示", duration=100)

    parent_center = parent.geometry().center()
    widget_center = auto_close_message.geometry().center()

    assert abs(parent_center.x() - widget_center.x()) <= 1
    assert abs(parent_center.y() - widget_center.y()) <= 1

    qtbot.wait(200)
