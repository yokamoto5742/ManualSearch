import pytest
import socket
from utils import check_file_accessibility, read_file_with_auto_encoding
import pytest
from unittest.mock import patch, mock_open


@pytest.mark.parametrize("file_path, expected_result", [
    ('/home/user/file.txt', True),
    ('//server/share/file.txt', True),
    ('Z:/network_drive/file.txt', True),
    ('/nonexistent/file.txt', False),
])

def test_check_file_accessibility(file_path, expected_result):
    with patch('os.path.exists', return_value=expected_result):
        with patch('socket.create_connection') as mock_connection:
            mock_connection.return_value.__enter__.return_value = None
            assert check_file_accessibility(file_path) == expected_result

def test_check_file_accessibility_network_error():
    with patch('socket.create_connection', side_effect=socket.error):
        assert check_file_accessibility('//server/share/file.txt') == False


@pytest.mark.parametrize("file_content, encoding", [
    ("こんにちは", "utf-8"),
    ("Hello", "ascii"),
    ("Здравствуйте", "utf-8"),
])
def test_read_file_with_auto_encoding(file_content, encoding):
    # 文字列をバイト列にエンコード
    encoded_content = file_content.encode(encoding)

    # ファイルの読み込みをモック
    mock_file = mock_open(read_data=encoded_content)

    # chardet.detect の戻り値をモック
    mock_detect = {'encoding': encoding, 'confidence': 0.99}

    with patch('builtins.open', mock_file), \
            patch('chardet.detect', return_value=mock_detect):
        result = read_file_with_auto_encoding('test.txt')

    assert result == file_content


def test_unknown_encoding():
    with patch('builtins.open', mock_open(read_data=b'test data')):
        with patch('chardet.detect', return_value={'encoding': None}):
            with pytest.raises(ValueError, match="Unable to detect encoding for file: test.txt"):
                read_file_with_auto_encoding('test.txt')


def test_decoding_error():
    invalid_data = b'\xff\xfe\xfd'  # 無効なUTF-8シーケンス

    with patch('builtins.open', mock_open(read_data=invalid_data)):
        with patch('chardet.detect', return_value={'encoding': 'utf-8'}):
            with pytest.raises(ValueError, match="Unable to decode the file: test.txt"):
                read_file_with_auto_encoding('test.txt')


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_file_with_auto_encoding('non_existent_file.txt')
