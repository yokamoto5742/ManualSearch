import pytest
import os
import configparser
from config_manager import ConfigManager

@pytest.fixture
def temp_config_file(tmp_path):
    config_file = tmp_path / "test_config.ini"
    config_file.touch()  # 空のファイルを作成
    return str(config_file)

@pytest.fixture
def config_manager(temp_config_file):
    return ConfigManager(temp_config_file)

def test_init_and_load_config(config_manager, temp_config_file):
    assert os.path.exists(temp_config_file)
    assert isinstance(config_manager.config, configparser.ConfigParser)

def test_get_file_extensions(config_manager):
    assert config_manager.get_file_extensions() == ['.pdf', '.txt', '.md']

def test_set_file_extensions(config_manager):
    new_extensions = ['.docx', '.xlsx']
    config_manager.set_file_extensions(new_extensions)
    assert config_manager.get_file_extensions() == new_extensions

def test_get_window_geometry(config_manager):
    assert config_manager.get_window_geometry() == [100, 100, 1150, 900]

def test_set_window_geometry(config_manager):
    new_geometry = [200, 200, 1000, 900]
    config_manager.set_window_geometry(*new_geometry)
    assert config_manager.get_window_geometry() == new_geometry

def test_get_font_size(config_manager):
    assert config_manager.get_font_size() == 16

def test_set_font_size(config_manager):
    new_size = 18
    config_manager.set_font_size(new_size)
    assert config_manager.get_font_size() == new_size

def test_get_acrobat_path(config_manager):
    assert config_manager.get_acrobat_path() == r'C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe'

def test_set_acrobat_path(config_manager):
    new_path = r'D:\Adobe\Acrobat.exe'
    config_manager.set_acrobat_path(new_path)
    assert config_manager.get_acrobat_path() == new_path

def test_get_directories(config_manager):
    assert config_manager.get_directories() == []

def test_set_directories(config_manager):
    new_dirs = ['/home/user/docs', '/home/user/downloads']
    config_manager.set_directories(new_dirs)
    assert config_manager.get_directories() == new_dirs

def test_get_last_directory(config_manager):
    assert config_manager.get_last_directory() == ''

def test_set_last_directory(config_manager):
    new_dir = '/home/user/last_dir'
    config_manager.set_last_directory(new_dir)
    assert config_manager.get_last_directory() == new_dir

def test_get_context_length(config_manager):
    assert config_manager.get_context_length() == 100

def test_set_context_length(config_manager):
    new_length = 100
    config_manager.set_context_length(new_length)
    assert config_manager.get_context_length() == new_length

def test_get_filename_font_size(config_manager):
    assert config_manager.get_filename_font_size() == 14

def test_set_filename_font_size(config_manager):
    new_size = 14
    config_manager.set_filename_font_size(new_size)
    assert config_manager.get_filename_font_size() == new_size

def test_get_result_detail_font_size(config_manager):
    assert config_manager.get_result_detail_font_size() == 14

def test_set_result_detail_font_size(config_manager):
    new_size = 14
    config_manager.set_result_detail_font_size(new_size)
    assert config_manager.get_result_detail_font_size() == new_size

def test_get_html_font_size(config_manager):
    assert config_manager.get_html_font_size() == 16

def test_set_html_font_size(config_manager):
    new_size = 18
    config_manager.set_html_font_size(new_size)
    assert config_manager.get_html_font_size() == new_size

def test_save_and_load_config(config_manager, temp_config_file):
    # 設定を変更
    config_manager.set_file_extensions(['.doc', '.xls'])
    config_manager.set_window_geometry(300, 300, 1100, 1000)
    config_manager.set_font_size(20)
    config_manager.set_acrobat_path(r'E:\Adobe\Acrobat.exe')
    config_manager.set_directories(['/path1', '/path2'])
    config_manager.set_last_directory('/last_path')
    config_manager.set_context_length(75)
    config_manager.set_filename_font_size(15)
    config_manager.set_result_detail_font_size(15)
    config_manager.set_html_font_size(20)

    # 新しいConfigManagerインスタンスを作成して設定を読み込む
    new_config_manager = ConfigManager(temp_config_file)

    # 設定が正しく保存され、読み込まれたことを確認
    assert new_config_manager.get_file_extensions() == ['.doc', '.xls']
    assert new_config_manager.get_window_geometry() == [300, 300, 1100, 1000]
    assert new_config_manager.get_font_size() == 20
    assert new_config_manager.get_acrobat_path() == r'E:\Adobe\Acrobat.exe'
    assert new_config_manager.get_directories() == ['/path1', '/path2']
    assert new_config_manager.get_last_directory() == '/last_path'
    assert new_config_manager.get_context_length() == 75
    assert new_config_manager.get_filename_font_size() == 15
    assert new_config_manager.get_result_detail_font_size() == 15
    assert new_config_manager.get_html_font_size() == 20
