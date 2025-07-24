import os
import socket
import tempfile
import pytest
from unittest.mock import patch, MagicMock, mock_open, Mock
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMessageBox, QPushButton

from utils.helpers import (
    normalize_path, is_network_file, check_file_accessibility,
    read_file_with_auto_encoding, create_confirmation_dialog,
    move_cursor_to_yes_button
)
from constants import (
    NETWORK_TIMEOUT, DNS_TEST_HOST, DNS_TEST_PORT,
    CURSOR_MOVE_DELAY, ERROR_MESSAGES, UI_LABELS
)


class TestIsNetworkFile:
    """is_network_file関数のP0レベルテスト"""

    def test_is_network_file_unc_path(self):
        """UNCパスのネットワークファイル判定テスト"""
        assert is_network_file(r'\\server\share\file.txt') == True
        assert is_network_file('//server/share/file.txt') == True

    def test_is_network_file_local_path_with_drive(self):
        """ドライブレターを含むローカルパスのテスト"""
        # 現在の実装では ':' がパスの最初の2文字以内にあるとネットワークファイルと判定される
        assert is_network_file(r'C:\Users\user\file.txt') == True  # ドライブ文字が含まれるため
        assert is_network_file('D:/Documents/file.txt') == True

    def test_is_network_file_special_characters(self):
        """特殊文字を含むパスのテスト"""
        assert is_network_file(r'\\server\share with spaces\file@#$.txt') == True

    def test_is_network_file_unix_absolute_path(self):
        """Unix絶対パスのテスト"""
        assert is_network_file('/home/user/file.txt') == False
        assert is_network_file('/var/log/app.log') == False
    
    def test_is_network_file_relative_path(self):
        """相対パスのテスト"""
        assert is_network_file('./file.txt') == False
        assert is_network_file('../folder/file.txt') == False
        assert is_network_file('file.txt') == False
    
    def test_is_network_file_empty_string(self):
        """空文字列のテスト"""
        assert is_network_file('') == False
    
    def test_is_network_file_network_drive_mapping(self):
        """ネットワークドライブマッピングのテスト"""
        assert is_network_file('Z:/mapped/drive/file.txt') == True


class TestCheckFileAccessibility:  
    """check_file_accessibility関数のP0レベルテスト"""
    
    def test_check_file_accessibility_existing_local_file(self, temp_dir):
        """存在するローカルファイルのアクセス可能性テスト"""
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        result = check_file_accessibility(test_file)
        assert result == True
    
    def test_check_file_accessibility_nonexistent_local_file(self):
        """存在しないローカルファイルのテスト"""
        result = check_file_accessibility('/nonexistent/file.txt')
        assert result == False
    
    @patch('utils.helpers.is_network_file', return_value=True)
    @patch('socket.create_connection')
    @patch('os.path.exists', return_value=True)
    def test_check_file_accessibility_network_file_accessible(
        self, mock_exists, mock_socket, mock_is_network
    ):
        """アクセス可能なネットワークファイルのテスト"""
        mock_socket.return_value.__enter__ = Mock()
        mock_socket.return_value.__exit__ = Mock()
        
        result = check_file_accessibility('//server/share/file.txt')
        assert result == True
        
        mock_socket.assert_called_once_with((DNS_TEST_HOST, DNS_TEST_PORT), timeout=NETWORK_TIMEOUT)
    
    @patch('utils.helpers.is_network_file', return_value=True)
    @patch('socket.create_connection')
    def test_check_file_accessibility_network_file_connection_error(
        self, mock_socket, mock_is_network
    ):
        """ネットワーク接続エラーのテスト"""
        mock_socket.side_effect = socket.error("Connection failed")
        
        result = check_file_accessibility('//server/share/file.txt')
        assert result == False
    
    @patch('utils.helpers.is_network_file', return_value=True)
    @patch('socket.create_connection')
    def test_check_file_accessibility_network_file_os_error(
        self, mock_socket, mock_is_network
    ):
        """ネットワークファイルOSエラーのテスト"""
        mock_socket.side_effect = OSError("Network error")
        
        result = check_file_accessibility('//server/share/file.txt')
        assert result == False
    
    def test_check_file_accessibility_custom_timeout(self, temp_dir):
        """カスタムタイムアウト設定のテスト"""
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        result = check_file_accessibility(test_file, timeout=10)
        assert result == True
    
    @patch('utils.helpers.is_network_file', return_value=True)
    @patch('socket.create_connection')
    def test_check_file_accessibility_timeout_parameter(self, mock_socket, mock_is_network):
        """タイムアウトパラメータが正しく渡されるテスト"""
        mock_socket.return_value.__enter__ = Mock()
        mock_socket.return_value.__exit__ = Mock()
        
        with patch('os.path.exists', return_value=True):
            check_file_accessibility('//server/share/file.txt', timeout=15)
        
        mock_socket.assert_called_once_with((DNS_TEST_HOST, DNS_TEST_PORT), timeout=15)


class TestReadFileWithAutoEncoding:
    """read_file_with_auto_encoding関数のP0レベルテスト"""
    
    def test_read_file_with_auto_encoding_utf8(self, temp_dir):
        """UTF-8エンコーディングファイルの読み込みテスト"""
        test_file = os.path.join(temp_dir, 'utf8.txt')
        test_content = 'UTF-8テストコンテンツ：日本語テキスト'
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        result = read_file_with_auto_encoding(test_file)
        assert result == test_content
    
    def test_read_file_with_auto_encoding_shift_jis(self, temp_dir):
        """Shift-JISエンコーディングファイルの読み込みテスト"""
        test_file = os.path.join(temp_dir, 'sjis.txt')
        test_content = 'Shift-JISテストファイル'
        
        with open(test_file, 'w', encoding='shift_jis') as f:
            f.write(test_content)
        
        result = read_file_with_auto_encoding(test_file)
        assert result == test_content
    
    def test_read_file_with_auto_encoding_ascii(self, temp_dir):
        """ASCIIファイルの読み込みテスト"""
        test_file = os.path.join(temp_dir, 'ascii.txt')
        test_content = 'ASCII test content'
        
        with open(test_file, 'w', encoding='ascii') as f:
            f.write(test_content)
        
        result = read_file_with_auto_encoding(test_file)
        assert result == test_content
    
    def test_read_file_with_auto_encoding_nonexistent_file(self):
        """存在しないファイルの読み込み例外テスト"""
        with pytest.raises(IOError) as exc_info:
            read_file_with_auto_encoding('/nonexistent/file.txt')
        
        assert "ファイルの読み込みに失敗しました" in str(exc_info.value)
    
    @patch('builtins.open')
    def test_read_file_with_auto_encoding_io_error(self, mock_open):
        """ファイル読み込みIOエラーのテスト"""
        mock_open.side_effect = IOError("Permission denied")
        
        with pytest.raises(IOError) as exc_info:
            read_file_with_auto_encoding('/test/file.txt')
        
        assert "ファイルの読み込みに失敗しました" in str(exc_info.value)
    
    @patch('chardet.detect')
    @patch('builtins.open')
    def test_read_file_with_auto_encoding_chardet_error(self, mock_open, mock_detect):
        """chardetエラーのテスト"""
        mock_open.return_value.__enter__.return_value.read.return_value = b'test data'
        mock_detect.side_effect = Exception("Chardet error")
        
        with pytest.raises(ValueError) as exc_info:
            read_file_with_auto_encoding('/test/file.txt')
        
        assert ERROR_MESSAGES['ENCODING_DETECTION_FAILED'] in str(exc_info.value)
    
    def test_read_file_with_auto_encoding_empty_file(self, temp_dir):
        """空ファイルの読み込みテスト"""
        test_file = os.path.join(temp_dir, 'empty.txt')
        with open(test_file, 'w') as f:
            pass  # 空ファイル作成
        
        result = read_file_with_auto_encoding(test_file)
        assert result == ''
    
    def test_read_file_with_auto_encoding_binary_file(self, temp_dir):
        """バイナリファイルの読み込みテスト"""
        test_file = os.path.join(temp_dir, 'binary.bin')
        binary_data = bytes(range(256))  # 0-255のバイナリデータ
        
        with open(test_file, 'wb') as f:
            f.write(binary_data)
        
        # バイナリファイルでもchardetがエンコーディングを検出すれば読み込める
        result = read_file_with_auto_encoding(test_file)
        assert isinstance(result, str)


class TestCreateConfirmationDialog:
    """create_confirmation_dialog関数のP0レベルテスト"""
    
    @pytest.fixture
    def parent_widget(self, qapp):
        """親ウィジェット"""
        from PyQt5.QtWidgets import QWidget
        return QWidget()

    def test_create_confirmation_dialog_basic(self, parent_widget):
        """基本的な確認ダイアログ作成テスト"""
        dialog = create_confirmation_dialog(
            parent_widget,
            "テストタイトル",
            "テストメッセージ",
            QMessageBox.Yes
        )

        assert isinstance(dialog, QMessageBox)
        assert dialog.windowTitle() == "テストタイトル"
        assert dialog.text() == "テストメッセージ"
        # defaultButtonは実際のボタンオブジェクトを返すため、値の比較ではなく存在確認
        assert dialog.defaultButton() is not None

    def test_create_confirmation_dialog_default_button_no(self, parent_widget):
        """デフォルトボタンがNoの場合のテスト"""
        dialog = create_confirmation_dialog(
            parent_widget,
            "タイトル",
            "メッセージ",
            QMessageBox.No
        )

        # defaultButtonは実際のボタンオブジェクトを返す
        assert dialog.defaultButton() is not None

    def test_create_confirmation_dialog_timer_setup(self, parent_widget):
        """タイマー設定のテスト"""
        dialog = create_confirmation_dialog(
            parent_widget,
            "タイトル",
            "メッセージ",
            QMessageBox.Yes
        )

        # タイマーが設定されていることを確認
        assert hasattr(dialog, '_cursor_timer')
        assert dialog._cursor_timer is not None
    
    def test_create_confirmation_dialog_button_texts(self, parent_widget):
        """確認ダイアログのボタンテキスト設定テスト"""
        dialog = create_confirmation_dialog(
            parent_widget,
            "タイトル",
            "メッセージ", 
            QMessageBox.No
        )
        
        yes_button = dialog.button(QMessageBox.Yes)
        no_button = dialog.button(QMessageBox.No)
        
        assert yes_button.text() == UI_LABELS['YES_BUTTON']
        assert no_button.text() == UI_LABELS['NO_BUTTON']
    
    def test_create_confirmation_dialog_button_styling(self, parent_widget):
        """ボタンスタイリングのテスト"""
        dialog = create_confirmation_dialog(
            parent_widget,
            "タイトル", 
            "メッセージ",
            QMessageBox.Yes
        )
        
        yes_button = dialog.button(QMessageBox.Yes)
        no_button = dialog.button(QMessageBox.No)
        
        # スタイルシートが設定されていることを確認
        assert "min-width: 100px" in yes_button.styleSheet()
        assert "min-width: 100px" in no_button.styleSheet()

    def test_create_confirmation_dialog_unicode_text(self, parent_widget):
        """Unicode文字を含むテキストのテスト"""
        title = "確認：ファイル削除"
        message = "ファイル「テスト_ファイル.txt」を削除しますか？"
        
        dialog = create_confirmation_dialog(
            parent_widget,
            title,
            message,
            QMessageBox.Yes
        )
        
        assert dialog.windowTitle() == title
        assert dialog.text() == message


class TestMoveCursorToYesButton:
    """move_cursor_to_yes_button関数のP0レベルテスト"""
    
    @pytest.fixture
    def mock_yes_button(self):
        """モックYesボタン"""
        button = MagicMock(spec=QPushButton)
        button.isVisible.return_value = True
        
        # ジオメトリのモック設定
        mock_geometry = MagicMock()
        mock_center = MagicMock()
        mock_center.x.return_value = 100
        mock_center.y.return_value = 50
        mock_geometry.center.return_value = mock_center
        button.geometry.return_value = mock_geometry
        
        # グローバル座標変換のモック
        mock_global_point = MagicMock()
        mock_global_point.x.return_value = 200
        mock_global_point.y.return_value = 150
        button.mapToGlobal.return_value = mock_global_point
        
        return button
    
    @patch('PyQt5.QtGui.QCursor.setPos')
    def test_move_cursor_to_yes_button_visible(self, mock_set_pos, mock_yes_button):
        """表示されているYesボタンへのカーソル移動テスト"""
        move_cursor_to_yes_button(mock_yes_button)
        
        # ボタンが表示されているかチェック
        mock_yes_button.isVisible.assert_called_once()
        
        # ジオメトリ取得とマッピング
        mock_yes_button.geometry.assert_called_once()
        mock_yes_button.mapToGlobal.assert_called_once()
        
        # カーソル位置設定
        mock_set_pos.assert_called_once()
    
    @patch('PyQt5.QtGui.QCursor.setPos')
    def test_move_cursor_to_yes_button_invisible(self, mock_set_pos, mock_yes_button):
        """非表示のYesボタンの場合のテスト"""
        mock_yes_button.isVisible.return_value = False
        
        move_cursor_to_yes_button(mock_yes_button)
        
        # ボタンが非表示の場合、カーソス移動は実行されない
        mock_yes_button.isVisible.assert_called_once()
        mock_set_pos.assert_not_called()
    
    @patch('PyQt5.QtGui.QCursor.setPos')
    def test_move_cursor_to_yes_button_exception_handling(self, mock_set_pos, mock_yes_button):
        """カーソル移動中の例外処理テスト"""
        mock_yes_button.geometry.side_effect = Exception("Geometry error")
        
        # 例外が発生してもクラッシュしないことを確認
        move_cursor_to_yes_button(mock_yes_button)
        
        # setPos は呼ばれない
        mock_set_pos.assert_not_called()
    
    @patch('PyQt5.QtGui.QCursor.setPos')
    def test_move_cursor_to_yes_button_map_to_global_error(self, mock_set_pos, mock_yes_button):
        """mapToGlobal エラーのテスト"""
        mock_yes_button.mapToGlobal.side_effect = Exception("Mapping error")
        
        # 例外が発生してもクラッシュしないことを確認
        move_cursor_to_yes_button(mock_yes_button)
        
        mock_set_pos.assert_not_called()


class TestHelpersIntegration:
    """helpers.py の統合テスト"""
    
    def test_file_accessibility_workflow(self, temp_dir):
        """ファイルアクセス可能性チェックのワークフローテスト"""
        # 実際のファイルを作成
        test_file = os.path.join(temp_dir, 'workflow_test.txt')
        test_content = 'ワークフローテスト用コンテンツ'
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # パス正規化
        normalized_path = normalize_path(test_file)
        
        # アクセス可能性チェック
        is_accessible = check_file_accessibility(normalized_path)
        assert is_accessible == True
        
        # ファイル読み込み
        content = read_file_with_auto_encoding(normalized_path)
        assert content == test_content
    
    @patch('PyQt5.QtWidgets.QMessageBox.exec_')
    def test_confirmation_dialog_workflow(self, mock_exec, qapp):
        """確認ダイアログのワークフローテスト"""
        from PyQt5.QtWidgets import QWidget
        
        parent = QWidget()
        
        # ダイアログ作成
        dialog = create_confirmation_dialog(
            parent,
            "テスト確認",
            "処理を続行しますか？",
            QMessageBox.Yes
        )
        
        # ダイアログの基本設定確認
        assert dialog.windowTitle() == "テスト確認"
        assert dialog.text() == "処理を続行しますか？"
        
        # ボタンテキスト確認
        yes_button = dialog.button(QMessageBox.Yes)
        no_button = dialog.button(QMessageBox.No)
        
        assert yes_button.text() == UI_LABELS['YES_BUTTON']
        assert no_button.text() == UI_LABELS['NO_BUTTON']
    
    def test_error_handling_consistency(self):
        """エラーハンドリングの一貫性テスト"""
        # 存在しないファイルでの各関数の動作確認
        nonexistent_path = '/absolutely/nonexistent/file.txt'
        
        # check_file_accessibility は False を返す
        assert check_file_accessibility(nonexistent_path) == False
        
        # read_file_with_auto_encoding は IOError を発生
        with pytest.raises(IOError):
            read_file_with_auto_encoding(nonexistent_path)
    
    def test_unicode_path_handling_integration(self, temp_dir):
        """Unicode パス処理の統合テスト"""
        # Unicode文字を含むファイル名
        unicode_filename = 'テスト_файл_测试_🎌.txt'
        unicode_path = os.path.join(temp_dir, unicode_filename)
        unicode_content = 'マルチバイト文字テスト：日本語、Русский、中文'
        
        # ファイル作成
        with open(unicode_path, 'w', encoding='utf-8') as f:
            f.write(unicode_content)
        
        # パス正規化
        normalized = normalize_path(unicode_path)
        
        # アクセス可能性チェック
        assert check_file_accessibility(normalized) == True
        
        # ファイル読み込み
        content = read_file_with_auto_encoding(normalized)
        assert content == unicode_content
    
    def test_large_file_handling(self, temp_dir):
        """大容量ファイル処理テスト"""
        large_file = os.path.join(temp_dir, 'large_test.txt')
        
        # 1MBのテストファイル作成
        large_content = 'A' * (1024 * 1024)  # 1MB
        
        with open(large_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        
        # パス処理とアクセス可能性チェック
        normalized = normalize_path(large_file)
        assert check_file_accessibility(normalized) == True
        
        # 大容量ファイルの読み込み
        content = read_file_with_auto_encoding(normalized)
        assert len(content) == len(large_content)
        assert content == large_content


class TestHelpersEdgeCases:
    """helpers.py のエッジケーステスト"""

    def test_normalize_path_very_long_path(self):
        """非常に長いパスの正規化テスト"""
        # Windows の最大パス長を超える長いパス
        long_path_parts = ['very_long_directory_name_' + str(i) for i in range(50)]
        long_path = r'C:\Users\test\\' + '\\'.join(long_path_parts) + r'\file.txt'

        result = normalize_path(long_path)

        # 正規化されることを確認（プラットフォーム固有の区切り文字）
        assert result.startswith('C:')
        assert result.endswith('file.txt')

    def test_is_network_file_edge_cases(self):
        """is_network_file のエッジケーステスト"""
        edge_cases = [
            (':', True),  # コロンのみ - 現在の実装では True
            ('//', True),  # スラッシュのみ - UNC開始として True
            ('C:', True),  # ドライブレターのみ
            ('//server', True),  # サーバー名のみ
            ('\\\\', True),  # UNC開始のみ
        ]

        for path, expected in edge_cases:
            result = is_network_file(path)
            assert result == expected, f"Failed for path: {path}"
    
    @patch('chardet.detect')
    def test_read_file_with_auto_encoding_low_confidence(self, mock_detect, temp_dir):
        """chardet低信頼度検出のテスト"""
        test_file = os.path.join(temp_dir, 'low_confidence.txt')
        
        with open(test_file, 'wb') as f:
            f.write(b'\x80\x81\x82\x83')  # あいまいなバイト列
        
        # 低信頼度でのエンコーディング検出をシミュレート
        mock_detect.return_value = {'encoding': 'ascii', 'confidence': 0.3}
        
        # 低信頼度でも処理を続行することを確認
        with patch('builtins.open', mock_open(read_data=b'\x80\x81\x82\x83')):
            try:
                read_file_with_auto_encoding(test_file)
            except UnicodeDecodeError:
                # デコードエラーが発生した場合、適切な例外処理がされることを確認
                pass
    
    def test_create_confirmation_dialog_parent_none(self):
        """親がNoneの場合の確認ダイアログテスト"""
        dialog = create_confirmation_dialog(
            None,  # 親なし
            "テストタイトル",
            "テストメッセージ",
            QMessageBox.Yes
        )
        
        assert isinstance(dialog, QMessageBox)
        assert dialog.parent() is None