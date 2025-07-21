import configparser
import os
import sys
from typing import List

from constants import (
    CONFIG_FILENAME,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_X,
    DEFAULT_WINDOW_Y,
    DEFAULT_FONT_SIZE,
    DEFAULT_HTML_FONT_SIZE,
    DEFAULT_CONTEXT_LENGTH,
    DEFAULT_PDF_TIMEOUT,
    DEFAULT_MAX_TEMP_FILES,
    DEFAULT_ACROBAT_PATH,
    DEFAULT_INDEX_FILE,
    DEFAULT_USE_INDEX_SEARCH,
    SUPPORTED_FILE_EXTENSIONS,
    MIN_FONT_SIZE,
    MAX_FONT_SIZE,
    MIN_WINDOW_WIDTH,
    MAX_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MAX_WINDOW_HEIGHT,
    MIN_PDF_TIMEOUT,
    MAX_PDF_TIMEOUT,
    MIN_MAX_TEMP_FILES,
    MAX_MAX_TEMP_FILES,
    CONFIG_SECTIONS,
    CONFIG_KEYS
)
from utils.helpers import read_file_with_auto_encoding


def get_config_path() -> str:
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, CONFIG_FILENAME)


CONFIG_PATH = get_config_path()


class ConfigManager:
    def __init__(self, config_file: str = CONFIG_PATH):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self) -> None:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding='utf-8') as configfile:
                    self.config.read_file(configfile)
            except UnicodeDecodeError:
                content = read_file_with_auto_encoding(self.config_file)
                self.config.read_string(content)

    def save_config(self) -> None:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)  # type: ignore
        except IOError as e:
            print(f"Error saving config: {e}")

    def get_file_extensions(self) -> List[str]:
        extensions = self.config.get(
            CONFIG_SECTIONS['FILE_TYPES'],
            CONFIG_KEYS['EXTENSIONS'],
            fallback=','.join(SUPPORTED_FILE_EXTENSIONS)
        )
        return [ext.strip() for ext in extensions.split(',') if ext.strip()]

    def get_window_width(self) -> int:
        """ウィンドウ幅を個別に取得"""
        width = self.config.getint(
            CONFIG_SECTIONS['WINDOW_SETTINGS'],
            CONFIG_KEYS['WINDOW_WIDTH'],
            fallback=DEFAULT_WINDOW_WIDTH
        )
        return max(MIN_WINDOW_WIDTH, min(MAX_WINDOW_WIDTH, width))

    def get_window_height(self) -> int:
        """ウィンドウ高さを個別に取得"""
        height = self.config.getint(
            CONFIG_SECTIONS['WINDOW_SETTINGS'],
            CONFIG_KEYS['WINDOW_HEIGHT'],
            fallback=DEFAULT_WINDOW_HEIGHT
        )
        return max(MIN_WINDOW_HEIGHT, min(MAX_WINDOW_HEIGHT, height))

    def get_window_x(self) -> int:
        """ウィンドウX座標を個別に取得"""
        return self.config.getint(
            CONFIG_SECTIONS['WINDOW_SETTINGS'],
            CONFIG_KEYS['WINDOW_X'],
            fallback=DEFAULT_WINDOW_X
        )

    def get_window_y(self) -> int:
        """ウィンドウY座標を個別に取得"""
        return self.config.getint(
            CONFIG_SECTIONS['WINDOW_SETTINGS'],
            CONFIG_KEYS['WINDOW_Y'],
            fallback=DEFAULT_WINDOW_Y
        )

    def get_window_size_and_position(self) -> List[int]:
        """ウィンドウサイズと位置を取得"""
        x = self.get_window_x()
        y = self.get_window_y()
        width = self.get_window_width()
        height = self.get_window_height()
        return [x, y, width, height]

    def get_font_size(self) -> int:
        size = self.config.getint(
            CONFIG_SECTIONS['WINDOW_SETTINGS'],
            CONFIG_KEYS['FONT_SIZE'],
            fallback=DEFAULT_FONT_SIZE
        )
        return max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))  # 範囲でクランプ

    def get_acrobat_path(self) -> str:
        return self.config.get(
            CONFIG_SECTIONS['PATHS'],
            CONFIG_KEYS['ACROBAT_PATH'],
            fallback=DEFAULT_ACROBAT_PATH
        )

    def set_file_extensions(self, extensions: List[str]) -> None:
        if CONFIG_SECTIONS['FILE_TYPES'] not in self.config:
            self.config[CONFIG_SECTIONS['FILE_TYPES']] = {}
        self.config[CONFIG_SECTIONS['FILE_TYPES']][CONFIG_KEYS['EXTENSIONS']] = ','.join(extensions)
        self.save_config()

    def set_window_size_and_position(self, x: int, y: int, width: int, height: int) -> None:
        """ウィンドウサイズと位置を個別に設定"""
        if CONFIG_SECTIONS['WINDOW_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']] = {}

        # 範囲チェック
        width = max(MIN_WINDOW_WIDTH, min(MAX_WINDOW_WIDTH, width))
        height = max(MIN_WINDOW_HEIGHT, min(MAX_WINDOW_HEIGHT, height))

        self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']][CONFIG_KEYS['WINDOW_X']] = str(x)
        self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']][CONFIG_KEYS['WINDOW_Y']] = str(y)
        self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']][CONFIG_KEYS['WINDOW_WIDTH']] = str(width)
        self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']][CONFIG_KEYS['WINDOW_HEIGHT']] = str(height)
        self.save_config()

    def set_window_width(self, width: int) -> None:
        """ウィンドウ幅を個別に設定"""
        if not MIN_WINDOW_WIDTH <= width <= MAX_WINDOW_WIDTH:
            raise ValueError(f"ウィンドウ幅は{MIN_WINDOW_WIDTH}-{MAX_WINDOW_WIDTH}の範囲で指定してください: {width}")

        if CONFIG_SECTIONS['WINDOW_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']][CONFIG_KEYS['WINDOW_WIDTH']] = str(width)
        self.save_config()

    def set_window_height(self, height: int) -> None:
        """ウィンドウ高さを個別に設定"""
        if not MIN_WINDOW_HEIGHT <= height <= MAX_WINDOW_HEIGHT:
            raise ValueError(
                f"ウィンドウ高さは{MIN_WINDOW_HEIGHT}-{MAX_WINDOW_HEIGHT}の範囲で指定してください: {height}")

        if CONFIG_SECTIONS['WINDOW_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']][CONFIG_KEYS['WINDOW_HEIGHT']] = str(height)
        self.save_config()

    def set_font_size(self, size: int) -> None:
        if not MIN_FONT_SIZE <= size <= MAX_FONT_SIZE:
            raise ValueError(f"フォントサイズは{MIN_FONT_SIZE}-{MAX_FONT_SIZE}の範囲で指定してください: {size}")

        if CONFIG_SECTIONS['WINDOW_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['WINDOW_SETTINGS']][CONFIG_KEYS['FONT_SIZE']] = str(size)
        self.save_config()

    def set_acrobat_path(self, path: str) -> None:
        if CONFIG_SECTIONS['PATHS'] not in self.config:
            self.config[CONFIG_SECTIONS['PATHS']] = {}
        self.config[CONFIG_SECTIONS['PATHS']][CONFIG_KEYS['ACROBAT_PATH']] = path
        self.save_config()

    def get_directories(self) -> List[str]:
        directories = self.config.get(CONFIG_SECTIONS['DIRECTORIES'], CONFIG_KEYS['DIRECTORY_LIST'], fallback='')
        return [dir.strip() for dir in directories.split(',') if dir.strip()]

    def set_directories(self, directories: List[str]) -> None:
        if CONFIG_SECTIONS['DIRECTORIES'] not in self.config:
            self.config[CONFIG_SECTIONS['DIRECTORIES']] = {}
        self.config[CONFIG_SECTIONS['DIRECTORIES']][CONFIG_KEYS['DIRECTORY_LIST']] = ','.join(directories)
        self.save_config()

    def get_last_directory(self) -> str:
        return self.config.get(CONFIG_SECTIONS['DIRECTORIES'], CONFIG_KEYS['LAST_DIRECTORY'], fallback='')

    def set_last_directory(self, directory: str) -> None:
        if CONFIG_SECTIONS['DIRECTORIES'] not in self.config:
            self.config[CONFIG_SECTIONS['DIRECTORIES']] = {}
        self.config[CONFIG_SECTIONS['DIRECTORIES']][CONFIG_KEYS['LAST_DIRECTORY']] = directory
        self.save_config()

    def get_context_length(self) -> int:
        return self.config.getint(CONFIG_SECTIONS['SEARCH_SETTINGS'], CONFIG_KEYS['CONTEXT_LENGTH'],
                                  fallback=DEFAULT_CONTEXT_LENGTH)

    def set_context_length(self, length: int) -> None:
        if CONFIG_SECTIONS['SEARCH_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['SEARCH_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['SEARCH_SETTINGS']][CONFIG_KEYS['CONTEXT_LENGTH']] = str(length)
        self.save_config()

    def get_filename_font_size(self) -> int:
        return self.config.getint(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['FILENAME_FONT_SIZE'],
                                  fallback=DEFAULT_FONT_SIZE)

    def set_filename_font_size(self, size: int) -> None:
        if CONFIG_SECTIONS['UI_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['UI_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['UI_SETTINGS']][CONFIG_KEYS['FILENAME_FONT_SIZE']] = str(size)
        self.save_config()

    def get_result_detail_font_size(self) -> int:
        return self.config.getint(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['RESULT_DETAIL_FONT_SIZE'],
                                  fallback=DEFAULT_FONT_SIZE)

    def set_result_detail_font_size(self, size: int) -> None:
        if CONFIG_SECTIONS['UI_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['UI_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['UI_SETTINGS']][CONFIG_KEYS['RESULT_DETAIL_FONT_SIZE']] = str(size)
        self.save_config()

    def get_html_font_size(self) -> int:
        return self.config.getint(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['HTML_FONT_SIZE'],
                                  fallback=DEFAULT_HTML_FONT_SIZE)

    def set_html_font_size(self, size: int) -> None:
        if CONFIG_SECTIONS['UI_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['UI_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['UI_SETTINGS']][CONFIG_KEYS['HTML_FONT_SIZE']] = str(size)
        self.save_config()

    def get_pdf_timeout(self) -> int:
        return self.config.getint(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['TIMEOUT'], fallback=DEFAULT_PDF_TIMEOUT)

    def set_pdf_timeout(self, timeout: int) -> None:
        if not MIN_PDF_TIMEOUT <= timeout <= MAX_PDF_TIMEOUT:
            raise ValueError(f"タイムアウトは{MIN_PDF_TIMEOUT}-{MAX_PDF_TIMEOUT}秒の範囲で指定してください: {timeout}")

        if CONFIG_SECTIONS['PDF_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['PDF_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['PDF_SETTINGS']][CONFIG_KEYS['TIMEOUT']] = str(timeout)
        self.save_config()

    def get_cleanup_temp_files(self) -> bool:
        return self.config.getboolean(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['CLEANUP_TEMP_FILES'], fallback=True)

    def set_cleanup_temp_files(self, cleanup: bool) -> None:
        if CONFIG_SECTIONS['PDF_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['PDF_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['PDF_SETTINGS']][CONFIG_KEYS['CLEANUP_TEMP_FILES']] = str(cleanup)
        self.save_config()

    def get_max_temp_files(self) -> int:
        return self.config.getint(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['MAX_TEMP_FILES'],
                                  fallback=DEFAULT_MAX_TEMP_FILES)

    def set_max_temp_files(self, max_files: int) -> None:
        if not MIN_MAX_TEMP_FILES <= max_files <= MAX_MAX_TEMP_FILES:
            raise ValueError(
                f"最大ファイル数は{MIN_MAX_TEMP_FILES}-{MAX_MAX_TEMP_FILES}の範囲で指定してください: {max_files}")

        if CONFIG_SECTIONS['PDF_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['PDF_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['PDF_SETTINGS']][CONFIG_KEYS['MAX_TEMP_FILES']] = str(max_files)
        self.save_config()

    # ========== インデックス関連の設定メソッド（新規追加） ==========

    def get_index_file_path(self) -> str:
        """インデックスファイルのパスを取得"""
        return self.config.get(
            CONFIG_SECTIONS['INDEX_SETTINGS'],
            CONFIG_KEYS['INDEX_FILE_PATH'],
            fallback=DEFAULT_INDEX_FILE
        )

    def set_index_file_path(self, path: str) -> None:
        """インデックスファイルのパスを設定"""
        if CONFIG_SECTIONS['INDEX_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['INDEX_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['INDEX_SETTINGS']][CONFIG_KEYS['INDEX_FILE_PATH']] = path
        self.save_config()

    def get_use_index_search(self) -> bool:
        """インデックス検索を使用するかどうかを取得"""
        return self.config.getboolean(
            CONFIG_SECTIONS['INDEX_SETTINGS'],
            CONFIG_KEYS['USE_INDEX_SEARCH'],
            fallback=DEFAULT_USE_INDEX_SEARCH
        )

    def set_use_index_search(self, use_index: bool) -> None:
        """インデックス検索を使用するかどうかを設定"""
        if CONFIG_SECTIONS['INDEX_SETTINGS'] not in self.config:
            self.config[CONFIG_SECTIONS['INDEX_SETTINGS']] = {}
        self.config[CONFIG_SECTIONS['INDEX_SETTINGS']][CONFIG_KEYS['USE_INDEX_SEARCH']] = str(use_index)
        self.save_config()
