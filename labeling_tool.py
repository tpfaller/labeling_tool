import sys
from PyQt5.QtWidgets import QApplication
from src.main_window import ImageLabeler

def main():
    app = QApplication(sys.argv)
    labeler = ImageLabeler()
    labeler.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
