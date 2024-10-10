import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
from config_manager import ConfigManager

VERSION = "1.0.5"
LAST_UPDATED = "2024/09/24"

def main():
    app = QApplication(sys.argv)
    config_manager = ConfigManager()  # ConfigManager のインスタンスを作成
    window = MainWindow(config_manager)  # ConfigManager のインスタンスを MainWindow に渡す
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()