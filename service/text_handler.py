import logging
import os
from typing import List, Optional

from PyQt5.QtWidgets import QWidget

from utils.constants import FILE_EXTENSION_MD, TEXT_VIEWER_DEFAULT_HEIGHT, TEXT_VIEWER_DEFAULT_WIDTH
from utils.helpers import read_file_with_auto_encoding
from widgets.text_viewer_widget import TextViewerWindow

logger = logging.getLogger(__name__)

# ウィンドウがGCで破棄されないよう参照を保持する
_active_viewers: List[TextViewerWindow] = []


def open_text_file(
    file_path: str,
    search_terms: List[str],
    html_font_size: int,
    position: int = 0,
    parent: Optional[QWidget] = None,
    width: int = TEXT_VIEWER_DEFAULT_WIDTH,
    height: int = TEXT_VIEWER_DEFAULT_HEIGHT,
) -> None:
    """テキストファイルをアプリ内の別ウィンドウでハイライト付きで開く

    Args:
        file_path: ファイルパス
        search_terms: 検索語リスト
        html_font_size: 表示フォントサイズ
        position: 検索ヒット行番号(1始まり、0でジャンプなし)
        parent: 親ウィジェット
        width: ウィンドウ幅
        height: ウィンドウ高さ

    Raises:
        Exception: ファイル処理エラー
    """
    try:
        content = read_file_with_auto_encoding(file_path)
        if content is None:
            content = ""

        is_markdown = os.path.splitext(file_path)[1].lower() == FILE_EXTENSION_MD

        viewer = TextViewerWindow(
            title=os.path.basename(file_path),
            content=content,
            search_terms=search_terms,
            font_size=html_font_size,
            is_markdown=is_markdown,
            position=position,
            width=width,
            height=height,
            file_path=file_path,
            parent=parent,
        )
        viewer.destroyed.connect(lambda: _remove_viewer(viewer))
        _active_viewers.append(viewer)

        viewer.show()
        viewer.raise_()
        viewer.activateWindow()

    except Exception as e:
        raise Exception(f"テキストファイルを開けませんでした: {str(e)}")


def _remove_viewer(viewer: TextViewerWindow) -> None:
    if viewer in _active_viewers:
        _active_viewers.remove(viewer)
