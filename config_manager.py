import configparser
import os
import sys
from typing import List, Tuple
import chardet

class ConfigManager:
    def __init__(self, config_file: str = 'config.ini'):
        self.config_file = self._get_config_path(config_file)
        self.config = configparser.ConfigParser()
        self.load_config()

    def _get_config_path(self, config_file: str) -> str:
        if getattr(sys, 'frozen', False):
            # PyInstallerでビルドされた実行ファイルの場合
            base_path = sys._MEIPASS
        else:
            # 通常のPythonスクリプトとして実行される場合
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, config_file)

    def load_config(self) -> None:
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config.read_file(f)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {self.config_file}")
            raise
        except PermissionError:
            print(f"設定ファイルを読み取る権限がありません: {self.config_file}")
            raise
        except configparser.Error as e:
            print(f"設定ファイルの解析中にエラーが発生しました: {e}")
            raise

    def save_config(self) -> None:
        try:
            with open(self.config_file, 'w', encoding='utf-8') as configfile:
                self.config.write(configfile)
        except PermissionError:
            print(f"設定ファイルを書き込む権限がありません: {self.config_file}")
            raise
        except IOError as e:
            print(f"設定ファイルの保存中にエラーが発生しました: {e}")
            raise

    def read_file_with_auto_encoding(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            raw_data = file.read()

        result = chardet.detect(raw_data)
        encoding = result['encoding']

        try:
            return raw_data.decode(encoding)
        except UnicodeDecodeError:
            # エンコーディング検出に失敗した場合、UTF-8を試してみる
            try:
                return raw_data.decode('utf-8')
            except UnicodeDecodeError:
                # UTF-8でも失敗した場合、CP932（Shift-JIS）を試す
                return raw_data.decode('cp932')

    @property
    def file_extensions(self) -> List[str]:
        return self.config.get('FileTypes', 'extensions', fallback='.pdf,.txt,.md').split(',')

    @file_extensions.setter
    def file_extensions(self, value: List[str]) -> None:
        self.config['FileTypes'] = {'extensions': ','.join(value)}
        self.save_config()

    @property
    def window_geometry(self) -> Tuple[int, int, int, int]:
        geometry = self.config.get('WindowSettings', 'geometry', fallback='100,100,900,800')
        return tuple(map(int, geometry.split(',')))

    @window_geometry.setter
    def window_geometry(self, value: Tuple[int, int, int, int]) -> None:
        self.config['WindowSettings'] = {'geometry': ','.join(map(str, value))}
        self.save_config()

    @property
    def font_size(self) -> int:
        return self.config.getint('WindowSettings', 'font_size', fallback=16)

    @font_size.setter
    def font_size(self, value: int) -> None:
        self.config['WindowSettings']['font_size'] = str(value)
        self.save_config()

    @property
    def acrobat_path(self) -> str:
        return self.config.get('Paths', 'acrobat_path', fallback=r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe')

    @acrobat_path.setter
    def acrobat_path(self, value: str) -> None:
        self.config['Paths'] = {'acrobat_path': value}
        self.save_config()

    @property
    def directories(self) -> List[str]:
        return self.config.get('Directories', 'list', fallback='').split(',')

    @directories.setter
    def directories(self, value: List[str]) -> None:
        self.config['Directories'] = {'list': ','.join(value)}
        self.save_config()

    @property
    def last_directory(self) -> str:
        return self.config.get('Directories', 'last_directory', fallback='')

    @last_directory.setter
    def last_directory(self, value: str) -> None:
        self.config['Directories']['last_directory'] = value
        self.save_config()

    @property
    def context_length(self) -> int:
        return self.config.getint('SearchSettings', 'context_length', fallback=50)

    @context_length.setter
    def context_length(self, value: int) -> None:
        self.config['SearchSettings'] = {'context_length': str(value)}
        self.save_config()

    @property
    def filename_font_size(self) -> int:
        return self.config.getint('UISettings', 'filename_font_size', fallback=14)

    @filename_font_size.setter
    def filename_font_size(self, value: int) -> None:
        self.config['UISettings'] = {'filename_font_size': str(value)}
        self.save_config()

    @property
    def result_detail_font_size(self) -> int:
        return self.config.getint('UISettings', 'result_detail_font_size', fallback=14)

    @result_detail_font_size.setter
    def result_detail_font_size(self, value: int) -> None:
        self.config['UISettings']['result_detail_font_size'] = str(value)
        self.save_config()

    @property
    def html_font_size(self) -> int:
        return self.config.getint('UISettings', 'html_font_size', fallback=16)

    @html_font_size.setter
    def html_font_size(self, value: int) -> None:
        self.config['UISettings']['html_font_size'] = str(value)
        self.save_config()
