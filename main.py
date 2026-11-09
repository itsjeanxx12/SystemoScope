import sys

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QLabel, QListWidgetItem,
    QWidget, QGridLayout, QVBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

from main_sidebar_ui import Ui_MainWindow
from monitor import get_system_info


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

    def create_card(self, title, value, description):
        card = QFrame()
        card.setObjectName("infoCard")
        card.setMinimumHeight(125)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("""
            color: #aaaaaa;
            font-size: 12px;
        """)

        value_label = QLabel(str(value))
        value_label.setWordWrap(True)
        value_label.setStyleSheet("""
            color: white;
            font-size: 19px;
            font-weight: bold;
        """)

        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("""
            color: #888888;
            font-size: 11px;
        """)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(description_label)
        layout.addStretch()

        card.setStyleSheet("""
            QFrame#infoCard {
                background-color: #292929;
                border: 1px solid #383838;
                border-radius: 8px;
            }

            QFrame#infoCard:hover {
                background-color: #303030;
                border: 1px solid #505050;
            }
        """)

        return card

    def create_summary_page(self):
        info = get_system_info()

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 20, 20, 20)
        page_layout.setSpacing(15)

        heading = QLabel("Your PC at a glance")
        heading.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
        """)

        subtitle = QLabel("A quick overview of your system.")
        subtitle.setStyleSheet("color: #999999; font-size: 12px;")

        page_layout.addWidget(heading)
        page_layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(12)

        cards = [
            (
                "OPERATING SYSTEM",
                info["os"],
                "Installed operating system"
            ),
            (
                "PROCESSOR",
                info["cpu"],
                f'{info["cores"]} cores / {info["threads"]} threads'
            ),
            (
                "MEMORY",
                f'{info["ramsize"]} GB RAM',
                f'{info["ramused"]} GB used / {info["ramfree"]} GB available'
            ),
            (
                "STORAGE",
                f'{info["disk"]} GB',
                f'{info["diskused"]} GB used / {info["diskfree"]} GB free (C:)'
            ),
            (
                "DEVICE",
                info["name"],
                f'Current user: {info["username"]}'
            ),
            (
                "ARCHITECTURE",
                info["architecture"],
                "System architecture"
            )
        ]

        for index, (title, value, description) in enumerate(cards):
            row = index // 2
            column = index % 2

            card = self.create_card(title, value, description)
            grid.addWidget(card, row, column)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        page_layout.addLayout(grid)
        page_layout.addStretch()

        return page

    def init_stacked_widget(self):
        while self.main_content.count():
            widget = self.main_content.widget(0)
            self.main_content.removeWidget(widget)
            widget.deleteLater()

        for menu in self.menu_list:
            text = menu.get("name")

            if text == "Summary":
                new_page = self.create_summary_page()

            else:
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
        self.menu_btn.setText("☰")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())