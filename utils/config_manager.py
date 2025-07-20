import configparser
import os
import sys
from typing import List

from utils.helpers import read_file_with_auto_encoding


def get_config_path() -> str:
    base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    return os.path.join(base_path, 'config.ini')

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
                self.config.write(configfile) # type: ignore
        except IOError as e:
            print(f"Error saving config: {e}")

    def get_file_extensions(self) -> List[str]:
        extensions = self.config.get('FileTypes', 'extensions', fallback='.pdf,.txt,.md')
        return [ext.strip() for ext in extensions.split(',') if ext.strip()]

    def get_window_geometry(self) -> List[int]:
        geometry = self.config.get('WindowSettings', 'geometry', fallback='100,100,1150,900')
        return [int(val) for val in geometry.split(',')]

    def get_font_size(self) -> int:
        size = self.config.getint('WindowSettings', 'font_size', fallback=16)
        return max(8, min(32, size))  # 8-32の範囲でクランプ

    def get_acrobat_path(self) -> str:
        return self.config.get('Paths', 'acrobat_path', fallback=r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe')

    def set_file_extensions(self, extensions: List[str]) -> None:
        if 'FileTypes' not in self.config:
            self.config['FileTypes'] = {}
        self.config['FileTypes']['extensions'] = ','.join(extensions)
        self.save_config()

    def set_window_geometry(self, x: int, y: int, width: int, height: int) -> None:
        if 'WindowSettings' not in self.config:
            self.config['WindowSettings'] = {}
        self.config['WindowSettings']['geometry'] = f"{x},{y},{width},{height}"
        self.save_config()

    def set_font_size(self, size: int) -> None:
        if not 8 <= size <= 32:
            raise ValueError(f"フォントサイズは8-32の範囲で指定してください: {size}")

        if 'WindowSettings' not in self.config:
            self.config['WindowSettings'] = {}
        self.config['WindowSettings']['font_size'] = str(size)
        self.save_config()

    def set_acrobat_path(self, path: str) -> None:
        if 'Paths' not in self.config:
            self.config['Paths'] = {}
        self.config['Paths']['acrobat_path'] = path
        self.save_config()

    def get_directories(self) -> List[str]:
        directories = self.config.get('Directories', 'list', fallback='')
        return [dir.strip() for dir in directories.split(',') if dir.strip()]

    def set_directories(self, directories: List[str]) -> None:
        if 'Directories' not in self.config:
            self.config['Directories'] = {}
        self.config['Directories']['list'] = ','.join(directories)
        self.save_config()

    def get_last_directory(self) -> str:
        return self.config.get('Directories', 'last_directory', fallback='')

    def set_last_directory(self, directory: str) -> None:
        if 'Directories' not in self.config:
            self.config['Directories'] = {}
        self.config['Directories']['last_directory'] = directory
        self.save_config()

    def get_context_length(self) -> int:
        return self.config.getint('SearchSettings', 'context_length', fallback=100)

    def set_context_length(self, length: int) -> None:
        if 'SearchSettings' not in self.config:
            self.config['SearchSettings'] = {}
        self.config['SearchSettings']['context_length'] = str(length)
        self.save_config()

    def get_filename_font_size(self) -> int:
        return self.config.getint('UISettings', 'filename_font_size', fallback=14)

    def set_filename_font_size(self, size: int) -> None:
        if 'UISettings' not in self.config:
            self.config['UISettings'] = {}
        self.config['UISettings']['filename_font_size'] = str(size)
        self.save_config()

    def get_result_detail_font_size(self) -> int:
        return self.config.getint('UISettings', 'result_detail_font_size', fallback=14)

    def set_result_detail_font_size(self, size: int) -> None:
        if 'UISettings' not in self.config:
            self.config['UISettings'] = {}
        self.config['UISettings']['result_detail_font_size'] = str(size)
        self.save_config()

    def get_html_font_size(self) -> int:
        return self.config.getint('UISettings', 'html_font_size', fallback=16)

    def set_html_font_size(self, size: int) -> None:
        if 'UISettings' not in self.config:
            self.config['UISettings'] = {}
        self.config['UISettings']['html_font_size'] = str(size)
        self.save_config()

    def get_pdf_timeout(self) -> int:
        return self.config.getint('PDFSettings', 'timeout', fallback=30)

    def set_pdf_timeout(self, timeout: int) -> None:
        if not 10 <= timeout <= 120:
            raise ValueError(f"タイムアウトは10-120秒の範囲で指定してください: {timeout}")

        if 'PDFSettings' not in self.config:
            self.config['PDFSettings'] = {}
        self.config['PDFSettings']['timeout'] = str(timeout)
        self.save_config()

    def get_cleanup_temp_files(self) -> bool:
        return self.config.getboolean('PDFSettings', 'cleanup_temp_files', fallback=True)

    def set_cleanup_temp_files(self, cleanup: bool) -> None:
        if 'PDFSettings' not in self.config:
            self.config['PDFSettings'] = {}
        self.config['PDFSettings']['cleanup_temp_files'] = str(cleanup)
        self.save_config()

    def get_max_temp_files(self) -> int:
        return self.config.getint('PDFSettings', 'max_temp_files', fallback=10)

    def set_max_temp_files(self, max_files: int) -> None:
        if not 1 <= max_files <= 50:
            raise ValueError(f"最大ファイル数は1-50の範囲で指定してください: {max_files}")

        if 'PDFSettings' not in self.config:
            self.config['PDFSettings'] = {}
        self.config['PDFSettings']['max_temp_files'] = str(max_files)
        self.save_config()
