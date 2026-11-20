import sys
import platform
import winreg

import psutil
import pyqtgraph as pg
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QListWidgetItem, QWidget, QGridLayout,
    QVBoxLayout, QHBoxLayout, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QPushButton, QMessageBox, QAbstractItemView,
    QScrollArea
)

from main_sidebar_ui import Ui_MainWindow
from monitor import SystemMonitor


APP_NAME = "SystemoScope"


def fmt_bytes(value):
    value = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def make_table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    return table


def set_cell(table, row, column, value):
    table.setItem(row, column, QTableWidgetItem(str(value)))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.resize(1050, 700)
        self.setMinimumSize(900, 600)

        self.monitor = SystemMonitor()
        self.latest = {}
        self.cpu_history = []
        self.ram_history = []
        self.net_down_history = []
        self.net_up_history = []
        self.pages = {}
        self.health_cards = {}
        self.summary_cards = {}
        self.network_cards = {}
        self.performance_cards = {}

        self.title_label = self.ui.title_label
        self.title_label.setText(APP_NAME)
        title_font = self.title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(15)
        self.title_label.setFont(title_font)

        self.side_menu = self.ui.listWidget_2
        self.side_menu.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.side_menu_icon_only = self.ui.listWidget
        self.side_menu_icon_only.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.side_menu_icon_only.hide()

        self.menu_btn = self.ui.pushButton
        self.menu_btn.setText("☰")
        self.menu_btn.setFixedSize(32, 30)
        self.menu_btn.setCheckable(True)
        self.menu_btn.setChecked(False)

        self.main_content = self.ui.stackedWidget
        self.menu_list = [
            {"name": "Summary", "icon": "./icons/summary.svg"},
            {"name": "Health", "icon": "./icons/health.svg"},
            {"name": "Network", "icon": "./icons/network.svg"},
            {"name": "Performance", "icon": "./icons/performance.svg"},
            {"name": "Diagnostics", "icon": "./icons/diagnostics.svg"},
            {"name": "Software", "icon": "./icons/software.svg"},
        ]

        self._apply_style()
        self.init_list_widget()
        self.init_signal_slot()
        self.init_stacked_widget()
        self.refresh()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(30000)

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #202020;
                color: #eeeeee;
                font-family: "Segoe UI";
                font-size: 12px;
            }
            QLabel { background-color: transparent; border: none; }
            QFrame#title_frame {
                background-color: #252525;
                border: 0;
            }
            QListWidget {
                background-color: #252525;
                border: 0;
                color: #dddddd;
                outline: 0;
                padding: 5px;
            }
            QListWidget::item {
                min-height: 38px;
                padding: 5px;
                border-radius: 5px;
            }
            QListWidget::item:selected {
                background-color: #3a3a3a;
                color: white;
            }
            QPushButton {
                background-color: #383838;
                color: #eeeeee;
                border: 1px solid #505050;
                border-radius: 5px;
                padding: 7px 10px;
            }
            QPushButton:hover {
                background-color: #454545;
            }
            QLineEdit {
                background-color: #292929;
                color: white;
                border: 1px solid #484848;
                border-radius: 5px;
                padding: 8px;
            }
            QTableWidget {
                background-color: #252525;
                alternate-background-color: #2d2d2d;
                color: #eeeeee;
                gridline-color: #414141;
                border: 1px solid #414141;
                selection-background-color: #505050;
            }
            QHeaderView::section {
                background-color: #333333;
                color: #eeeeee;
                padding: 8px;
                border: 0;
            }
            QScrollArea {
                border: 0;
                background: transparent;
            }
        """)

    def init_signal_slot(self):
        self.menu_btn.toggled.connect(self.side_menu.setHidden)
        self.menu_btn.toggled.connect(self.title_label.setHidden)
        self.menu_btn.toggled.connect(self.side_menu_icon_only.setVisible)
        self.side_menu.currentRowChanged.connect(self.main_content.setCurrentIndex)
        self.side_menu_icon_only.currentRowChanged.connect(self.main_content.setCurrentIndex)
        self.side_menu.currentRowChanged.connect(self.side_menu_icon_only.setCurrentRow)
        self.side_menu_icon_only.currentRowChanged.connect(self.side_menu.setCurrentRow)

    def init_list_widget(self):
        self.side_menu.clear()
        self.side_menu_icon_only.clear()
        for menu in self.menu_list:
            item = QListWidgetItem()
            item.setIcon(QIcon(menu["icon"]))
            item.setSizeHint(QSize(40, 40))
            self.side_menu_icon_only.addItem(item)

            full_item = QListWidgetItem()
            full_item.setIcon(QIcon(menu["icon"]))
            full_item.setText(menu["name"])
            self.side_menu.addItem(full_item)
        self.side_menu.setCurrentRow(0)

    def _page(self, title, subtitle):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        heading = QLabel(title)
        heading.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        description = QLabel(subtitle)
        description.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        description.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(description)
        return page, layout

    def create_card(self, title, value, description):
        card = QFrame()
        card.setObjectName("infoCard")
        card.setMinimumHeight(125)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(7)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet("background: transparent; color: #aaaaaa; font-size: 12px;")
        value_label = QLabel(str(value))
        value_label.setWordWrap(True)
        value_label.setStyleSheet("background: transparent; color: white; font-size: 19px; font-weight: bold;")
        description_label = QLabel(str(description))
        description_label.setWordWrap(True)
        description_label.setStyleSheet("background: transparent; color: #888888; font-size: 11px;")

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
        card.value_label = value_label
        card.description_label = description_label
        return card

    def _add_cards(self, layout, definitions, target, columns=2):
        grid = QGridLayout()
        grid.setSpacing(12)
        for index, (key, title, value, description) in enumerate(definitions):
            card = self.create_card(title, value, description)
            target[key] = card
            grid.addWidget(card, index // columns, index % columns)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        layout.addLayout(grid)

    def create_summary_page(self):
        page, layout = self._page("Your PC at a glance", "A quick overview of your system.")
        info = self.monitor.static_info()
        definitions = [
            ("os", "OPERATING SYSTEM", info["os"], "Installed operating system"),
            ("cpu", "PROCESSOR", info["cpu"], f'{info["cores"]} cores / {info["threads"]} threads'),
            ("ram", "MEMORY", f'{info["ramsize"]} GB RAM', f'{info["ramused"]} GB used / {info["ramfree"]} GB available'),
            ("storage", "STORAGE", f'{info["disk"]} GB', f'{info["diskused"]} GB used / {info["diskfree"]} GB free (C:)'),
            ("device", "DEVICE", info["name"], f'Current user: {info["username"]}'),
            ("architecture", "ARCHITECTURE", info["architecture"], "System architecture"),
        ]
        self._add_cards(layout, definitions, self.summary_cards)
        layout.addStretch()
        return page

    def create_health_page(self):
        page, layout = self._page("System Health", "Monitor hardware condition and system resource usage.")
        definitions = [
            ("battery", "Battery status", "—", "Power information"),
            ("cpu_temp", "CPU temperature", "Unavailable", "CPU sensor"),
            ("gpu_temp", "GPU temperature", "Unavailable", "GPU sensor"),
            ("cooling", "Cooling", "Unavailable", "Fan speed sensors"),
            ("ram", "RAM usage", "—", "Memory utilization"),
            ("cpu", "CPU usage", "—", "Processor utilization"),
            ("disk", "Disk details", "—", "Storage usage"),
        ]
        self._add_cards(layout, definitions, self.health_cards, 3)

        note = QLabel(
            "Temperature and fan readings require hardware sensor support. On Windows, run "
            "LibreHardwareMonitor in the background (preferably as administrator). "
            "Unsupported readings are displayed as unavailable."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #999999; font-size: 11px;")
        layout.addWidget(note)

        self.temp_plot = pg.PlotWidget()
        self.temp_plot.setBackground("#292929")
        self.temp_plot.setTitle("CPU temperature history", color="#ffffff", size="11pt")
        self.temp_plot.setLabel("left", "Temperature (°C)", color="#aaaaaa")
        self.temp_plot.setLabel("bottom", "Recent samples", color="#aaaaaa")
        self.temp_plot.showGrid(x=True, y=True, alpha=0.2)
        self.temp_plot.setMinimumHeight(170)
        self.temp_curve = self.temp_plot.plot([], pen=pg.mkPen("#ff7777", width=2))
        layout.addWidget(self.temp_plot)
        return page

    def create_network_page(self):
        page, layout = self._page("Network", "Live network throughput and adapter information.")
        definitions = [
            ("download", "Download speed", "—", "Incoming network traffic"),
            ("upload", "Upload speed", "—", "Outgoing network traffic"),
            ("sent", "Data sent", "—", "Since system start"),
            ("received", "Data received", "—", "Since system start"),
        ]
        self._add_cards(layout, definitions, self.network_cards)
        self.network_plot = pg.PlotWidget()
        self.network_plot.setBackground("#292929")
        self.network_plot.setTitle("Network activity", color="#ffffff", size="11pt")
        self.network_plot.setLabel("left", "Bytes per second", color="#aaaaaa")
        self.network_plot.showGrid(x=True, y=True, alpha=0.2)
        self.network_down_curve = self.network_plot.plot([], pen=pg.mkPen("#65b5ff", width=2), name="Download")
        self.network_up_curve = self.network_plot.plot([], pen=pg.mkPen("#75d69c", width=2), name="Upload")
        layout.addWidget(self.network_plot, 1)
        self.adapter_table = make_table(["Adapter", "Status", "IP address", "Speed"])
        layout.addWidget(self.adapter_table)
        return page

    def create_performance_page(self):
        page, layout = self._page("Performance", "Track processor, memory, and running processes.")
        definitions = [
            ("cpu", "CPU usage", "—", "Total processor utilization"),
            ("ram", "RAM usage", "—", "Physical memory utilization"),
            ("swap", "Virtual memory", "—", "Swap usage"),
            ("processes", "Processes", "—", "Running processes"),
        ]
        self._add_cards(layout, definitions, self.performance_cards)
        self.performance_plot = pg.PlotWidget()
        self.performance_plot.setBackground("#292929")
        self.performance_plot.setTitle("CPU usage per logical processor", color="#ffffff", size="11pt")
        self.performance_plot.setLabel("left", "Usage (%)", color="#aaaaaa")
        self.performance_plot.showGrid(x=True, y=True, alpha=0.2)
        self.performance_plot.setYRange(0, 100)
        layout.addWidget(self.performance_plot, 1)
        self.core_curves = []
        self.process_table = make_table(["Process", "PID", "CPU %", "Memory", "User", "Status"])
        layout.addWidget(self.process_table, 2)
        return page

    def create_diagnostics_page(self):
        page, layout = self._page("Diagnostics", "Run basic checks and review detected hardware information.")
        run_button = QPushButton("Run diagnostics")
        run_button.clicked.connect(self.run_diagnostics)
        layout.addWidget(run_button)
        self.diagnostics_table = make_table(["Check", "Result", "Details"])
        layout.addWidget(self.diagnostics_table, 1)
        self.run_diagnostics()
        return page

    def create_software_page(self):
        page, layout = self._page("Installed software", "Browse applications registered in Windows.")
        search_row = QHBoxLayout()
        self.software_search = QLineEdit()
        self.software_search.setPlaceholderText("Search installed applications…")
        self.software_search.textChanged.connect(self.filter_software)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_software)
        search_row.addWidget(self.software_search, 1)
        search_row.addWidget(refresh_button)
        layout.addLayout(search_row)
        self.software_table = make_table(["Application", "Version", "Publisher", "Install date"])
        layout.addWidget(self.software_table, 1)
        self.software_rows = []
        self.load_software()
        return page

    def init_stacked_widget(self):
        while self.main_content.count():
            widget = self.main_content.widget(0)
            self.main_content.removeWidget(widget)
            widget.deleteLater()

        builders = [
            self.create_summary_page,
            self.create_health_page,
            self.create_network_page,
            self.create_performance_page,
            self.create_diagnostics_page,
            self.create_software_page,
        ]
        for builder in builders:
            page = builder()
            self.pages[builder.__name__] = page
            self.main_content.addWidget(page)

    def refresh(self):
        try:
            data = self.monitor.snapshot()
            self.latest = data
            self.update_summary(data)
            self.update_health(data)
            self.update_network(data)
            self.update_performance(data)
            self.update_temperature_plot(data)
        except Exception as error:
            self.ui.statusbar.showMessage(f"Monitoring update failed: {error}", 5000)

    def update_summary(self, data):
        self.summary_cards["ram"].value_label.setText(f'{data["ram_percent"]:.1f}%')
        self.summary_cards["ram"].description_label.setText(
            f'{fmt_bytes(data["ram_used"])} used / {fmt_bytes(data["ram_total"])} total'
        )
        system_disk = next((disk for disk in data["disks"] if disk["mount"].lower().startswith("c:")), None)
        if system_disk is None and data["disks"]:
            system_disk = data["disks"][0]
        if system_disk:
            self.summary_cards["storage"].value_label.setText(f'{system_disk["percent"]:.1f}% used')
            self.summary_cards["storage"].description_label.setText(
                f'{fmt_bytes(system_disk["free"])} free / {fmt_bytes(system_disk["total"])} total'
            )
        else:
            self.summary_cards["storage"].value_label.setText("Unavailable")
            self.summary_cards["storage"].description_label.setText("No accessible volumes")

    def update_health(self, data):
        battery = data["battery"]
        if battery["present"]:
            state = "Charging" if battery["plugged"] else "On battery"
            self._set_health("battery", f'{battery["percent"]:.0f}%', state)
        else:
            self._set_health("battery", "Not detected", "Battery information unavailable")

        self._set_health(
            "cpu_temp",
            f'{data["cpu_temp"]:.1f} °C' if data["cpu_temp"] is not None else "Unavailable",
            "CPU temperature sensor"
        )
        self._set_health(
            "gpu_temp",
            f'{data["gpu_temp"]:.1f} °C' if data["gpu_temp"] is not None else "Unavailable",
            "GPU temperature sensor"
        )
        if data["fans"]:
            fan_summary = " · ".join(f'{fan["name"]}: {fan["rpm"]:.0f} RPM' for fan in data["fans"][:3])
            self._set_health("cooling", f'{len(data["fans"])} fan(s)', fan_summary)
        else:
            self._set_health("cooling", "Unavailable", "No fan speed sensor exposed")

        self._set_health("ram", f'{data["ram_percent"]:.1f}%',
                         f'{fmt_bytes(data["ram_used"])} used / {fmt_bytes(data["ram_total"])}')
        self._set_health("cpu", f'{data["cpu"]:.1f}%', f'{len(data["per_cpu"])} logical processors')
        if data["disks"]:
            disk = max(data["disks"], key=lambda item: item["percent"])
            self._set_health("disk", f'{disk["percent"]:.1f}% used',
                             f'{disk["device"]} · {fmt_bytes(disk["free"])} free')
        else:
            self._set_health("disk", "Unavailable", "No accessible disk volumes")

    def _set_health(self, key, value, description):
        card = self.health_cards[key]
        card.value_label.setText(value)
        card.description_label.setText(description)

    def update_network(self, data):
        rates = data["net_rates"]
        self.network_cards["download"].value_label.setText(fmt_bytes(rates["recv"]) + "/s")
        self.network_cards["upload"].value_label.setText(fmt_bytes(rates["sent"]) + "/s")
        self.network_cards["sent"].value_label.setText(fmt_bytes(data["net_totals"]["sent"]))
        self.network_cards["received"].value_label.setText(fmt_bytes(data["net_totals"]["recv"]))
        self.net_down_history.append(rates["recv"])
        self.net_up_history.append(rates["sent"])
        self.net_down_history = self.net_down_history[-60:]
        self.net_up_history = self.net_up_history[-60:]
        self.network_down_curve.setData(self.net_down_history)
        self.network_up_curve.setData(self.net_up_history)

        adapters = data["network_adapters"]
        self.adapter_table.setSortingEnabled(False)
        self.adapter_table.setRowCount(len(adapters))
        for row, adapter in enumerate(adapters):
            for col, value in enumerate(adapter):
                set_cell(self.adapter_table, row, col, value)
        self.adapter_table.setSortingEnabled(True)

    def update_performance(self, data):
        self.performance_cards["cpu"].value_label.setText(f'{data["cpu"]:.1f}%')
        self.performance_cards["ram"].value_label.setText(f'{data["ram_percent"]:.1f}%')
        self.performance_cards["swap"].value_label.setText(f'{data["swap_percent"]:.1f}%')
        self.performance_cards["processes"].value_label.setText(str(data["process_count"]))

        for curve in self.core_curves:
            self.performance_plot.removeItem(curve)
        self.core_curves = []
        for index, value in enumerate(data["per_cpu"]):
            curve = self.performance_plot.plot([index, index + 1], [value, value],
                                               pen=pg.mkPen(pg.intColor(index), width=5))
            self.core_curves.append(curve)

        processes = data["processes"]
        self.process_table.setSortingEnabled(False)
        self.process_table.setRowCount(min(len(processes), 20))
        for row, process in enumerate(processes[:20]):
            values = [
                process["name"], process["pid"], f'{process["cpu"]:.1f}%',
                fmt_bytes(process["memory"]), process["user"], process["status"]
            ]
            for col, value in enumerate(values):
                set_cell(self.process_table, row, col, value)
        self.process_table.setSortingEnabled(True)

    def update_temperature_plot(self, data):
        if data["cpu_temp"] is None:
            self.temp_curve.setData([])
            return
        self.cpu_history.append(data["cpu_temp"])
        self.cpu_history = self.cpu_history[-60:]
        self.temp_curve.setData(self.cpu_history)

    def run_diagnostics(self):
        checks = []
        try:
            checks.append(("CPU", "Passed", f'{psutil.cpu_count(logical=False)} physical / {psutil.cpu_count()} logical cores'))
        except Exception as error:
            checks.append(("CPU", "Unavailable", str(error)))
        try:
            memory = psutil.virtual_memory()
            checks.append(("Memory", "Passed", f'{fmt_bytes(memory.total)} installed'))
        except Exception as error:
            checks.append(("Memory", "Unavailable", str(error)))
        try:
            disks = psutil.disk_partitions()
            checks.append(("Storage", "Passed" if disks else "Warning", f'{len(disks)} mounted volume(s)'))
        except Exception as error:
            checks.append(("Storage", "Unavailable", str(error)))
        try:
            battery = psutil.sensors_battery()
            checks.append(("Battery", "Detected" if battery else "Not detected",
                           f'{battery.percent:.0f}% charge' if battery else "No battery reported by the OS"))
        except Exception as error:
            checks.append(("Battery", "Unavailable", str(error)))
        try:
            temp = self.monitor.snapshot()["cpu_temp"]
            checks.append(("CPU temperature", "Detected" if temp is not None else "Unavailable",
                           f'{temp:.1f} °C' if temp is not None else "No supported sensor found"))
        except Exception as error:
            checks.append(("CPU temperature", "Unavailable", str(error)))

        self.diagnostics_table.setRowCount(len(checks))
        for row, values in enumerate(checks):
            for col, value in enumerate(values):
                set_cell(self.diagnostics_table, row, col, value)

    def load_software(self):
        self.software_rows = []
        if sys.platform == "win32":
            locations = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            ]
            for hive, path in locations:
                try:
                    with winreg.OpenKey(hive, path) as root:
                        count = winreg.QueryInfoKey(root)[0]
                        for index in range(count):
                            try:
                                subkey_name = winreg.EnumKey(root, index)
                                with winreg.OpenKey(root, subkey_name) as app:
                                    def read_value(name):
                                        try:
                                            return winreg.QueryValueEx(app, name)[0]
                                        except OSError:
                                            return ""
                                    name = read_value("DisplayName")
                                    if name and not read_value("SystemComponent"):
                                        self.software_rows.append((
                                            str(name), str(read_value("DisplayVersion") or "—"),
                                            str(read_value("Publisher") or "—"),
                                            str(read_value("InstallDate") or "—")
                                        ))
                            except OSError:
                                continue
                except OSError:
                    continue
        self.software_rows = sorted(set(self.software_rows), key=lambda item: item[0].lower())
        self.filter_software()

    def filter_software(self):
        if not hasattr(self, "software_table"):
            return
        query = self.software_search.text().lower().strip()
        rows = [item for item in self.software_rows if query in " ".join(item).lower()]
        self.software_table.setSortingEnabled(False)
        self.software_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                set_cell(self.software_table, row, col, value)
        self.software_table.setSortingEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
