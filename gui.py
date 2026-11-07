import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
import monitor

class main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SystemoScope")
        self.resize(1200,700)

        self.splash=QLabel("SystemoScope")
        self.splash.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignTop)
        headingfont = self.splash.font()
        headingfont.setPointSize(30)
        self.splash.setFont(headingfont)

        layout = QVBoxLayout()
        layout.addWidget(self.splash)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = main()
    window.show()
    sys.exit(app.exec())