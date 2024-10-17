import pytest
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog, QInputDialog, QPushButton
from PyQt5.QtCore import Qt
from directory_widget import DirectoryWidget
import os

class MockConfigManager:
    def __init__(self):
        self.directories = []
        self.last_directory = ""

    def get_directories(self):
        return self.directories

    def set_directories(self, dirs):
        self.directories = dirs

    def get_last_directory(self):
        return self.last_directory

    def set_last_directory(self, dir):
        self.last_directory = dir

@pytest.fixture(scope="session")
def qapp():
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def directory_widget(qapp, qtbot):
    config_manager = MockConfigManager()
    widget = DirectoryWidget(config_manager)
    qtbot.addWidget(widget)
    return widget

def find_button_by_text(widget, text):
    for child in widget.findChildren(QPushButton):
        if child.text() == text:
            return child
    return None

def test_initialization(directory_widget):
    assert directory_widget.dir_combo.count() == 0
    assert directory_widget.include_subdirs_checkbox.isChecked()

@pytest.mark.parametrize("test_dir", ["/test/dir1", "C:\\test\\dir2"])
def test_add_directory(directory_widget, qtbot, monkeypatch, test_dir):
    monkeypatch.setattr(QFileDialog, 'getExistingDirectory', lambda *args: test_dir)
    add_button = find_button_by_text(directory_widget, "追加")
    assert add_button is not None, "追加ボタンが見つかりません"
    qtbot.mouseClick(add_button, Qt.LeftButton)
    assert directory_widget.dir_combo.count() == 1
    assert directory_widget.dir_combo.currentText() == test_dir
    assert directory_widget.config_manager.get_last_directory() == test_dir

@pytest.mark.parametrize("old_dir,new_dir", [("/old/dir", "/new/dir"), ("C:\\old\\dir", "C:\\new\\dir")])
def test_edit_directory(directory_widget, qtbot, monkeypatch, old_dir, new_dir):
    directory_widget.config_manager.set_directories([old_dir])
    directory_widget.dir_combo.addItem(old_dir)
    directory_widget.dir_combo.setCurrentText(old_dir)
    monkeypatch.setattr(QInputDialog, 'getText', lambda *args, **kwargs: (new_dir, True))
    edit_button = find_button_by_text(directory_widget, "編集")
    assert edit_button is not None, "編集ボタンが見つかりません"
    qtbot.mouseClick(edit_button, Qt.LeftButton)
    assert directory_widget.dir_combo.currentText() == new_dir
    assert directory_widget.config_manager.get_directories() == [new_dir]

@pytest.mark.parametrize("test_dir", ["/test/dir", "C:\\test\\dir"])
def test_delete_directory(directory_widget, qtbot, monkeypatch, test_dir):
    directory_widget.config_manager.set_directories([test_dir])
    directory_widget.dir_combo.addItem(test_dir)
    directory_widget.dir_combo.setCurrentText(test_dir)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.Yes)
    delete_button = find_button_by_text(directory_widget, "削除")
    assert delete_button is not None, "削除ボタンが見つかりません"
    qtbot.mouseClick(delete_button, Qt.LeftButton)
    assert directory_widget.dir_combo.count() == 0
    assert directory_widget.config_manager.get_directories() == []

def test_include_subdirs(directory_widget):
    assert directory_widget.include_subdirs()
    directory_widget.include_subdirs_checkbox.setChecked(False)
    assert not directory_widget.include_subdirs()

@pytest.mark.parametrize("valid_dir,invalid_dir", [("/valid/dir", "/invalid/dir"), ("C:\\valid\\dir", "C:\\invalid\\dir")])
def test_validate_directory(directory_widget, monkeypatch, valid_dir, invalid_dir):
    monkeypatch.setattr(os.path, 'isdir', lambda path: path == valid_dir)
    directory_widget.dir_combo.setCurrentText(valid_dir)
    assert directory_widget.dir_combo.styleSheet() == ""
    directory_widget.dir_combo.setCurrentText(invalid_dir)
    assert "background-color: #FFCCCC;" in directory_widget.dir_combo.styleSheet()

def test_update_last_directory(directory_widget, monkeypatch):
    test_dir = "/test/dir"
    monkeypatch.setattr(os.path, 'isdir', lambda path: True)
    directory_widget.dir_combo.setCurrentText(test_dir)
    assert directory_widget.config_manager.get_last_directory() == test_dir
