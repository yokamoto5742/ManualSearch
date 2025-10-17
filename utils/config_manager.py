import configparser
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from utils.constants import (
    CONFIG_FILENAME,
    CONFIG_KEYS,
    CONFIG_SECTIONS,
    DEFAULT_ACROBAT_PATH,
    DEFAULT_CONTEXT_LENGTH,
    DEFAULT_FONT_SIZE,
    DEFAULT_HTML_FONT_SIZE,
    DEFAULT_INDEX_FILE,
    DEFAULT_MAX_TEMP_FILES,
    DEFAULT_PDF_TIMEOUT,
    DEFAULT_USE_INDEX_SEARCH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_X,
    DEFAULT_WINDOW_Y,
    MAX_FONT_SIZE,
    MAX_MAX_TEMP_FILES,
    MAX_PDF_TIMEOUT,
    MAX_WINDOW_HEIGHT,
    MAX_WINDOW_WIDTH,
    MIN_FONT_SIZE,
    MIN_MAX_TEMP_FILES,
    MIN_PDF_TIMEOUT,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    SUPPORTED_FILE_EXTENSIONS,
)
from utils.helpers import read_file_with_auto_encoding


def get_config_path() -> str:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, CONFIG_FILENAME)


CONFIG_PATH = get_config_path()


class ConfigValueValidator:
    RANGES: Dict[str, Tuple[int, int]] = {
        'window_width': (MIN_WINDOW_WIDTH, MAX_WINDOW_WIDTH),
        'window_height': (MIN_WINDOW_HEIGHT, MAX_WINDOW_HEIGHT),
        'font_size': (MIN_FONT_SIZE, MAX_FONT_SIZE),
        'filename_font_size': (MIN_FONT_SIZE, MAX_FONT_SIZE),
        'result_detail_font_size': (MIN_FONT_SIZE, MAX_FONT_SIZE),
        'html_font_size': (MIN_FONT_SIZE, MAX_FONT_SIZE),
        'timeout': (MIN_PDF_TIMEOUT, MAX_PDF_TIMEOUT),
        'max_temp_files': (MIN_MAX_TEMP_FILES, MAX_MAX_TEMP_FILES),
    }
    
    @classmethod
    def validate_and_clamp(cls, key: str, value: int) -> int:
        if key in cls.RANGES:
            min_val, max_val = cls.RANGES[key]
            return max(min_val, min(max_val, value))
        return value
    
    @classmethod
    def validate_range(cls, key: str, value: int) -> None:
        if key in cls.RANGES:
            min_val, max_val = cls.RANGES[key]
            if not min_val <= value <= max_val:
                raise ValueError(f"{key}は{min_val}-{max_val}の範囲で指定してください: {value}")


class ConfigManager:
    DEFAULTS: Dict[str, Any] = {
        'window_width': DEFAULT_WINDOW_WIDTH,
        'window_height': DEFAULT_WINDOW_HEIGHT,
        'window_x': DEFAULT_WINDOW_X,
        'window_y': DEFAULT_WINDOW_Y,
        'font_size': DEFAULT_FONT_SIZE,
        'filename_font_size': DEFAULT_FONT_SIZE,
        'result_detail_font_size': DEFAULT_FONT_SIZE,
        'html_font_size': DEFAULT_HTML_FONT_SIZE,
        'context_length': DEFAULT_CONTEXT_LENGTH,
        'timeout': DEFAULT_PDF_TIMEOUT,
        'max_temp_files': DEFAULT_MAX_TEMP_FILES,
        'cleanup_temp_files': True,
        'acrobat_path': DEFAULT_ACROBAT_PATH,
        'index_file_path': DEFAULT_INDEX_FILE,
        'use_index_search': DEFAULT_USE_INDEX_SEARCH,
        'extensions': ','.join(SUPPORTED_FILE_EXTENSIONS),
    }

    def __init__(self, config_file: str = CONFIG_PATH):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self) -> None:
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, encoding='utf-8') as configfile:
                self.config.read_file(configfile)
        except UnicodeDecodeError:
            content = read_file_with_auto_encoding(self.config_file)
            self.config.read_string(content)

    def save_config(self) -> None:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except IOError as e:
            print(f"設定の保存に失敗: {e}")

    def _get_int(self, section: str, key: str, validate: bool = True) -> int:
        default = self.DEFAULTS.get(key, 0)
        value = self.config.getint(section, key, fallback=default)
        
        if validate:
            value = ConfigValueValidator.validate_and_clamp(key, value)
        
        return value
    
    def _set_int(self, section: str, key: str, value: int, validate: bool = True) -> None:
        if validate:
            ConfigValueValidator.validate_range(key, value)
        
        self._ensure_section(section)
        self.config[section][key] = str(value)
        self.save_config()
    
    def _get_str(self, section: str, key: str) -> str:
        default = self.DEFAULTS.get(key, '')
        return self.config.get(section, key, fallback=default)
    
    def _set_str(self, section: str, key: str, value: str) -> None:
        self._ensure_section(section)
        self.config[section][key] = value
        self.save_config()
    
    def _get_bool(self, section: str, key: str) -> bool:
        default = self.DEFAULTS.get(key, False)
        return self.config.getboolean(section, key, fallback=default)
    
    def _set_bool(self, section: str, key: str, value: bool) -> None:
        self._ensure_section(section)
        self.config[section][key] = str(value)
        self.save_config()
    
    def _ensure_section(self, section: str) -> None:
        if section not in self.config:
            self.config[section] = {}
    
    def get_window_width(self) -> int:
        return self._get_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['WINDOW_WIDTH'])
    
    def set_window_width(self, width: int) -> None:
        self._set_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['WINDOW_WIDTH'], width)
    
    def get_window_height(self) -> int:
        return self._get_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['WINDOW_HEIGHT'])
    
    def set_window_height(self, height: int) -> None:
        self._set_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['WINDOW_HEIGHT'], height)
    
    def get_window_x(self) -> int:
        return self._get_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['WINDOW_X'], validate=False)
    
    def get_window_y(self) -> int:
        return self._get_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['WINDOW_Y'], validate=False)
    
    def get_window_size_and_position(self) -> List[int]:
        return [
            self.get_window_x(),
            self.get_window_y(),
            self.get_window_width(),
            self.get_window_height(),
        ]
    
    def set_window_size_and_position(self, x: int, y: int, width: int, height: int) -> None:
        section = CONFIG_SECTIONS['WINDOW_SETTINGS']
        self._ensure_section(section)

        width = ConfigValueValidator.validate_and_clamp('window_width', width)
        height = ConfigValueValidator.validate_and_clamp('window_height', height)
        
        self.config[section][CONFIG_KEYS['WINDOW_X']] = str(x)
        self.config[section][CONFIG_KEYS['WINDOW_Y']] = str(y)
        self.config[section][CONFIG_KEYS['WINDOW_WIDTH']] = str(width)
        self.config[section][CONFIG_KEYS['WINDOW_HEIGHT']] = str(height)
        
        self.save_config()
    
    def get_font_size(self) -> int:
        return self._get_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['FONT_SIZE'])
    
    def set_font_size(self, size: int) -> None:
        self._set_int(CONFIG_SECTIONS['WINDOW_SETTINGS'], CONFIG_KEYS['FONT_SIZE'], size)
    
    def get_filename_font_size(self) -> int:
        return self._get_int(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['FILENAME_FONT_SIZE'])
    
    def set_filename_font_size(self, size: int) -> None:
        self._set_int(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['FILENAME_FONT_SIZE'], size)
    
    def get_result_detail_font_size(self) -> int:
        return self._get_int(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['RESULT_DETAIL_FONT_SIZE'])
    
    def set_result_detail_font_size(self, size: int) -> None:
        self._set_int(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['RESULT_DETAIL_FONT_SIZE'], size)
    
    def get_html_font_size(self) -> int:
        return self._get_int(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['HTML_FONT_SIZE'])
    
    def set_html_font_size(self, size: int) -> None:
        self._set_int(CONFIG_SECTIONS['UI_SETTINGS'], CONFIG_KEYS['HTML_FONT_SIZE'], size)
    
    def get_acrobat_path(self) -> str:
        return self._get_str(CONFIG_SECTIONS['PATHS'], CONFIG_KEYS['ACROBAT_PATH'])
    
    def set_acrobat_path(self, path: str) -> None:
        self._set_str(CONFIG_SECTIONS['PATHS'], CONFIG_KEYS['ACROBAT_PATH'], path)
    
    def get_acrobat_reader_path(self) -> str:
        return self._get_str(CONFIG_SECTIONS['PATHS'], CONFIG_KEYS['ACROBAT_READER_PATH'])
    
    def get_acrobat_reader_x86_path(self) -> str:
        return self._get_str(CONFIG_SECTIONS['PATHS'], CONFIG_KEYS['ACROBAT_READER_X86_PATH'])
    
    def find_available_acrobat_path(self) -> Optional[str]:
        paths_to_check = [
            self.get_acrobat_path(),
            self.get_acrobat_reader_path(),
            self.get_acrobat_reader_x86_path(),
        ]
        
        for path in paths_to_check:
            if os.path.exists(path):
                return path
        
        return None
    
    def get_directories(self) -> List[str]:
        directories_str = self._get_str(CONFIG_SECTIONS['DIRECTORIES'], CONFIG_KEYS['DIRECTORY_LIST'])
        return [d.strip() for d in directories_str.split(',') if d.strip()]
    
    def set_directories(self, directories: List[str]) -> None:
        self._set_str(CONFIG_SECTIONS['DIRECTORIES'], CONFIG_KEYS['DIRECTORY_LIST'], ','.join(directories))
    
    def get_last_directory(self) -> str:
        return self._get_str(CONFIG_SECTIONS['DIRECTORIES'], CONFIG_KEYS['LAST_DIRECTORY'])
    
    def set_last_directory(self, directory: str) -> None:
        self._set_str(CONFIG_SECTIONS['DIRECTORIES'], CONFIG_KEYS['LAST_DIRECTORY'], directory)
    
    def get_file_extensions(self) -> List[str]:
        extensions_str = self._get_str(CONFIG_SECTIONS['FILE_TYPES'], CONFIG_KEYS['EXTENSIONS'])
        return [ext.strip() for ext in extensions_str.split(',') if ext.strip()]
    
    def set_file_extensions(self, extensions: List[str]) -> None:
        self._set_str(CONFIG_SECTIONS['FILE_TYPES'], CONFIG_KEYS['EXTENSIONS'], ','.join(extensions))
    
    def get_context_length(self) -> int:
        return self._get_int(CONFIG_SECTIONS['SEARCH_SETTINGS'], CONFIG_KEYS['CONTEXT_LENGTH'], validate=False)
    
    def set_context_length(self, length: int) -> None:
        self._set_int(CONFIG_SECTIONS['SEARCH_SETTINGS'], CONFIG_KEYS['CONTEXT_LENGTH'], length, validate=False)
    
    def get_pdf_timeout(self) -> int:
        return self._get_int(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['TIMEOUT'])
    
    def set_pdf_timeout(self, timeout: int) -> None:
        self._set_int(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['TIMEOUT'], timeout)
    
    def get_cleanup_temp_files(self) -> bool:
        return self._get_bool(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['CLEANUP_TEMP_FILES'])
    
    def set_cleanup_temp_files(self, cleanup: bool) -> None:
        self._set_bool(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['CLEANUP_TEMP_FILES'], cleanup)
    
    def get_max_temp_files(self) -> int:
        return self._get_int(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['MAX_TEMP_FILES'])
    
    def set_max_temp_files(self, max_files: int) -> None:
        self._set_int(CONFIG_SECTIONS['PDF_SETTINGS'], CONFIG_KEYS['MAX_TEMP_FILES'], max_files)
    
    def get_index_file_path(self) -> str:
        return self._get_str(CONFIG_SECTIONS['INDEX_SETTINGS'], CONFIG_KEYS['INDEX_FILE_PATH'])
    
    def set_index_file_path(self, path: str) -> None:
        self._set_str(CONFIG_SECTIONS['INDEX_SETTINGS'], CONFIG_KEYS['INDEX_FILE_PATH'], path)
    
    def get_use_index_search(self) -> bool:
        return self._get_bool(CONFIG_SECTIONS['INDEX_SETTINGS'], CONFIG_KEYS['USE_INDEX_SEARCH'])
    
    def set_use_index_search(self, use_index: bool) -> None:
        self._set_bool(CONFIG_SECTIONS['INDEX_SETTINGS'], CONFIG_KEYS['USE_INDEX_SEARCH'], use_index)
