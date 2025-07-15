import sys

from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from utils.config_manager import load_config
from version import VERSION


def main():
    app = QApplication(sys.argv)
    config = load_config()
    window = MainWindow(
        config=config,
        version=VERSION
    )
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()