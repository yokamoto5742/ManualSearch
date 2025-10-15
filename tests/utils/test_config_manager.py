import os

import pytest

from utils.constants import (
    MAX_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
)
from utils.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManagerクラスのテスト"""

    def test_init_with_existing_config(self, temp_config_file):
        """既存の設定ファイルでの初期化テスト"""
        config = ConfigManager(temp_config_file)
        assert config.config_file == temp_config_file
        assert len(config.config.sections()) > 0

    def test_init_without_config(self, temp_dir):
        """設定ファイルが存在しない場合の初期化テスト"""
        non_existent_path = os.path.join(temp_dir, 'non_existent.ini')
        config = ConfigManager(non_existent_path)
        assert config.config_file == non_existent_path

    def test_get_file_extensions(self, temp_config_file):
        """ファイル拡張子の取得テスト"""
        config = ConfigManager(temp_config_file)
        extensions = config.get_file_extensions()
        assert isinstance(extensions, list)
        assert '.pdf' in extensions
        assert '.txt' in extensions
        assert '.md' in extensions

    def test_get_window_dimensions(self, temp_config_file):
        """ウィンドウサイズ関連の取得テスト"""
        config = ConfigManager(temp_config_file)

        # 個別取得のテスト
        assert config.get_window_width() == 1150
        assert config.get_window_height() == 900
        assert config.get_window_x() == 50
        assert config.get_window_y() == 50

        # 一括取得のテスト
        size_pos = config.get_window_size_and_position()
        assert size_pos == [50, 50, 1150, 900]

    def test_window_size_validation(self, temp_config_file):
        """ウィンドウサイズの範囲検証テスト"""
        config = ConfigManager(temp_config_file)

        # 範囲外の値を設定
        config.config['WindowSettings']['window_width'] = '10000'
        config.config['WindowSettings']['window_height'] = '10'

        # 範囲内にクランプされることを確認
        assert config.get_window_width() == MAX_WINDOW_WIDTH
        assert config.get_window_height() == MIN_WINDOW_HEIGHT

    def test_set_window_dimensions(self, temp_config_file):
        """ウィンドウサイズ設定のテスト"""
        config = ConfigManager(temp_config_file)

        # 個別設定
        config.set_window_width(1200)
        config.set_window_height(800)
        assert config.get_window_width() == 1200
        assert config.get_window_height() == 800

        # 一括設定
        config.set_window_size_and_position(100, 100, 1300, 950)
        assert config.get_window_x() == 100
        assert config.get_window_y() == 100
        assert config.get_window_width() == 1300
        assert config.get_window_height() == 950

    def test_font_size(self, temp_config_file):
        """フォントサイズ関連のテスト"""
        config = ConfigManager(temp_config_file)

        # デフォルト値の確認
        assert config.get_font_size() == 14
        assert config.get_html_font_size() == 16

        # 設定と取得
        config.set_font_size(18)
        assert config.get_font_size() == 18

        # 範囲外の値での例外テスト
        with pytest.raises(ValueError):
            config.set_font_size(50)

    def test_directories_management(self, temp_config_file):
        """ディレクトリ管理のテスト"""
        config = ConfigManager(temp_config_file)

        # 初期状態
        assert config.get_directories() == []
        assert config.get_last_directory() == ''

        # ディレクトリの設定
        dirs = ['/path/to/dir1', '/path/to/dir2']
        config.set_directories(dirs)
        assert config.get_directories() == dirs

        # 最後のディレクトリ
        config.set_last_directory('/path/to/dir1')
        assert config.get_last_directory() == '/path/to/dir1'

    def test_index_settings(self, temp_config_file):
        """インデックス設定のテスト"""
        config = ConfigManager(temp_config_file)

        # デフォルト値
        assert config.get_index_file_path() == 'search_index.json'
        assert config.get_use_index_search() == False

        # 設定変更
        config.set_index_file_path('/custom/path/index.json')
        config.set_use_index_search(True)

        assert config.get_index_file_path() == '/custom/path/index.json'
        assert config.get_use_index_search() == True

    def test_pdf_settings(self, temp_config_file):
        """PDF設定のテスト"""
        config = ConfigManager(temp_config_file)

        # タイムアウト設定
        assert config.get_pdf_timeout() == 30
        config.set_pdf_timeout(60)
        assert config.get_pdf_timeout() == 60

        # 範囲外の値での例外テスト
        with pytest.raises(ValueError):
            config.set_pdf_timeout(200)

        # その他の設定
        assert config.get_cleanup_temp_files() == True
        assert config.get_max_temp_files() == 10

    def test_save_and_load(self, temp_dir):
        """設定の保存と読み込みテスト"""
        config_path = os.path.join(temp_dir, 'save_test.ini')

        # 新規作成と保存
        config1 = ConfigManager(config_path)
        config1.set_font_size(20)
        config1.set_directories(['/test/path'])
        config1.save_config()

        # 別インスタンスで読み込み
        config2 = ConfigManager(config_path)
        assert config2.get_font_size() == 20
        assert config2.get_directories() == ['/test/path']
