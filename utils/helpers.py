import os
import re
import socket
from typing import Optional

import chardet
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QMessageBox

from utils.constants import (
    NETWORK_TIMEOUT,
    DNS_TEST_HOST,
    DNS_TEST_PORT,
    CURSOR_MOVE_DELAY,
    ERROR_MESSAGES,
    UI_LABELS
)


def normalize_path(file_path: str) -> str:
    """ファイルパスを正規化。

    Args:
        file_path: ファイルパス

    Returns:
        正規化されたパス
    """
    if not file_path:
        return ''

    if file_path.startswith('\\\\'):
        return file_path.replace('\\', '/')

    if len(file_path) >= 2 and file_path[1] == ':':
        return file_path.replace('\\', '/')

    normalized = os.path.normpath(file_path.replace('\\', '/'))
    return re.sub('/+', '/', normalized)


def is_network_file(file_path: str) -> bool:
    """ネットワークファイルか判定。

    Args:
        file_path: ファイルパス

    Returns:
        ネットワークファイルの場合True
    """
    if not file_path:
        return False

    if file_path.startswith('\\\\') or file_path.startswith('//'):
        return True

    if len(file_path) >= 2 and file_path[1] == ':':
        return True

    normalized_path = normalize_path(file_path)
    return normalized_path.startswith('//') or ':' in normalized_path[:2]


def check_file_accessibility(file_path: str, timeout: int = NETWORK_TIMEOUT) -> bool:
    """ファイルがアクセス可能か確認。

    Args:
        file_path: ファイルパス
        timeout: ネットワーク接続タイムアウト秒数

    Returns:
        アクセス可能な場合True
    """
    normalized_path = normalize_path(file_path)
    if is_network_file(normalized_path):
        try:
            with socket.create_connection((DNS_TEST_HOST, DNS_TEST_PORT), timeout=timeout):
                return os.path.exists(normalized_path)
        except (socket.error, OSError):
            return False
    return os.path.exists(normalized_path)


def read_file_with_auto_encoding(file_path: str) -> str:
    """自動エンコーディング検出でファイルを読み込む。

    Args:
        file_path: ファイルパス

    Returns:
        ファイルコンテンツ

    Raises:
        IOError: ファイル読み込み失敗
        ValueError: エンコーディング検出失敗
    """
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
    except IOError as e:
        raise IOError(f"ファイルの読み込みに失敗しました: {file_path}") from e

    if len(raw_data) == 0:
        return ""

    try:
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    except Exception as e:
        raise ValueError(f"{ERROR_MESSAGES['ENCODING_DETECTION_FAILED']}: {file_path}") from e

    if encoding is None:
        try:
            return raw_data.decode()
        except UnicodeDecodeError:
            try:
                return raw_data.decode('latin-1')
            except UnicodeDecodeError as e:
                raise ValueError(f"{ERROR_MESSAGES['ENCODING_DETECTION_FAILED']}: {file_path}") from e

    try:
        return raw_data.decode(encoding)
    except UnicodeDecodeError as e:
        fallback_encodings = ['utf-8', 'cp1252', 'latin-1']
        for fallback_encoding in fallback_encodings:
            if fallback_encoding != encoding:
                try:
                    return raw_data.decode(fallback_encoding)
                except UnicodeDecodeError:
                    continue

        raise ValueError(f"{ERROR_MESSAGES['FILE_DECODE_FAILED']}: {file_path}") from e


def create_confirmation_dialog(
    parent,
    title: str,
    message: str,
    default_button: QMessageBox.StandardButton
) -> QMessageBox:
    """確認ダイアログを作成。

    Args:
        parent: 親ウィジェット
        title: ダイアログタイトル
        message: メッセージテキスト
        default_button: デフォルトボタン

    Returns:
        QMessageBoxインスタンス
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

    button_style = """
    QPushButton {
        min-width: 100px;
        text-align: center;
    }
    """

    yes_button = msg_box.button(QMessageBox.Yes)
    if yes_button:
        yes_button.setText(UI_LABELS['YES_BUTTON'])
        yes_button.setStyleSheet(button_style)
    no_button = msg_box.button(QMessageBox.No)
    if no_button:
        no_button.setText(UI_LABELS['NO_BUTTON'])
        no_button.setStyleSheet(button_style)

    msg_box.setDefaultButton(default_button)

    timer = QTimer()
    timer.setSingleShot(True)
    if yes_button:
        timer.timeout.connect(lambda: move_cursor_to_yes_button(yes_button))
    timer.start(CURSOR_MOVE_DELAY)
    # Store timer reference to prevent garbage collection
    setattr(msg_box, '_cursor_timer', timer)

    return msg_box


def move_cursor_to_yes_button(yes_button) -> None:
    """Yesボタンへカーソルを移動。

    Args:
        yes_button: Yesボタンウィジェット
    """
    try:
        if yes_button.isVisible():
            button_rect = yes_button.geometry()
            button_center = button_rect.center()

            global_center = yes_button.mapToGlobal(button_center)

            QCursor.setPos(global_center)
    except Exception as e:
        print(f"マウスカーソル移動中にエラーが発生しました: {e}")
