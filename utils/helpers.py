import os
import re
import socket
from typing import Optional

import chardet
from PyQt5.QtWidgets import QMessageBox


def normalize_path(file_path: str) -> str:
    normalized_path = os.path.normpath(file_path.replace('\\', '/'))
    return re.sub('/+', '/', normalized_path)


def is_network_file(file_path: str) -> bool:
    normalized_path = normalize_path(file_path)
    return normalized_path.startswith('//') or ':' in normalized_path[:2]


def check_file_accessibility(file_path: str, timeout: int = 5) -> bool:
    normalized_path = normalize_path(file_path)
    if is_network_file(normalized_path):
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=timeout):
                return os.path.exists(normalized_path)
        except (socket.error, OSError):
            return False
    return os.path.exists(normalized_path)


def read_file_with_auto_encoding(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
    except IOError as e:
        raise IOError(f"ファイルの読み込みに失敗しました: {file_path}") from e

    try:
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    except Exception as e:
        raise ValueError(f"エンコーディングの検出に失敗しました: {file_path}") from e

    if encoding is None:
        raise ValueError(f"エンコーディングを検出できませんでした: {file_path}")

    try:
        return raw_data.decode(encoding)
    except UnicodeDecodeError as e:
        raise ValueError(f"ファイルのデコードに失敗しました: {file_path}") from e


def create_confirmation_dialog(parent, title: str, message: str,
                               default_button: QMessageBox.StandardButton) -> QMessageBox:
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
    yes_button.setText('はい')
    yes_button.setStyleSheet(button_style)
    no_button = msg_box.button(QMessageBox.No)
    no_button.setText('いいえ')
    no_button.setStyleSheet(button_style)

    msg_box.setDefaultButton(default_button)
    return msg_box