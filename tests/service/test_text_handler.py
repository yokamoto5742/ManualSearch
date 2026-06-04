import os

import pytest
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

from service.text_handler import _active_viewers, open_text_file
from utils.constants import HIGHLIGHT_COLORS, MAX_FONT_SIZE, MIN_FONT_SIZE
from widgets.text_viewer_widget import TextViewerWindow


def _close_and_flush(viewers):
    """ビューアを閉じ、WA_DeleteOnCloseによる遅延削除を確実に処理する

    processEvents()はDeferredDeleteを配送しないため、明示的に送出しないと
    後続テストで解放済みオブジェクトにアクセスしてクラッシュする。
    """
    for viewer in viewers:
        viewer.close()
    QApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    QApplication.processEvents()


@pytest.fixture(autouse=True)
def cleanup_viewers(qapp):
    """各テスト後にopen_text_fileが生成したビューアを閉じる"""
    yield
    _close_and_flush(list(_active_viewers))
    _active_viewers.clear()


@pytest.fixture
def make_viewer(qapp):
    """テスト用にTextViewerWindowを生成し、終了時に確実に閉じる

    WA_DeleteOnCloseとqtbot.addWidgetの併用による二重解放を避けるため、
    qtbotを使わず自前でcloseする。
    """
    created = []

    def _make(*args, **kwargs):
        viewer = TextViewerWindow(*args, **kwargs)
        created.append(viewer)
        return viewer

    yield _make

    _close_and_flush(created)


@pytest.mark.unit
class TestOpenTextFile:
    """open_text_file関数のテスト"""

    def test_open_text_file_success(self, sample_text_file):
        """テキストファイルを正常に開く"""
        open_text_file(sample_text_file, ['テスト', 'Python'], 16)

        assert len(_active_viewers) == 1
        viewer = _active_viewers[0]
        assert viewer.isVisible()
        assert viewer.windowTitle() == os.path.basename(sample_text_file)

    def test_open_text_file_empty_search_terms(self, sample_text_file):
        """検索語が空でも開ける"""
        open_text_file(sample_text_file, [], 16)

        assert len(_active_viewers) == 1

    def test_open_text_file_markdown(self, sample_markdown_file):
        """Markdownファイルを開く"""
        open_text_file(sample_markdown_file, ['Python'], 16)

        assert len(_active_viewers) == 1

    def test_open_text_file_not_found(self):
        """存在しないファイルの場合は例外"""
        with pytest.raises(Exception) as exc_info:
            open_text_file('C:\\non_existent_file.txt', ['test'], 16)

        assert 'テキストファイルを開けませんでした' in str(exc_info.value)

    def test_open_text_file_with_position(self, sample_text_file):
        """行番号指定で開く"""
        open_text_file(sample_text_file, ['test'], 16, position=2)

        assert len(_active_viewers) == 1


@pytest.mark.unit
class TestSearchHighlighter:
    """SearchHighlighterのテスト"""

    def test_rules_created_for_each_term(self, make_viewer):
        """検索語ごとにハイライトルールが作成される"""
        viewer = make_viewer('t', 'Python testing', ['Python', 'testing'], 16)

        assert len(viewer.highlighter.rules) == 2

    def test_empty_terms_skipped(self, make_viewer):
        """空白のみの検索語はスキップされる"""
        viewer = make_viewer('t', 'content', ['  ', 'Test', ''], 16)

        assert len(viewer.highlighter.rules) == 1

    def test_color_cycling(self, make_viewer):
        """色は循環して割り当てられる"""
        terms = [f'word{i}' for i in range(len(HIGHLIGHT_COLORS) + 1)]
        viewer = make_viewer('t', ' '.join(terms), terms, 16)

        first_color = viewer.highlighter.rules[0][1].background().color()
        cycled_color = viewer.highlighter.rules[len(HIGHLIGHT_COLORS)][1].background().color()
        assert first_color == QColor(HIGHLIGHT_COLORS[0])
        assert cycled_color == QColor(HIGHLIGHT_COLORS[0])


@pytest.mark.unit
class TestTextViewerWindow:
    """TextViewerWindowのテスト"""

    def test_plaintext_content_set(self, make_viewer):
        """プレーンテキストが表示される"""
        viewer = make_viewer('title', 'hello world', [], 16, is_markdown=False)

        assert 'hello world' in viewer.text_browser.toPlainText()

    def test_markdown_content_set(self, make_viewer):
        """Markdownが描画される"""
        viewer = make_viewer('title', '# Heading', [], 16, is_markdown=True)

        assert 'Heading' in viewer.text_browser.toPlainText()

    def test_font_size_clamped_min(self, make_viewer):
        """フォントサイズが最小値にクランプされる"""
        viewer = make_viewer('t', 'x', [], MIN_FONT_SIZE - 5)

        assert viewer.text_browser.font().pointSize() == MIN_FONT_SIZE

    def test_font_size_clamped_max(self, make_viewer):
        """フォントサイズが最大値にクランプされる"""
        viewer = make_viewer('t', 'x', [], MAX_FONT_SIZE + 5)

        assert viewer.text_browser.font().pointSize() == MAX_FONT_SIZE

    def test_font_size_within_range(self, make_viewer):
        """範囲内のフォントサイズはそのまま"""
        viewer = make_viewer('t', 'x', [], 16)

        assert viewer.text_browser.font().pointSize() == 16

    def test_zoom_in_increases_font(self, make_viewer):
        """文字を大きくするとフォントが拡大"""
        viewer = make_viewer('t', 'x', [], 16)
        before = viewer.text_browser.font().pointSize()

        viewer.zoom_in()

        assert viewer.text_browser.font().pointSize() > before

    def test_zoom_out_decreases_font(self, make_viewer):
        """文字を小さくするとフォントが縮小"""
        viewer = make_viewer('t', 'x', [], 16)
        before = viewer.text_browser.font().pointSize()

        viewer.zoom_out()

        assert viewer.text_browser.font().pointSize() < before

    def test_scroll_to_line(self, make_viewer):
        """行ジャンプでカーソルが該当行に移動"""
        content = "line1\nline2\nline3\nline4"
        viewer = make_viewer('t', content, [], 16, position=3)

        # カーソルが3行目(0始まりで2)にあることを確認
        assert viewer.text_browser.textCursor().blockNumber() == 2

    def test_no_highlighter_when_no_terms(self, make_viewer):
        """検索語がない場合ハイライタは生成されない"""
        viewer = make_viewer('t', 'content', [], 16)

        assert not hasattr(viewer, 'highlighter')
