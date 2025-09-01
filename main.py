import sys
import warnings

from PyQt5.QtWidgets import QApplication

from app.main_window import MainWindow
from utils.config_manager import ConfigManager

# Swigに関するDeprecationWarningを抑制
warnings.filterwarnings("ignore", "builtin type SwigPyPacked has no __module__ attribute", DeprecationWarning)
warnings.filterwarnings("ignore", "builtin type SwigPyObject has no __module__ attribute", DeprecationWarning)
warnings.filterwarnings("ignore", "builtin type swigvarlink has no __module__ attribute", DeprecationWarning)


def main():
    app = QApplication(sys.argv)
    config = ConfigManager()
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()