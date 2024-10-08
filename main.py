import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui import MainWindow

VERSION = "1.1.0"
LAST_UPDATED = "2024/10/08"

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.setWindowTitle(f"マニュアル検索アプリ v{VERSION}")
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
