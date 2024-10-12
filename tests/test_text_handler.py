import pytest
import os
import tempfile
from unittest.mock import patch
from text_handler import open_text_file, highlight_text_file


@pytest.fixture
def sample_text_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write("This is a sample text file.\nIt contains some test content.")
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def sample_md_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md') as tmp:
        tmp.write("# Sample Markdown\n\nThis is a **bold** text.")
    yield tmp.name
    os.unlink(tmp.name)


def test_open_text_file(sample_text_file):
    with patch('webbrowser.open') as mock_open:
        open_text_file(sample_text_file, ['sample', 'test'], 16)
        mock_open.assert_called_once()
        called_url = mock_open.call_args[0][0]
        assert called_url.startswith('file://')
        assert called_url.endswith('.html')


def test_highlight_text_file_txt(sample_text_file):
    result = highlight_text_file(sample_text_file, ['sample', 'test'], 16)

    with open(result, 'r', encoding='utf-8') as f:
        content = f.read()

    assert '<span style="background-color: yellow;">sample</span>' in content
    assert '<span style="background-color: lightgreen;">test</span>' in content
    assert 'font-size: 16px;' in content

    os.unlink(result)


def test_highlight_text_file_md(sample_md_file):
    result = highlight_text_file(sample_md_file, ['Sample', 'bold'], 16)

    with open(result, 'r', encoding='utf-8') as f:
        content = f.read()

    assert '<h1><span style="background-color: yellow;">Sample</span> Markdown</h1>' in content
    assert '<strong><span style="background-color: lightgreen;">bold</span></strong>' in content
    assert 'font-size: 16px;' in content

    os.unlink(result)


@pytest.mark.parametrize("file_extension", ['.txt', '.md'])
def test_highlight_text_file_different_extensions(file_extension):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=file_extension) as tmp:
        tmp.write("Test content")

    result = highlight_text_file(tmp.name, ['Test'], 16)

    with open(result, 'r', encoding='utf-8') as f:
        content = f.read()

    if file_extension == '.txt':
        assert '<pre>' in content
    else:
        assert '<pre>' not in content

    os.unlink(tmp.name)
    os.unlink(result)


def test_open_text_file_exception():
    with pytest.raises(Exception) as exc_info:
        open_text_file('non_existent_file.txt', [], 16)
    assert "テキストファイルを開けませんでした" in str(exc_info.value)


@patch('text_handler.read_file_with_auto_encoding')
def test_highlight_text_file_encoding_error(mock_read_file):
    mock_read_file.side_effect = ValueError("エンコーディングエラー")

    with pytest.raises(ValueError) as exc_info:
        highlight_text_file('test.txt', [], 16)
    assert "ファイルの読み込みに失敗しました" in str(exc_info.value)
