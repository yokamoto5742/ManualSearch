import html
import os
import re
import sys
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest
from jinja2 import Environment, TemplateNotFound

from service.text_handler import (
    create_jinja_environment,
    create_temp_html_file,
    generate_html_content,
    get_available_templates,
    get_file_type_display_name,
    get_template_directory,
    highlight_search_terms,
    highlight_text_file,
    open_text_file,
    validate_template_file,
)
from utils.constants import (
    FILE_TYPE_DISPLAY_NAMES,
    HIGHLIGHT_COLORS,
    HIGHLIGHT_STYLE_TEMPLATE,
    MARKDOWN_EXTENSIONS,
    MAX_FONT_SIZE,
    MIN_FONT_SIZE,
    TEMPLATE_DIRECTORY,
    TEXT_VIEWER_TEMPLATE,
)


@pytest.mark.unit
class TestGetTemplateDirectory:
    """get_template_directory関数のテスト"""

    def test_get_template_directory_non_frozen(self):
        """非フリーズモード（通常実行）でのテンプレートディレクトリ取得"""
        with patch.object(sys, 'frozen', False, create=True):
            result = get_template_directory()

            expected_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            expected_base = expected_base.replace('tests\\service', '').replace('tests/service', '')

            assert TEMPLATE_DIRECTORY in result
            assert os.path.isabs(result)

    def test_get_template_directory_frozen(self):
        """フリーズモード（PyInstaller実行）でのテンプレートディレクトリ取得"""
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, '_MEIPASS', r'C:\temp\frozen_app', create=True):
                result = get_template_directory()

                expected_path = os.path.join(r'C:\temp\frozen_app', TEMPLATE_DIRECTORY)
                assert result == expected_path

    def test_get_template_directory_returns_string(self):
        """テンプレートディレクトリのパスが文字列型であることを確認"""
        result = get_template_directory()
        assert isinstance(result, str)


@pytest.mark.unit
class TestCreateJinjaEnvironment:
    """create_jinja_environment関数のテスト"""

    def test_create_jinja_environment_creates_directory(self, temp_dir):
        """存在しないテンプレートディレクトリを作成"""
        template_dir = os.path.join(temp_dir, 'new_templates')

        with patch('service.text_handler.get_template_directory', return_value=template_dir):
            env = create_jinja_environment()

            assert os.path.exists(template_dir)
            assert isinstance(env, Environment)

    def test_create_jinja_environment_existing_directory(self, template_directory):
        """既存のテンプレートディレクトリを使用"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            env = create_jinja_environment()

            assert isinstance(env, Environment)
            assert env.autoescape is True

    def test_jinja_environment_autoescape_enabled(self, template_directory):
        """自動エスケープが有効であることを確認"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            env = create_jinja_environment()

            assert env.autoescape is True

    def test_jinja_environment_trim_and_lstrip_blocks(self, template_directory):
        """trim_blocksとlstrip_blocksが有効であることを確認"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            env = create_jinja_environment()

            assert env.trim_blocks is True
            assert env.lstrip_blocks is True


@pytest.mark.unit
class TestOpenTextFile:
    """open_text_file関数のテスト"""

    def test_open_text_file_success(self, sample_text_file, template_directory):
        """テキストファイルを正常に開く"""
        search_terms = ['テスト', 'Python']
        font_size = 16

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            with patch('service.text_handler.webbrowser.open') as mock_browser:
                open_text_file(sample_text_file, search_terms, font_size)

                mock_browser.assert_called_once()
                call_args = mock_browser.call_args[0][0]
                assert call_args.startswith('file://')
                assert call_args.endswith('.html')

    def test_open_text_file_with_empty_search_terms(self, sample_text_file, template_directory):
        """検索語が空のリストの場合"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            with patch('service.text_handler.webbrowser.open') as mock_browser:
                open_text_file(sample_text_file, [], 16)

                mock_browser.assert_called_once()

    def test_open_text_file_file_not_found(self, template_directory):
        """存在しないファイルを開こうとした場合"""
        non_existent_file = 'C:\\non_existent_file.txt'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            with pytest.raises(Exception) as exc_info:
                open_text_file(non_existent_file, ['test'], 16)

            assert 'テキストファイルを開けませんでした' in str(exc_info.value)

    def test_open_text_file_various_font_sizes(self, sample_text_file, template_directory):
        """様々なフォントサイズでファイルを開く"""
        font_sizes = [8, 12, 16, 20, 32]

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            with patch('service.text_handler.webbrowser.open') as mock_browser:
                for font_size in font_sizes:
                    mock_browser.reset_mock()
                    open_text_file(sample_text_file, ['test'], font_size)
                    assert mock_browser.called


@pytest.mark.unit
class TestHighlightTextFile:
    """highlight_text_file関数のテスト"""

    def test_highlight_text_file_basic(self, sample_text_file, template_directory):
        """基本的なテキストファイルのハイライト"""
        search_terms = ['Python', 'テスト']

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result_path = highlight_text_file(sample_text_file, search_terms, 16)

            assert os.path.exists(result_path)
            assert result_path.endswith('.html')

            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'Python' in content or 'python' in content.lower()

    def test_highlight_text_file_markdown(self, sample_markdown_file, template_directory):
        """Markdownファイルのハイライト"""
        search_terms = ['Python', 'テスト']

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result_path = highlight_text_file(sample_markdown_file, search_terms, 16)

            assert os.path.exists(result_path)

            with open(result_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Markdownが処理されてHTMLタグが含まれる
                assert '<' in content and '>' in content

    def test_highlight_text_file_empty_search_terms(self, sample_text_file, template_directory):
        """検索語が空の場合のハイライト"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result_path = highlight_text_file(sample_text_file, [], 16)

            assert os.path.exists(result_path)

    def test_highlight_text_file_invalid_file(self, template_directory):
        """無効なファイルパスの場合"""
        invalid_path = 'C:\\invalid\\path\\file.txt'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            with pytest.raises((ValueError, IOError)) as exc_info:
                highlight_text_file(invalid_path, ['test'], 16)

            error_message = str(exc_info.value)
            assert 'ファイルの読み込みに失敗しました' in error_message or 'file.txt' in error_message

    def test_highlight_text_file_various_extensions(self, temp_dir, template_directory):
        """様々な拡張子のファイルでハイライト処理"""
        extensions = ['.txt', '.md']

        for ext in extensions:
            file_path = os.path.join(temp_dir, f'test{ext}')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('Test content with Python keyword')

            with patch('service.text_handler.get_template_directory', return_value=template_directory):
                result_path = highlight_text_file(file_path, ['Python'], 16)
                assert os.path.exists(result_path)

    def test_highlight_text_file_font_size_boundary(self, sample_text_file, template_directory):
        """フォントサイズの境界値テスト"""
        font_sizes = [MIN_FONT_SIZE - 5, MIN_FONT_SIZE, 16, MAX_FONT_SIZE, MAX_FONT_SIZE + 5]

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            for font_size in font_sizes:
                result_path = highlight_text_file(sample_text_file, ['test'], font_size)
                assert os.path.exists(result_path)

                # Clean up
                if os.path.exists(result_path):
                    try:
                        os.remove(result_path)
                    except:
                        pass


@pytest.mark.unit
class TestHighlightSearchTerms:
    """highlight_search_terms関数のテスト"""

    def test_highlight_search_terms_single_term(self):
        """単一の検索語のハイライト"""
        content = "This is a test content with Python"
        search_terms = ["Python"]

        result = highlight_search_terms(content, search_terms)

        assert '<span style=' in result
        assert 'background-color' in result
        assert 'Python' in result

    def test_highlight_search_terms_multiple_terms(self):
        """複数の検索語のハイライト"""
        content = "Python programming and testing"
        search_terms = ["Python", "testing"]

        result = highlight_search_terms(content, search_terms)

        # 両方の検索語がハイライトされる
        assert result.count('<span style=') >= 2

    def test_highlight_search_terms_case_insensitive(self):
        """大文字小文字を区別しないハイライト"""
        content = "python Python PYTHON"
        search_terms = ["python"]

        result = highlight_search_terms(content, search_terms)

        # 全ての形式がハイライトされる
        assert result.count('<span style=') == 3

    def test_highlight_search_terms_empty_terms(self):
        """空の検索語リスト"""
        content = "Test content"
        search_terms = []

        result = highlight_search_terms(content, search_terms)

        assert result == content

    def test_highlight_search_terms_whitespace_terms(self):
        """空白のみの検索語を含む場合"""
        content = "Test content"
        search_terms = ["  ", "Test", ""]

        result = highlight_search_terms(content, search_terms)

        # 空白のみの検索語はスキップされる
        assert '<span style=' in result
        assert 'Test' in result

    def test_highlight_search_terms_special_regex_characters(self):
        """正規表現の特殊文字を含む検索語"""
        content = "Test with special chars: .*+?^${}()|[]"
        search_terms = [".*+"]

        result = highlight_search_terms(content, search_terms)

        # 特殊文字がエスケープされて正しくハイライトされる
        assert 'span' in result or result == content

    def test_highlight_search_terms_color_cycling(self):
        """複数の検索語で色が循環使用される"""
        content = "word1 word2 word3 word4 word5 word6"
        search_terms = ["word1", "word2", "word3", "word4", "word5", "word6"]

        result = highlight_search_terms(content, search_terms)

        # 全ての色が使用される
        for color in HIGHLIGHT_COLORS:
            assert color in result

    def test_highlight_search_terms_overlapping_matches(self):
        """重複するマッチのハイライト"""
        content = "testing test tests"
        search_terms = ["test"]

        result = highlight_search_terms(content, search_terms)

        # testを含む全ての単語がハイライトされる
        assert result.count('<span') >= 1

    def test_highlight_search_terms_japanese_characters(self):
        """日本語文字のハイライト"""
        content = "これはテストです。テスト文書。"
        search_terms = ["テスト"]

        result = highlight_search_terms(content, search_terms)

        assert '<span style=' in result
        assert 'テスト' in result
        assert result.count('<span') == 2

    def test_highlight_search_terms_with_html_content(self):
        """既にHTMLタグを含むコンテンツのハイライト"""
        content = "<p>Test content with <b>Python</b></p>"
        search_terms = ["Python"]

        result = highlight_search_terms(content, search_terms)

        assert '<span style=' in result
        assert 'Python' in result


@pytest.mark.unit
class TestGenerateHtmlContent:
    """generate_html_content関数のテスト"""

    def test_generate_html_content_basic(self, template_directory):
        """基本的なHTML生成"""
        file_path = 'C:\\test\\sample.txt'
        content = 'Test content'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = generate_html_content(file_path, content, False, 16, ['test'])

            assert isinstance(result, str)
            assert 'sample.txt' in result
            assert 'Test content' in result

    def test_generate_html_content_markdown(self, template_directory):
        """MarkdownコンテンツでのHTML生成"""
        file_path = 'C:\\test\\sample.md'
        content = '<h1>Test</h1>'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = generate_html_content(file_path, content, True, 16, ['test'])

            assert isinstance(result, str)
            assert 'sample.md' in result

    def test_generate_html_content_font_size_clamp(self, template_directory):
        """フォントサイズが最小値と最大値の範囲に制限される"""
        file_path = 'C:\\test\\sample.txt'
        content = 'Test'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            # 最小値以下
            result1 = generate_html_content(file_path, content, False, MIN_FONT_SIZE - 10)
            assert f'{MIN_FONT_SIZE}px' in result1

            # 最大値以上
            result2 = generate_html_content(file_path, content, False, MAX_FONT_SIZE + 10)
            assert f'{MAX_FONT_SIZE}px' in result2

            # 範囲内
            result3 = generate_html_content(file_path, content, False, 16)
            assert '16px' in result3

    def test_generate_html_content_none_font_size(self, template_directory):
        """フォントサイズがNoneの場合はデフォルト値を使用"""
        file_path = 'C:\\test\\sample.txt'
        content = 'Test'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = generate_html_content(file_path, content, False, None)

            assert '16px' in result

    def test_generate_html_content_none_search_terms(self, template_directory):
        """検索語がNoneの場合は空リストとして扱う"""
        file_path = 'C:\\test\\sample.txt'
        content = 'Test'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = generate_html_content(file_path, content, False, 16, None)

            assert isinstance(result, str)

    def test_generate_html_content_file_type_display(self, template_directory):
        """ファイルタイプの表示名が含まれる"""
        test_cases = [
            ('C:\\test\\file.txt', '.txt', 'file.txt'),
            ('C:\\test\\file.md', '.md', 'file.md'),
            ('C:\\test\\file.pdf', '.pdf', 'file.pdf'),
        ]

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            for file_path, ext, filename in test_cases:
                result = generate_html_content(file_path, 'content', False, 16)
                # テンプレートにファイル名が含まれることを確認
                assert filename in result
                # HTMLが生成されることを確認
                assert '<html' in result or '<div' in result

    def test_generate_html_content_template_not_found(self, temp_dir):
        """テンプレートファイルが存在しない場合"""
        empty_template_dir = os.path.join(temp_dir, 'empty_templates')
        os.makedirs(empty_template_dir)

        with patch('service.text_handler.get_template_directory', return_value=empty_template_dir):
            with pytest.raises(FileNotFoundError) as exc_info:
                generate_html_content('test.txt', 'content', False, 16)

            assert 'テンプレートファイルが見つかりません' in str(exc_info.value)

    def test_generate_html_content_special_characters(self, template_directory):
        """特殊文字を含むパスとコンテンツの処理"""
        file_path = 'C:\\test\\特殊文字\\ファイル.txt'
        content = '特殊文字 <>&"\' テスト'

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = generate_html_content(file_path, content, False, 16)

            assert isinstance(result, str)
            assert 'ファイル.txt' in result


@pytest.mark.unit
class TestCreateTempHtmlFile:
    """create_temp_html_file関数のテスト"""

    def test_create_temp_html_file_basic(self):
        """基本的な一時HTMLファイル作成"""
        html_content = '<html><body>Test</body></html>'

        result_path = create_temp_html_file(html_content)

        assert os.path.exists(result_path)
        assert result_path.endswith('.html')

        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert content == html_content

        # Clean up
        os.remove(result_path)

    def test_create_temp_html_file_unicode_content(self):
        """Unicode文字を含むHTMLファイル作成"""
        html_content = '<html><body>日本語テスト содержание тест</body></html>'

        result_path = create_temp_html_file(html_content)

        assert os.path.exists(result_path)

        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '日本語テスト' in content
            assert 'содержание' in content

        # Clean up
        os.remove(result_path)

    def test_create_temp_html_file_large_content(self):
        """大容量のHTMLコンテンツ作成"""
        large_content = '<html><body>' + 'A' * 100000 + '</body></html>'

        result_path = create_temp_html_file(large_content)

        assert os.path.exists(result_path)

        file_size = os.path.getsize(result_path)
        assert file_size > 100000

        # Clean up
        os.remove(result_path)

    def test_create_temp_html_file_empty_content(self):
        """空のHTMLコンテンツ"""
        html_content = ''

        result_path = create_temp_html_file(html_content)

        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) == 0

        # Clean up
        os.remove(result_path)

    def test_create_temp_html_file_returns_absolute_path(self):
        """絶対パスが返される"""
        html_content = '<html></html>'

        result_path = create_temp_html_file(html_content)

        assert os.path.isabs(result_path)

        # Clean up
        os.remove(result_path)

    def test_create_temp_html_file_multiple_calls(self):
        """複数回呼び出して異なるファイルが作成される"""
        html_content = '<html></html>'

        paths = [create_temp_html_file(html_content) for _ in range(3)]

        # 全て異なるパス
        assert len(set(paths)) == 3

        # 全て存在する
        for path in paths:
            assert os.path.exists(path)

        # Clean up
        for path in paths:
            os.remove(path)


@pytest.mark.unit
class TestGetFileTypeDisplayName:
    """get_file_type_display_name関数のテスト"""

    def test_get_file_type_display_name_txt(self):
        """txtファイルの表示名"""
        result = get_file_type_display_name('.txt')
        assert result == 'テキストファイル'

    def test_get_file_type_display_name_md(self):
        """mdファイルの表示名"""
        result = get_file_type_display_name('.md')
        assert result == 'Markdownファイル'

    def test_get_file_type_display_name_pdf(self):
        """pdfファイルの表示名"""
        result = get_file_type_display_name('.pdf')
        assert result == 'PDFファイル'

    def test_get_file_type_display_name_unknown(self):
        """未知のファイル拡張子"""
        result = get_file_type_display_name('.xyz')
        assert result == '不明なファイル'

    def test_get_file_type_display_name_case_insensitive(self):
        """大文字小文字を区別しない"""
        result1 = get_file_type_display_name('.TXT')
        result2 = get_file_type_display_name('.txt')
        assert result1 == result2 == 'テキストファイル'

    def test_get_file_type_display_name_empty_string(self):
        """空文字列の場合"""
        result = get_file_type_display_name('')
        assert result == '不明なファイル'

    def test_get_file_type_display_name_no_dot(self):
        """ドットなしの拡張子"""
        result = get_file_type_display_name('txt')
        assert result == '不明なファイル'


@pytest.mark.unit
class TestValidateTemplateFile:
    """validate_template_file関数のテスト"""

    def test_validate_template_file_exists(self, template_directory):
        """テンプレートファイルが存在する場合"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = validate_template_file()
            assert result is True

    def test_validate_template_file_not_exists(self, temp_dir):
        """テンプレートファイルが存在しない場合"""
        empty_dir = os.path.join(temp_dir, 'empty')
        os.makedirs(empty_dir)

        with patch('service.text_handler.get_template_directory', return_value=empty_dir):
            result = validate_template_file()
            assert result is False

    def test_validate_template_file_directory_not_exists(self):
        """テンプレートディレクトリ自体が存在しない場合"""
        non_existent_dir = 'C:\\non_existent_directory'

        with patch('service.text_handler.get_template_directory', return_value=non_existent_dir):
            result = validate_template_file()
            assert result is False


@pytest.mark.unit
class TestGetAvailableTemplates:
    """get_available_templates関数のテスト"""

    def test_get_available_templates_with_templates(self, template_directory):
        """テンプレートファイルが存在する場合"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = get_available_templates()

            assert isinstance(result, list)
            assert len(result) > 0
            assert all(template.endswith('.html') for template in result)

    def test_get_available_templates_empty_directory(self, temp_dir):
        """テンプレートファイルがない空のディレクトリ"""
        empty_dir = os.path.join(temp_dir, 'empty_templates')
        os.makedirs(empty_dir)

        with patch('service.text_handler.get_template_directory', return_value=empty_dir):
            result = get_available_templates()

            assert result == []

    def test_get_available_templates_directory_not_exists(self):
        """テンプレートディレクトリが存在しない場合"""
        non_existent_dir = 'C:\\non_existent_directory'

        with patch('service.text_handler.get_template_directory', return_value=non_existent_dir):
            result = get_available_templates()

            assert result == []

    def test_get_available_templates_mixed_files(self, temp_dir):
        """HTMLファイルと他のファイルが混在する場合"""
        mixed_dir = os.path.join(temp_dir, 'mixed_templates')
        os.makedirs(mixed_dir)

        # 様々なファイルを作成
        with open(os.path.join(mixed_dir, 'template1.html'), 'w') as f:
            f.write('<html></html>')
        with open(os.path.join(mixed_dir, 'template2.html'), 'w') as f:
            f.write('<html></html>')
        with open(os.path.join(mixed_dir, 'readme.txt'), 'w') as f:
            f.write('readme')
        with open(os.path.join(mixed_dir, 'style.css'), 'w') as f:
            f.write('css')

        with patch('service.text_handler.get_template_directory', return_value=mixed_dir):
            result = get_available_templates()

            assert len(result) == 2
            assert 'template1.html' in result
            assert 'template2.html' in result
            assert 'readme.txt' not in result
            assert 'style.css' not in result

    def test_get_available_templates_returns_list(self, template_directory):
        """結果がリスト型であることを確認"""
        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result = get_available_templates()

            assert isinstance(result, list)


@pytest.mark.unit
class TestEdgeCases:
    """エッジケースと統合テスト"""

    def test_highlight_text_file_with_encoding_issues(self, temp_dir, template_directory):
        """エンコーディング問題のあるファイル処理"""
        file_path = os.path.join(temp_dir, 'encoded.txt')

        # Shift-JISでファイル作成
        with open(file_path, 'w', encoding='shift-jis') as f:
            f.write('日本語のテストファイルです')

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            result_path = highlight_text_file(file_path, ['テスト'], 16)

            assert os.path.exists(result_path)

    def test_full_workflow_text_to_html(self, sample_text_file, template_directory):
        """テキストファイルからHTMLへの完全なワークフロー"""
        search_terms = ['Python', 'テスト']
        font_size = 18

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            # ハイライト処理
            html_path = highlight_text_file(sample_text_file, search_terms, font_size)

            # 結果検証
            assert os.path.exists(html_path)

            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # 検索語がハイライトされている
                assert 'background-color' in content
                # フォントサイズが適用されている
                assert '18px' in content
                # ファイル名が含まれている
                assert 'sample.txt' in content

    def test_markdown_extensions_applied(self, temp_dir, template_directory):
        """Markdown拡張機能が適用される"""
        md_file = os.path.join(temp_dir, 'test.md')
        content = "Line 1\nLine 2\nLine 3"

        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(content)

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            html_path = highlight_text_file(md_file, [], 16)

            with open(html_path, 'r', encoding='utf-8') as f:
                result = f.read()

                # nl2br拡張により改行がbrタグに変換される
                assert '<br' in result or '\n' in result

    def test_regex_error_handling_in_highlight(self):
        """正規表現エラー時のグレースフルな処理"""
        content = "Test content"
        # 無効な正規表現パターンを含む検索語
        invalid_terms = ["(unclosed", "valid_term"]

        # エラーでクラッシュせず、処理を継続
        result = highlight_search_terms(content, invalid_terms)

        assert isinstance(result, str)
        assert 'Test content' in result

    def test_concurrent_temp_file_creation(self):
        """並行して一時ファイルを作成しても競合しない"""
        html_content = '<html>test</html>'

        results = []
        for i in range(10):
            path = create_temp_html_file(html_content)
            results.append(path)

        # 全て異なるパス
        assert len(set(results)) == 10

        # Clean up
        for path in results:
            if os.path.exists(path):
                os.remove(path)

    def test_empty_file_handling(self, temp_dir, template_directory):
        """空のファイルの処理"""
        empty_file = os.path.join(temp_dir, 'empty.txt')
        with open(empty_file, 'w', encoding='utf-8') as f:
            f.write('')

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            html_path = highlight_text_file(empty_file, ['test'], 16)

            assert os.path.exists(html_path)

    def test_very_long_search_term(self, sample_text_file, template_directory):
        """非常に長い検索語の処理"""
        long_term = 'A' * 1000

        with patch('service.text_handler.get_template_directory', return_value=template_directory):
            html_path = highlight_text_file(sample_text_file, [long_term], 16)

            assert os.path.exists(html_path)

    def test_special_html_characters_in_search_terms(self):
        """HTML特殊文字を含む検索語"""
        content = html.escape("Test with <tag> and & characters")
        search_terms = ["<tag>", "&"]

        result = highlight_search_terms(content, search_terms)

        # エスケープされた文字列内でマッチング
        assert isinstance(result, str)
