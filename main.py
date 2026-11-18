import sys

from PySide6.QtWidgets import (
    QMainWindow, QApplication, QLabel, QListWidgetItem,
    QWidget, QGridLayout, QVBoxLayout, QFrame
)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QFont
import pyqtgraph as pg

from main_sidebar_ui import Ui_MainWindow
from monitor import get_system_info
from monitor import get_battery_info
from monitor import get_cpu_temp


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

    def create_health_page(self):
        battery = get_battery_info()
        cpu_temp = get_cpu_temp()
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(20, 20, 20, 20)
        page_layout.setSpacing(15)

        heading = QLabel("System Health")
        heading.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
        """)
        subtitle = QLabel("Monitor your system's health and battery.")
        subtitle.setStyleSheet("color: #999999; font-size: 12px;")
        page_layout.addWidget(heading)
        page_layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(12)

        cards = []
        if battery is not None and battery["percent"] is not None:
            cards.append((
                "BATTERY",
                f'{battery["percent"]}%',
                f'Time Left : {battery["secsleft"] // 3600}h {(battery["secsleft"] % 3600) // 60}m'
            ))
        else:
            cards.append((
                "BATTERY",
                "No battery",
                ""
            ))

        if cpu_temp is not None:
            temp_val = f"{round(cpu_temp, 1)} °C"
            temp_desc = "Normal temperature" if cpu_temp < 80 else "High temperature"
        else:
            temp_val = "N/A"
            temp_desc = "Run as Administrator to read sensor"

        cards.append((
            "CPU TEMPERATURE",
            temp_val,
            temp_desc
        ))

        for index, (title, value, description) in enumerate(cards):
            row = index // 2
            column = index % 2

            card = self.create_card(title, value, description)
            if title == "CPU TEMPERATURE":
                self.cpu_temp_card = card
            grid.addWidget(card, row, column)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        page_layout.addLayout(grid)

        self.cpu_temp_history = [round(cpu_temp, 1)] if cpu_temp is not None else [0]

        self.temp_plot = pg.PlotWidget()
        self.temp_plot.setBackground("#292929")
        self.temp_plot.setTitle("CPU Temperature (°C)", color="#ffffff", size="11pt")
        self.temp_plot.setLabel("left", "Temperature (°C)", color="#aaaaaa")
        self.temp_plot.setLabel("bottom", "Time (s)", color="#aaaaaa")
        self.temp_plot.showGrid(x=True, y=True, alpha=0.2)
        self.temp_plot.setYRange(0, 100)
        self.temp_plot.setMinimumHeight(220)

        pen = pg.mkPen(color="#ff5555", width=2)
        self.temp_curve = self.temp_plot.plot(self.cpu_temp_history, pen=pen)

        page_layout.addWidget(self.temp_plot)
        page_layout.addStretch()

        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self.update_cpu_temp)
        self.health_timer.start(1000)

        return page

    def update_cpu_temp(self):
        temp = get_cpu_temp()
        labels = self.cpu_temp_card.findChildren(QLabel)
        if temp is not None:
            temp_rounded = round(temp, 1)
            self.cpu_temp_history.append(temp_rounded)
            if len( labels ) >= 3:
                labels[1].setText(f"{temp_rounded} °C")
                labels[2].setText("Normal temperature" if temp_rounded < 80 else "High temperature")
        else:
            self.cpu_temp_history.append(0)
            if len( labels ) >= 3:
                labels[1].setText("N/A")
                labels[2].setText("Run as Administrator to read sensor")

        if len(self.cpu_temp_history) > 60:
            self.cpu_temp_history.pop(0)

        self.temp_curve.setData(self.cpu_temp_history)

    def init_stacked_widget(self):
        while self.main_content.count():
            widget = self.main_content.widget(0)
            self.main_content.removeWidget(widget)
            widget.deleteLater()

        for menu in self.menu_list:
            text = menu.get("name")

            if text == "Summary":
                new_page = self.create_summary_page()

            elif text == "Health":
                new_page = self.create_health_page()
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