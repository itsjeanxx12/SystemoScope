
import sys
from PySide6.QtWidgets import QMainWindow, QApplication, QLabel, QListWidgetItem, QWidget, QGridLayout
from PySide6.QtCore import Qt,QSize
from PySide6.QtGui import QIcon, QPixmap, QFont

from main_sidebar_ui import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()

        self.ui.setupUi(self)

        self.title_label = self.ui.title_label
        self.title_label.setText("SystemoScope")
        titlefont = self.title_label.font()
        titlefont.setBold(True)
        titlefont.setPointSize(15)
        self.title_label.setFont(titlefont)

        self.side_menu = self.ui.listWidget_2
        self.side_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.side_menu_icon_only = self.ui.listWidget
        self.side_menu_icon_only.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.side_menu_icon_only.hide()

        self.menu_btn = self.ui.pushButton
        self.menu_btn.setText("☰")
        self.menu_btn.setFixedSize(30, 30)
        self.menu_btn.setCheckable(True)
        self.menu_btn.setChecked(False)

        self.main_content = self.ui.stackedWidget
        self.menu_list = [
            {
                "name": "Summary",
                "icon": "./icons/summary.svg"
            },
            {
                "name": "Health",
                "icon": "./icons/health.svg"
            },
            {
                "name": "Network",
                "icon": "./icons/network.svg"
            },
            {
                "name": "Performance",
                "icon": "./icons/performance.svg"
            },
            {
                "name": "Diagnostics",
                "icon": "./icons/diagnostics.svg"
            },
            {
                "name": "Software",
                "icon": "./icons/software.svg"
            }
        ]

        self.init_list_widget()
        self.init_signal_slot()
        self.init_stacked_widget()

    def init_signal_slot(self):
        self.menu_btn.toggled.connect(self.side_menu.setHidden)
        self.menu_btn.toggled.connect(self.title_label.setHidden)
        self.menu_btn.toggled.connect(self.side_menu_icon_only.setVisible)

        self.side_menu.currentRowChanged.connect(self.main_content.setCurrentIndex)
        self.side_menu_icon_only.currentRowChanged.connect(self.main_content.setCurrentIndex)
        self.side_menu.currentRowChanged.connect(self.side_menu_icon_only.setCurrentRow)
        self.side_menu_icon_only.currentRowChanged.connect(self.side_menu.setCurrentRow)

        self.menu_btn.toggled.connect(self.button_icon_change)

    def init_list_widget(self):
        self.side_menu.clear()
        self.side_menu_icon_only.clear()

        for menu in self.menu_list:
            item = QListWidgetItem()
            item.setIcon(QIcon(menu.get("icon")))
            item.setSizeHint(QSize(40, 40))
            self.side_menu_icon_only.addItem(item)

            item_new = QListWidgetItem()
            item_new.setIcon(QIcon(menu.get("icon")))
            item_new.setText(menu.get("name"))
            self.side_menu.addItem(item_new)

        self.side_menu.setCurrentRow(0)

    def init_stacked_widget(self):
        widget_list = self.main_content.findChildren(QWidget)
        for widget in widget_list:
            self.main_content.removeWidget(widget)
            widget.deleteLater()

        for menu in self.menu_list:
            text = menu.get("name")
            layout = QGridLayout()
            label = QLabel(text=text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setPixelSize(20)
            label.setFont(font)
            layout.addWidget(label)
            new_page = QWidget()
            new_page.setLayout(layout)
            self.main_content.addWidget(new_page)

    def button_icon_change(self, status):
        if status:
            self.menu_btn.setText("☰")
        else:
            self.menu_btn.setText("☰")


if __name__ == "__main__":
    app=QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
