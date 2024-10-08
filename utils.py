import os
import re
import socket
from typing import Optional

def normalize_path(file_path: str) -> str:
    normalized_path = os.path.normpath(file_path.replace('\\', '/'))
    normalized_path = re.sub('/+', '/', normalized_path)
    return normalized_path

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
    encodings = ['utf-8', 'shift_jis', 'cp932', 'euc-jp', 'iso2022_jp']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                return file.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode the file: {file_path}")

def get_file_size(file_path: str) -> int:
    return os.path.getsize(file_path)

def get_file_extension(file_path: str) -> str:
    return os.path.splitext(file_path)[1].lower()

def is_valid_file_type(file_path: str, allowed_extensions: list) -> bool:
    return get_file_extension(file_path) in allowed_extensions

def create_directory_if_not_exists(directory_path: str) -> None:
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def get_file_creation_time(file_path: str) -> float:
    return os.path.getctime(file_path)

def get_file_modification_time(file_path: str) -> float:
    return os.path.getmtime(file_path)
