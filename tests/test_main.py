import pytest
import re
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QApplication
from main import main, VERSION, LAST_UPDATED


def test_version_format():
    assert isinstance(VERSION, str), "VERSIONは文字列であるべきです"
    assert re.match(r'^\d+\.\d+\.\d+$', VERSION), "VERSIONは 'X.Y.Z' 形式であるべきです"


def test_last_updated_format():
    assert isinstance(LAST_UPDATED, str), "LAST_UPDATEDは文字列であるべきです"
    assert re.match(r'^\d{4}/\d{2}/\d{2}$', LAST_UPDATED), "LAST_UPDATEDは 'YYYY/MM/DD' 形式であるべきです"


@pytest.fixture
def mock_qapplication(monkeypatch):
    mock_app = MagicMock(spec=QApplication)
    monkeypatch.setattr(QApplication, '__init__', lambda *args: None)
    monkeypatch.setattr(QApplication, 'exec_', mock_app.exec_)
    return mock_app


@pytest.fixture
def mock_config_manager():
    return MagicMock()


@pytest.fixture
def mock_main_window():
    with patch('main.MainWindow') as mock:
        yield mock


def test_main(mock_qapplication, mock_config_manager, mock_main_window):
    with patch('main.ConfigManager', return_value=mock_config_manager):
        with patch('main.sys.exit') as mock_exit:
            main()

    mock_main_window.assert_called_once_with(mock_config_manager)
    mock_main_window.return_value.show.assert_called_once()
    mock_qapplication.exec_.assert_called_once()
    mock_exit.assert_called_once_with(mock_qapplication.exec_.return_value)
