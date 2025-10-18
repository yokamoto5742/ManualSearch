import re
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QPushButton

from utils.constants import SEARCH_TYPE_AND, SEARCH_TYPE_OR, UI_LABELS
from widgets.search_widget import SearchWidget


@pytest.mark.unit
@pytest.mark.gui
class TestSearchWidget:
    """SearchWidgetクラスの包括的なテスト"""

    @pytest.fixture
    def mock_config_manager(self):
        """ConfigManagerのモックを作成"""
        config_mock = MagicMock()
        config_mock.get_font_size.return_value = 14
        config_mock.get_directories.return_value = []
        config_mock.get_file_extensions.return_value = ['.pdf', '.txt', '.md']
        return config_mock

    @pytest.fixture
    def search_widget(self, qtbot, mock_config_manager):
        """SearchWidgetインスタンスを作成"""
        widget = SearchWidget(mock_config_manager)
        qtbot.addWidget(widget)
        return widget

    # ========== 初期化テスト ==========

    def test_init_creates_ui_components(self, search_widget):
        """初期化時にUI コンポーネントが正しく作成されることを検証"""
        assert search_widget.search_input is not None
        assert search_widget.search_type_combo is not None
        assert search_widget.config_manager is not None

    def test_init_sets_placeholder_text(self, search_widget):
        """検索入力フィールドにプレースホルダーテキストが設定されることを検証"""
        expected_placeholder = UI_LABELS['SEARCH_PLACEHOLDER']
        assert search_widget.search_input.placeholderText() == expected_placeholder

    def test_init_creates_search_type_combo_items(self, search_widget):
        """検索タイプコンボボックスに正しいアイテムが追加されることを検証"""
        combo = search_widget.search_type_combo
        assert combo.count() == 2
        assert combo.itemText(0) == UI_LABELS['AND_SEARCH_LABEL']
        assert combo.itemText(1) == UI_LABELS['OR_SEARCH_LABEL']

    def test_init_stores_config_manager(self, mock_config_manager):
        """ConfigManagerが正しく保存されることを検証"""
        widget = SearchWidget(mock_config_manager)
        assert widget.config_manager is mock_config_manager

    # ========== シグナル接続テスト ==========

    def test_search_button_emits_search_requested_signal(self, qtbot, search_widget):
        """検索ボタンクリック時にsearch_requestedシグナルが発行されることを検証"""
        with qtbot.waitSignal(search_widget.search_requested, timeout=1000):
            # 検索ボタンを見つけてクリック
            search_button = search_widget.findChild(QPushButton, '')
            assert search_button is not None
            search_button.click()

    def test_return_key_emits_search_requested_signal(self, qtbot, search_widget):
        """検索入力フィールドでEnterキー押下時にsearch_requestedシグナルが発行されることを検証"""
        with qtbot.waitSignal(search_widget.search_requested, timeout=1000):
            search_widget.search_input.setFocus()
            qtbot.keyPress(search_widget.search_input, Qt.Key_Return)

    def test_search_requested_signal_defined(self, search_widget):
        """search_requestedシグナルが定義されていることを検証"""
        assert hasattr(search_widget, 'search_requested')

    # ========== get_search_terms メソッドテスト ==========

    def test_get_search_terms_single_term(self, search_widget):
        """単一の検索語を正しく取得できることを検証"""
        search_widget.search_input.setText('Python')
        terms = search_widget.get_search_terms()
        assert terms == ['Python']

    def test_get_search_terms_multiple_terms_comma(self, search_widget):
        """カンマ区切りの複数検索語を正しく取得できることを検証"""
        search_widget.search_input.setText('Python,Java,C++')
        terms = search_widget.get_search_terms()
        assert terms == ['Python', 'Java', 'C++']

    def test_get_search_terms_multiple_terms_japanese_comma(self, search_widget):
        """全角カンマ区切りの複数検索語を正しく取得できることを検証"""
        search_widget.search_input.setText('Python、Java、C++')
        terms = search_widget.get_search_terms()
        assert terms == ['Python', 'Java', 'C++']

    def test_get_search_terms_mixed_separators(self, search_widget):
        """半角・全角カンマ混在時に正しく分割できることを検証"""
        search_widget.search_input.setText('Python,Java、C++')
        terms = search_widget.get_search_terms()
        assert terms == ['Python', 'Java', 'C++']

    def test_get_search_terms_strips_whitespace(self, search_widget):
        """検索語の前後の空白が正しく削除されることを検証"""
        search_widget.search_input.setText('  Python  ,  Java  ,  C++  ')
        terms = search_widget.get_search_terms()
        assert terms == ['Python', 'Java', 'C++']

    def test_get_search_terms_empty_input(self, search_widget):
        """空の入力に対して空リストを返すことを検証"""
        search_widget.search_input.setText('')
        terms = search_widget.get_search_terms()
        assert terms == []

    def test_get_search_terms_whitespace_only(self, search_widget):
        """空白のみの入力に対して空リストを返すことを検証"""
        search_widget.search_input.setText('   ')
        terms = search_widget.get_search_terms()
        assert terms == []

    def test_get_search_terms_ignores_empty_terms(self, search_widget):
        """連続した区切り文字や空の検索語を無視することを検証"""
        search_widget.search_input.setText('Python,,Java,,')
        terms = search_widget.get_search_terms()
        assert terms == ['Python', 'Java']

    def test_get_search_terms_with_japanese_text(self, search_widget):
        """日本語テキストを正しく処理できることを検証"""
        search_widget.search_input.setText('テスト、プログラミング、開発')
        terms = search_widget.get_search_terms()
        assert terms == ['テスト', 'プログラミング', '開発']

    def test_get_search_terms_with_special_characters(self, search_widget):
        """特殊文字を含む検索語を正しく処理できることを検証"""
        search_widget.search_input.setText('test@example.com,user#123')
        terms = search_widget.get_search_terms()
        assert terms == ['test@example.com', 'user#123']

    def test_get_search_terms_regex_error_handling(self, search_widget, capsys):
        """正規表現エラー時に空リストを返し、エラーメッセージを出力することを検証"""
        with patch('re.split', side_effect=re.error('Test regex error')):
            terms = search_widget.get_search_terms()
            assert terms == []
            captured = capsys.readouterr()
            assert '正規表現エラー' in captured.out

    def test_get_search_terms_attribute_error_handling(self, search_widget, capsys):
        """search_input未初期化時のAttributeError処理を検証"""
        # search_inputを一時的に削除
        original_input = search_widget.search_input
        delattr(search_widget, 'search_input')

        terms = search_widget.get_search_terms()
        assert terms == []
        captured = capsys.readouterr()
        assert '検索入力フィールドが正しく初期化されていません' in captured.out

        # 復元
        search_widget.search_input = original_input

    # ========== get_search_type メソッドテスト ==========

    def test_get_search_type_and_selected(self, search_widget):
        """AND検索が選択されている場合にSEARCH_TYPE_ANDを返すことを検証"""
        search_widget.search_type_combo.setCurrentIndex(0)  # AND検索
        search_type = search_widget.get_search_type()
        assert search_type == SEARCH_TYPE_AND

    def test_get_search_type_or_selected(self, search_widget):
        """OR検索が選択されている場合にSEARCH_TYPE_ORを返すことを検証"""
        search_widget.search_type_combo.setCurrentIndex(1)  # OR検索
        search_type = search_widget.get_search_type()
        assert search_type == SEARCH_TYPE_OR

    def test_get_search_type_default_is_and(self, search_widget):
        """デフォルトでAND検索が選択されることを検証"""
        # 初期状態でAND検索が選択されている
        search_type = search_widget.get_search_type()
        assert search_type == SEARCH_TYPE_AND

    def test_get_search_type_attribute_error_handling(self, search_widget, capsys):
        """search_type_combo未初期化時のAttributeError処理を検証"""
        # search_type_comboを一時的に削除
        original_combo = search_widget.search_type_combo
        delattr(search_widget, 'search_type_combo')

        search_type = search_widget.get_search_type()
        assert search_type == SEARCH_TYPE_AND  # デフォルト値
        captured = capsys.readouterr()
        assert '検索タイプコンボボックスが正しく初期化されていません' in captured.out

        # 復元
        search_widget.search_type_combo = original_combo

    def test_get_search_type_startswith_logic(self, search_widget):
        """startsWithロジックがAND判定に正しく機能することを検証"""
        # AND検索ラベルで始まる場合
        search_widget.search_type_combo.setCurrentIndex(0)
        assert search_widget.search_type_combo.currentText().startswith("AND")
        assert search_widget.get_search_type() == SEARCH_TYPE_AND

        # OR検索ラベルで始まる場合
        search_widget.search_type_combo.setCurrentIndex(1)
        assert not search_widget.search_type_combo.currentText().startswith("AND")
        assert search_widget.get_search_type() == SEARCH_TYPE_OR

    # ========== UI インタラクションテスト ==========

    def test_search_input_accepts_text_input(self, qtbot, search_widget):
        """検索入力フィールドがテキスト入力を受け付けることを検証"""
        search_widget.search_input.setFocus()
        qtbot.keyClicks(search_widget.search_input, 'test query')
        assert search_widget.search_input.text() == 'test query'

    def test_search_input_clear_functionality(self, search_widget):
        """検索入力フィールドのクリア機能を検証"""
        search_widget.search_input.setText('some text')
        search_widget.search_input.clear()
        assert search_widget.search_input.text() == ''

    def test_combo_box_selection_change(self, qtbot, search_widget):
        """コンボボックスの選択変更が正しく機能することを検証"""
        # 初期状態はAND検索
        assert search_widget.search_type_combo.currentIndex() == 0

        # OR検索に変更
        search_widget.search_type_combo.setCurrentIndex(1)
        assert search_widget.search_type_combo.currentIndex() == 1

        # AND検索に戻す
        search_widget.search_type_combo.setCurrentIndex(0)
        assert search_widget.search_type_combo.currentIndex() == 0

    def test_widget_visibility(self, search_widget):
        """ウィジェットが可視状態であることを検証"""
        search_widget.show()
        assert search_widget.isVisible()

    # ========== レイアウトテスト ==========

    def test_layout_exists(self, search_widget):
        """レイアウトが正しく設定されていることを検証"""
        layout = search_widget.layout()
        assert layout is not None
        assert layout.count() > 0

    def test_search_layout_has_input_and_button(self, search_widget):
        """検索レイアウトに入力フィールドとボタンが含まれることを検証"""
        # 検索入力フィールドが存在
        assert search_widget.search_input is not None

        # 検索ボタンが存在
        search_button = search_widget.findChild(QPushButton)
        assert search_button is not None
        assert search_button.text() == UI_LABELS['SEARCH_BUTTON']

    # ========== 統合テスト（複数機能の組み合わせ） ==========

    def test_complete_search_workflow(self, qtbot, search_widget):
        """完全な検索ワークフロー（入力→選択→実行）を検証"""
        # 検索語を入力
        search_widget.search_input.setText('Python,Java')

        # OR検索に変更
        search_widget.search_type_combo.setCurrentIndex(1)

        # 検索語とタイプを取得
        terms = search_widget.get_search_terms()
        search_type = search_widget.get_search_type()

        assert terms == ['Python', 'Java']
        assert search_type == SEARCH_TYPE_OR

        # シグナル発行の検証
        with qtbot.waitSignal(search_widget.search_requested, timeout=1000):
            qtbot.keyPress(search_widget.search_input, Qt.Key_Return)

    def test_multiple_searches_with_different_types(self, search_widget):
        """異なる検索タイプで複数回検索できることを検証"""
        # 最初の検索: AND検索
        search_widget.search_input.setText('term1,term2')
        search_widget.search_type_combo.setCurrentIndex(0)
        assert search_widget.get_search_terms() == ['term1', 'term2']
        assert search_widget.get_search_type() == SEARCH_TYPE_AND

        # 2回目の検索: OR検索
        search_widget.search_input.setText('term3,term4,term5')
        search_widget.search_type_combo.setCurrentIndex(1)
        assert search_widget.get_search_terms() == ['term3', 'term4', 'term5']
        assert search_widget.get_search_type() == SEARCH_TYPE_OR

        # 3回目の検索: AND検索に戻す
        search_widget.search_input.setText('final_term')
        search_widget.search_type_combo.setCurrentIndex(0)
        assert search_widget.get_search_terms() == ['final_term']
        assert search_widget.get_search_type() == SEARCH_TYPE_AND

    def test_empty_search_workflow(self, qtbot, search_widget):
        """空の検索語で検索を実行した場合の動作を検証"""
        search_widget.search_input.setText('')

        # シグナルは発行されるが、検索語は空
        with qtbot.waitSignal(search_widget.search_requested, timeout=1000):
            qtbot.keyPress(search_widget.search_input, Qt.Key_Return)

        terms = search_widget.get_search_terms()
        assert terms == []

    # ========== エッジケーステスト ==========

    def test_very_long_search_term(self, search_widget):
        """非常に長い検索語を正しく処理できることを検証"""
        long_term = 'a' * 1000
        search_widget.search_input.setText(long_term)
        terms = search_widget.get_search_terms()
        assert terms == [long_term]

    def test_many_search_terms(self, search_widget):
        """多数の検索語を正しく処理できることを検証"""
        many_terms = ','.join([f'term{i}' for i in range(100)])
        search_widget.search_input.setText(many_terms)
        terms = search_widget.get_search_terms()
        assert len(terms) == 100
        assert terms[0] == 'term0'
        assert terms[99] == 'term99'

    def test_search_terms_with_newlines(self, search_widget):
        """改行を含む検索語の処理を検証"""
        search_widget.search_input.setText('term1,term2\nterm3')
        terms = search_widget.get_search_terms()
        # 改行はそのまま保持される（セパレーターはカンマのみ）
        assert 'term2\nterm3' in terms

    def test_search_terms_with_tabs(self, search_widget):
        """タブを含む検索語の処理を検証"""
        search_widget.search_input.setText('term1,\tterm2\t')
        terms = search_widget.get_search_terms()
        assert terms == ['term1', 'term2']

    def test_unicode_search_terms(self, search_widget):
        """Unicode文字（絵文字など）を含む検索語を正しく処理できることを検証"""
        search_widget.search_input.setText('テスト😀,Python🐍,検索✨')
        terms = search_widget.get_search_terms()
        assert terms == ['テスト😀', 'Python🐍', '検索✨']

    # ========== 静的メソッドテスト ==========

    def test_create_search_type_combo_static_method(self):
        """_create_search_type_combo静的メソッドが正しいコンボボックスを作成することを検証"""
        combo = SearchWidget._create_search_type_combo()

        assert combo is not None
        assert combo.count() == 2
        assert combo.itemText(0) == UI_LABELS['AND_SEARCH_LABEL']
        assert combo.itemText(1) == UI_LABELS['OR_SEARCH_LABEL']

    # ========== メモリリークテスト ==========

    def test_widget_cleanup(self, qtbot, mock_config_manager):
        """ウィジェットが正しくクリーンアップされることを検証"""
        widget = SearchWidget(mock_config_manager)
        # qtbot.addWidgetを使わずに手動でクリーンアップをテスト
        widget.show()
        assert widget.isVisible()

        # ウィジェットを閉じる
        widget.close()
        assert not widget.isVisible()

        # 明示的にクリーンアップ
        widget.deleteLater()
        qtbot.wait(100)

        # ウィジェットが正常に作成・破棄されたことを確認
        # （deleteLater後はアクセスしない）

    # ========== シグナル/スロット接続の詳細テスト ==========

    def test_return_pressed_connection(self, qtbot, search_widget):
        """returnPressedシグナルとsearch_requestedシグナルの接続を検証"""
        signal_count = 0

        def on_search_requested():
            nonlocal signal_count
            signal_count += 1

        search_widget.search_requested.connect(on_search_requested)

        # Enterキーを押す
        search_widget.search_input.setFocus()
        qtbot.keyPress(search_widget.search_input, Qt.Key_Return)
        qtbot.wait(100)

        assert signal_count == 1

    def test_button_clicked_connection(self, qtbot, search_widget):
        """ボタンクリックとsearch_requestedシグナルの接続を検証"""
        signal_count = 0

        def on_search_requested():
            nonlocal signal_count
            signal_count += 1

        search_widget.search_requested.connect(on_search_requested)

        # ボタンをクリック
        search_button = search_widget.findChild(QPushButton)
        search_button.click()
        qtbot.wait(100)

        assert signal_count == 1

    def test_multiple_signal_emissions(self, qtbot, search_widget):
        """複数回のシグナル発行が正しく動作することを検証"""
        signal_count = 0

        def on_search_requested():
            nonlocal signal_count
            signal_count += 1

        search_widget.search_requested.connect(on_search_requested)

        # 複数回検索を実行
        for _ in range(5):
            search_widget.search_input.setFocus()
            qtbot.keyPress(search_widget.search_input, Qt.Key_Return)
            qtbot.wait(50)

        assert signal_count == 5
