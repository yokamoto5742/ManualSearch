import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
from config_manager import ConfigManager

VERSION = "1.1.1"
LAST_UPDATED = "2024/10/14"

def main():
    app = QApplication(sys.argv)
    config_manager = ConfigManager()
    window = MainWindow(config_manager)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()