import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
import monitor

class main(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SystemoScope")
        self.resize(1200,700)

        self.splash=QLabel("<b>SystemoScope</b>")
        self.splash.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignTop)
        headingfont = self.splash.font()
        headingfont.setPointSize(30)
        self.splash.setFont(headingfont)

        self.welcome=QLabel(f"Welcome, <b>{monitor.get_username()}</b>")
        self.welcome.setAlignment(Qt.AlignmentFlag.AlignLeft)
        welcomefont = self.welcome.font()
        welcomefont.setPointSize(30)
        self.welcome.setFont(welcomefont)

        self.sysinfo = QLabel("<b>System Information: </b>")
        self.sysinfo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        sysinfofont = self.sysinfo.font()
        sysinfofont.setPointSize(25)
        self.sysinfo.setFont(sysinfofont)

        self.osinfo = QLabel(f"<b>OS:</b> {monitor.get_system_info()["os"]}")
        self.cpuinfo = QLabel(f"<b>CPU:</b> {monitor.get_system_info()["cpu"]}")
        self.raminfo = QLabel(f"<b>RAM Size:</b> {monitor.get_system_info()["ramsize"]} GB")
        self.pcname = QLabel(f"<b>PC Name:</b> {monitor.get_system_info()["name"]}")


        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(20)
        labels = [
            self.splash,
            self.welcome,
            self.sysinfo,
            self.osinfo,
            self.cpuinfo,
            self.raminfo,
            self.pcname,
        ]

        for label in [self.osinfo,self.cpuinfo,self.raminfo,self.pcname]:
            font = label.font()
            font.setPointSize(15)
            label.setFont(font)
            
        for label in labels:
            layout.addWidget(label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = main()
    window.show()
    sys.exit(app.exec())