import logging
import sys

from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow
from utils.config_manager import ConfigManager
from utils.log_rotation import setup_logging

logger = logging.getLogger(__name__)


def main():
    config = ConfigManager()
    log_level = config.config.get('LOGGING', 'log_level', fallback='INFO')
    log_directory = config.config.get('LOGGING', 'log_directory', fallback='logs')
    log_retention_days = config.config.getint('LOGGING', 'log_retention_days', fallback=7)

    setup_logging(log_directory=log_directory, log_retention_days=log_retention_days, log_level=log_level)
    logger.info("アプリケーションを起動します")

    try:
        app = QApplication(sys.argv)
        window = MainWindow(config)
        window.show()
        logger.info("メインウィンドウを表示しました")
        sys.exit(app.exec_())
    except Exception as e:
        logger.exception(f"アプリケーション起動中にエラーが発生しました: {e}")
        raise


if __name__ == '__main__':
    main()
