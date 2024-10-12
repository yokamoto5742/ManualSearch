import configparser
import os
import sys
from utils import read_file_with_auto_encoding

def get_config_path():
    if getattr(sys, 'frozen', False):
        # PyInstallerでビルドされた実行ファイルの場合
        base_path = sys._MEIPASS
    else:
        # 通常のPythonスクリプトとして実行される場合
        base_path = os.path.dirname(__file__)

    return os.path.join(base_path, 'config.ini')

CONFIG_PATH = get_config_path()

class ConfigManager:
    def __init__(self, config_file=CONFIG_PATH):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as configfile:
                    self.config.read_file(configfile)
            except UnicodeDecodeError:
                # UTF-8で失敗した場合、他のエンコーディングを試す
                content = read_file_with_auto_encoding(self.config_file)
                self.config.read_string(content)

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def get_file_extensions(self):
        return self.config.get('FileTypes', 'extensions', fallback='.pdf,.txt,.md').split(',')

    def get_window_geometry(self):
        geometry = self.config.get('WindowSettings', 'geometry', fallback='100,100,900,800')
        return [int(x) for x in geometry.split(',')]

    def get_font_size(self):
        return self.config.getint('WindowSettings', 'font_size', fallback=16)

    def get_acrobat_path(self):
        return self.config.get('Paths', 'acrobat_path', fallback=r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe')

    def set_file_extensions(self, extensions):
        if 'FileTypes' not in self.config:
            self.config['FileTypes'] = {}
        self.config['FileTypes']['extensions'] = ','.join(extensions)
        self.save_config()

    def set_window_geometry(self, x, y, width, height):
        if 'WindowSettings' not in self.config:
            self.config['WindowSettings'] = {}
        self.config['WindowSettings']['geometry'] = f"{x},{y},{width},{height}"
        self.save_config()

    def set_font_size(self, size):
        if 'WindowSettings' not in self.config:
            self.config['WindowSettings'] = {}
        self.config['WindowSettings']['font_size'] = str(size)
        self.save_config()

    def set_acrobat_path(self, path):
        if 'Paths' not in self.config:
            self.config['Paths'] = {}
        self.config['Paths']['acrobat_path'] = path
        self.save_config()

    def get_directories(self):
        directories = self.config.get('Directories', 'list', fallback='').split(',')
        return [dir.strip() for dir in directories if dir.strip()]

    def set_directories(self, directories):
        if 'Directories' not in self.config:
            self.config['Directories'] = {}
        self.config['Directories']['list'] = ','.join(directories)
        self.save_config()

    def get_last_directory(self):
        return self.config.get('Directories', 'last_directory', fallback='')

    def set_last_directory(self, directory):
        if 'Directories' not in self.config:
            self.config['Directories'] = {}
        self.config['Directories']['last_directory'] = directory
        self.save_config()

    def get_context_length(self):
        return self.config.getint('SearchSettings', 'context_length', fallback=50)

    def set_context_length(self, length):
        if 'SearchSettings' not in self.config:
            self.config['SearchSettings'] = {}
        self.config['SearchSettings']['context_length'] = str(length)
        self.save_config()

    def get_filename_font_size(self):
        return self.config.getint('UISettings', 'filename_font_size', fallback=12)

    def set_filename_font_size(self, size):
        if 'UISettings' not in self.config:
            self.config['UISettings'] = {}
        self.config['UISettings']['filename_font_size'] = str(size)
        self.save_config()

    def get_result_detail_font_size(self):
        return self.config.getint('UISettings', 'result_detail_font_size', fallback=12)

    def set_result_detail_font_size(self, size):
        if 'UISettings' not in self.config:
            self.config['UISettings'] = {}
        self.config['UISettings']['result_detail_font_size'] = str(size)
        self.save_config()

    def get_html_font_size(self):
        return self.config.getint('UISettings', 'html_font_size', fallback=16)

    def set_html_font_size(self, size):
        if 'UISettings' not in self.config:
            self.config['UISettings'] = {}
        self.config['UISettings']['html_font_size'] = str(size)
        self.save_config()
