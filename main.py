import sys

from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow
from utils.config_manager import ConfigManager


def main():
    app = QApplication(sys.argv)
    config = ConfigManager()
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()