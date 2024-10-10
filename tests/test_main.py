import unittest
from unittest.mock import patch, MagicMock, ANY
import re
from datetime import datetime
from main import main, VERSION, LAST_UPDATED

class TestMain(unittest.TestCase):

    @patch('main.QApplication')
    @patch('main.ConfigManager')
    @patch('main.MainWindow')
    def test_main_function(self, mock_main_window, mock_config_manager, mock_qapplication):
        # モックオブジェクトのセットアップ
        mock_app = MagicMock()
        mock_qapplication.return_value = mock_app
        mock_window = MagicMock()
        mock_main_window.return_value = mock_window

        # main関数の実行
        with patch('sys.exit') as mock_exit:
            main()

        # アサーション
        mock_qapplication.assert_called_once_with(ANY)  # ANYを使用して任意の引数を許可
        mock_config_manager.assert_called_once()
        mock_main_window.assert_called_once_with(mock_config_manager.return_value)
        mock_window.show.assert_called_once()
        mock_app.exec_.assert_called_once()
        mock_exit.assert_called_once_with(mock_app.exec_.return_value)

    def test_version_format(self):
        # バージョン番号の形式をチェック（例: x.y.z）
        version_pattern = r'^\d+\.\d+\.\d+$'
        self.assertTrue(re.match(version_pattern, VERSION), f"Version '{VERSION}' does not match the expected format")

    def test_last_updated_format(self):
        # 日付形式をチェック（YYYY/MM/DD）
        try:
            date = datetime.strptime(LAST_UPDATED, "%Y/%m/%d")
            self.assertTrue(date <= datetime.now(), "LAST_UPDATED date is in the future")
        except ValueError:
            self.fail(f"LAST_UPDATED '{LAST_UPDATED}' does not match the expected format YYYY/MM/DD")

if __name__ == '__main__':
    unittest.main()
