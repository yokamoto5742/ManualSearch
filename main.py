import sys

from PyQt5.QtWidgets import QApplication

from main_window import MainWindow
from config_manager import ConfigManager

VERSION = "1.1.4"
LAST_UPDATED = "2024/10/20"

def main():
    app = QApplication(sys.argv)
    config_manager = ConfigManager()
    window = MainWindow(config_manager)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()