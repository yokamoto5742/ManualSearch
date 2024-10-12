import os
import re
import socket

def normalize_path(file_path):
    # バックスラッシュをフォワードスラッシュに変換し、パスを正規化
    normalized_path = os.path.normpath(file_path.replace('\\', '/'))
    # 連続するスラッシュを単一のスラッシュに置換
    normalized_path = re.sub('/+', '/', normalized_path)
    return normalized_path

def is_network_file(file_path):
    normalized_path = normalize_path(file_path)
    return normalized_path.startswith('//') or ':' in normalized_path[:2]

def check_file_accessibility(file_path, timeout=5):
    normalized_path = normalize_path(file_path)
    if is_network_file(normalized_path):
        try:
            with socket.create_connection(("8.8.8.8", 53), timeout=timeout):
                return os.path.exists(normalized_path)
        except (socket.error, OSError):
            return False
    return os.path.exists(normalized_path)

def read_file_with_auto_encoding(file_path):
    encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso2022_jp']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode the file: {file_path}")
