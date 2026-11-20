import sys
from datetime import timedelta

import psutil
import pyqtgraph as pg
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QLineEdit, QMessageBox,
    QAbstractItemView, QScrollArea, QSizePolicy
)

from monitor import SystemMonitor


APP_STYLE = """"Q"M"ainWindow, QWidget { background: #0b1020; color: #e6eaf2; font-family: "Segoe UI"; font-size: 13px; }
QFrame#Sidebar { background: #0e1528; border-right: 1px solid #202b43; }
QLabel#Brand { font-size: 22px; font-weight: 750; color: #f4f7ff; padding: 8px 4px 22px; }
QLabel#Muted { color: #8c9ab5; }
QLabel#PageTitle { font-size: 25px; font-weight: 700; color: #f4f7ff; }
QLabel#CardTitle { color: #91a0bb; font-size: 12px; font-weight: 600; }
QLabel#Metric { color: #f5f7fc; font-size: 27px; font-weight: 700; }
QLabel#SubMetric { color: #8c9ab5; font-size: 11px; }
QFrame#Card { background: #121b30; border: 1px solid #202d48; border-radius: 12px; }
QPushButton#Nav { text-align: left; padding: 12px 14px; border: 0; border-radius: 8px; color: #9eabc3; background: transparent; font-weight: 600; }
QPushButton#Nav:hover { background: #17243d; color: #ffffff; }
QPushButton#Nav[active="true"] { background: #20375f; color: #ffffff; }
QPushButton#Action { background: #243c66; border: 1px solid #355787; border-radius: 7px; padding: 8px 12px; color: white; }
QPushButton#Action:hover { background: #2e4c7d; }
QLineEdit { background: #0c1426; border: 1px solid #263550; border-radius: 7px; padding: 9px; color: #e6eaf2; }
QTableWidget { background: #10192c; alternate-background-color: #131f35; border: 1px solid #24314a; border-radius: 8px; gridline-color: #202d43; selection-background-color: #294875; }
QHeaderView::section { background: #17243b; color: #aebbd0; border: 0; padding: 9px; font-weight: 600; }
QProgressBar { background: #0a1222; border: 0; border-radius: 4px; height: 8px; text-align: center; }
QProgressBar::chunk { background: #5b9cf0; border-radius: 4px; }
QScrollArea { border: 0; }
"""

def fmt_bytes(value):
    value = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"

def metric_card(title, value="—", subtitle="", parent=None):
    card = QFrame()
    card.setObjectName("Card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(7)
    name = QLabel(title.upper())
    name.setObjectName("CardTitle")
    val = QLabel(str(value))
    val.setObjectName("Metric")
    sub = QLabel(subtitle)
    sub.setObjectName("SubMetric")
    sub.setWordWrap(True)
    layout.addWidget(name)
    layout.addWidget(val)
    layout.addWidget(sub)
    card.value_label = val
    card.sub_label = sub
    return card

def make_table(headers):
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSortingEnabled(True)
    return table

def put(table, row, col, value):
    item = QTableWidgetItem(str(value))
    if col > 0:
        item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    table.setItem(row, col, item)

class SystemScope(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SystemScope")
        self.resize(1280, 820)
        self.setMinimumSize(980, 650)
        self.monitor = SystemMonitor()
        self.latest = {}
        self.cpu_history = []
        self.ram_history = []
        self.process_rows = []
        self.pages = {}
        self.nav_buttons = {}
        self._build_ui()
        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

    def _build_ui(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 22, 16, 18)
        side.setSpacing(7)
        brand = QLabel("SystemScope")
        brand.setObjectName("Brand")
        side.addWidget(brand)
        section_label = QLabel("SYSTEM MONITOR")
        section_label.setObjectName("Muted")
        side.addWidget(section_label)
        for key, label in [
            ("Overview", "◈   Overview"),
            ("Health", "♡   Health"),
            ("Processes", "▤   Processes"),
            ("Storage", "▧   Storage"),
            ("System", "⚙   System info"),
        ]:
            button = QPushButton(label)
            button.setObjectName("Nav")
            button.setProperty("active", key == "Overview")
            button.clicked.connect(lambda checked=False, name=key: self.show_page(name))
            side.addWidget(button)
            self.nav_buttons[key] = button
        side.addStretch()
        self.status_label = QLabel("● Monitoring active")
        self.status_label.setObjectName("Muted")
        side.addWidget(self.status_label)
        update_label = QLabel("Updates every 2 seconds")
        update_label.setObjectName("Muted")
        side.addWidget(update_label)

        self.stack = QStackedWidget()
        for name, builder in [
            ("Overview", self._overview_page),
            ("Health", self._health_page),
            ("Processes", self._process_page),
            ("Storage", self._storage_page),
            ("System", self._system_page),
        ]:
            page = builder()
            self.pages[name] = page
            self.stack.addWidget(page)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

    def _page_shell(self, title, description):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 25, 28, 24)
        layout.setSpacing(16)
        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        desc = QLabel(description)
        desc.setObjectName("Muted")
        layout.addWidget(heading)
        layout.addWidget(desc)
        return page, layout

    def _overview_page(self):
        page, layout = self._page_shell("Overview", "A live snapshot of your computer.")
        grid = QGridLayout()
        grid.setSpacing(12)
        self.overview_cards = {}
        for i, (key, title, sub) in enumerate([
            ("cpu", "CPU usage", "Processor utilization"),
            ("ram", "RAM usage", "Memory in use"),
            ("processes", "Processes", "Running processes"),
            ("battery", "Battery", "Power status"),
        ]):
            card = metric_card(title, "—", sub)
            self.overview_cards[key] = card
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid)
        chart_grid = QGridLayout()
        chart_grid.setSpacing(12)
        self.cpu_plot = self._make_plot("CPU usage", "%")
        self.ram_plot = self._make_plot("Memory usage", "%")
        chart_grid.addWidget(self.cpu_plot, 0, 0)
        chart_grid.addWidget(self.ram_plot, 0, 1)
        layout.addLayout(chart_grid, 1)
        self.network_label = QLabel("Network: waiting for data…")
        self.network_label.setObjectName("Muted")
        layout.addWidget(self.network_label)
        return page

    def _make_plot(self, title, unit):
        plot = pg.PlotWidget()
        plot.setBackground("#121b30")
        plot.setTitle(title, color="#e6eaf2", size="12pt")
        plot.showGrid(x=True, y=True, alpha=0.2)
        plot.setYRange(0, 100)
        plot.setLabel("left", unit)
        plot.getAxis("bottom").setStyle(showValues=False)
        plot.getAxis("left").setTextPen("#8c9ab5")
        plot.getAxis("bottom").setTextPen("#8c9ab5")
        plot.getPlotItem().getViewBox().setBorder(pg.mkPen("#263550"))
        return plot

    def _health_page(self):
        page, layout = self._page_shell("Health", "Hardware condition and live resource usage.")
        grid = QGridLayout()
        grid.setSpacing(12)
        self.health_cards = {}
        cards = [
            ("battery", "Battery status"),
            ("cpu_temp", "CPU temperature"),
            ("gpu_temp", "GPU temperature"),
            ("cooling", "Cooling"),
            ("ram", "RAM usage"),
            ("cpu", "CPU usage"),
            ("disk", "Disk details"),
        ]
        for index, (key, title) in enumerate(cards):
            card = metric_card(title, "—", "Waiting for sensor data")
            self.health_cards[key] = card
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)
        note = QLabel(
            "Temperature and fan readings depend on hardware support. On Windows, install and run "
            "LibreHardwareMonitor as administrator for CPU/GPU temperatures and fan speeds. "
            "Unsupported sensors are shown as unavailable rather than guessed."
        )
        note.setObjectName("Muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        return page

    def _process_page(self):
        page, layout = self._page_shell("Processes", "Inspect running processes and their resource usage.")
        bar = QHBoxLayout()
        self.process_search = QLineEdit()
        self.process_search.setPlaceholderText("Search by process name or PID…")
        self.process_search.textChanged.connect(self._filter_processes)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("Action")
        refresh_btn.clicked.connect(self.refresh_processes)
        end_btn = QPushButton("End selected process")
        end_btn.setObjectName("Action")
        end_btn.clicked.connect(self.end_process)
        bar.addWidget(self.process_search, 1)
        bar.addWidget(refresh_btn)
        bar.addWidget(end_btn)
        layout.addLayout(bar)
        self.process_table = make_table(["Process", "PID", "CPU %", "Memory", "User", "Status"])
        layout.addWidget(self.process_table, 1)
        warning = QLabel("Ending a process can cause unsaved work to be lost. Protected processes may not be accessible.")
        warning.setObjectName("Muted")
        layout.addWidget(warning)
        return page

    def _storage_page(self):
        page, layout = self._page_shell("Storage", "Disk capacity and activity.")
        self.storage_cards = {}
        grid = QGridLayout()
        for i, key in enumerate(("read", "write")):
            card = metric_card("Total bytes " + key, "—", "Since system start")
            self.storage_cards[key] = card
            grid.addWidget(card, 0, i)
        layout.addLayout(grid)
        self.disk_table = make_table(["Drive", "Mount point", "File system", "Used", "Free", "Capacity", "Usage"])
        layout.addWidget(self.disk_table, 1)
        return page

    def _system_page(self):
        page, layout = self._page_shell("System information", "Hardware and operating system details.")
        self.system_table = make_table(["Property", "Value"])
        self.system_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.system_table)
        return page

    def show_page(self, name):
        self.stack.setCurrentWidget(self.pages[name])
        for key, button in self.nav_buttons.items():
            button.setProperty("active", key == name)
            button.style().unpolish(button)
            button.style().polish(button)
        if name == "Processes":
            self.refresh_processes()

    def refresh(self):
        try:
            data = self.monitor.snapshot()
            self.latest = data
            self._update_overview(data)
            self._update_health(data)
            self._update_storage(data)
            self._update_system(data)
            self.status_label.setText("● Monitoring active")
        except Exception as error:
            self.status_label.setText("● Monitoring error")
            print("SystemScope refresh error:", error)

    def _update_overview(self, data):
        self.overview_cards["cpu"].value_label.setText(f'{data["cpu"]:.1f}%')
        self.overview_cards["ram"].value_label.setText(f'{data["ram_percent"]:.1f}%')
        self.overview_cards["ram"].sub_label.setText(
            f'{fmt_bytes(data["ram_used"])} of {fmt_bytes(data["ram_total"])}'
        )
        self.overview_cards["processes"].value_label.setText(str(data["process_count"]))
        battery = data["battery"]
        self.overview_cards["battery"].value_label.setText(
            f'{battery["percent"]:.0f}%' if battery["present"] else "No battery"
        )
        self.overview_cards["battery"].sub_label.setText(
            "Charging" if battery["plugged"] else "On battery" if battery["present"] else "Desktop / unavailable"
        )
        self.cpu_history.append(data["cpu"])
        self.ram_history.append(data["ram_percent"])
        self.cpu_history = self.cpu_history[-60:]
        self.ram_history = self.ram_history[-60:]
        self.cpu_plot.clear()
        self.ram_plot.clear()
        self.cpu_plot.plot(self.cpu_history, pen=pg.mkPen("#65a9ff", width=2))
        self.ram_plot.plot(self.ram_history, pen=pg.mkPen("#6dd6b0", width=2))
        rates = data["net_rates"]
        self.network_label.setText(
            f'Network  ↓ {fmt_bytes(rates["recv"])}/s     ↑ {fmt_bytes(rates["sent"])}/s'
        )

    def _update_health(self, data):
        battery = data["battery"]
        if battery["present"]:
            status = "Charging" if battery["plugged"] else "Discharging"
            health = f' · {battery["health"]:.0f}% health' if battery["health"] is not None else ""
            self._set_card("battery", f'{battery["percent"]:.0f}%', status set_card("battery", "Not detected", "Battery information unavailable")

        self._set_card("cpu_temp", f'{data["cpu_temp"]:.1f} °C' if data["cpu_temp"] is not None else "Unavailable",
                       "CPU package / core sensor")
        self._set_card("gpu_temp", f'{data["gpu_temp"]:.1f} °C' if data["gpu_temp"] is not None else "Unavailable",
                       "GPU temperature sensor")
        if data["fans"]:
            fan_text = " · ".join(f'{fan["name"]}: {fan["rpm"]:.0f} RPM' for fan in data["fans"][:3])
            self._set_card("cooling", f'{len(data["fans"])} fan sensor(s)', fan_text)
        else:
            self._set_card("cooling", "Unavailable", "Fan RPM sensor not exposed")
        self._set_card("ram", f'{data["ram_percent"]:.1f}%',
                       f'{fmt_bytes(data["ram_used"])} used / {fmt_bytes(data["ram_total"])} total')
        self._set_card("cpu", f'{data["cpu"]:.1f}%', f'{len(data["per_cpu"])} logical processors')
        disks = data["disks"]
        if disks:
            most_full = max(disks, key=lambda item: item["percent"])
            self._set_card("disk", f'{most_full["percent"]:.0f}% used',
                           f'{most_full["device"]} · {fmt_bytes(most_full["free"])} free')
        else:
            self._set_card("disk", "Unavailable", "No accessible disk volumes")

    def _set_card(self, key, value, subtitle):
        self.health_cards[key].value_label.setText(value)
        self.health_cards[key].sub_label.setText(subtitle)

    def _update_storage(self, data):
        io = data["disk_io"]
        self.storage_cards["read"].value_label.setText(fmt_bytes(io["read"]))
        self.storage_cards["write"].value_label.setText(fmt_bytes(io["write"]))
        table = self.disk_table
        table.setSortingEnabled(False)
        table.setRowCount(len(data["disks"]))
        for row, disk in enumerate(data["disks"]):
            values = [
                disk["device"], disk["mount"], disk["filesystem"],
                fmt_bytes(disk["used"]), fmt_bytes(disk["free"]),
                fmt_bytes(disk["total"]), f'{disk["percent"]:.1f}%'
            ]
            for col, value in enumerate(values):
                put(table, row, col, value)
        table.setSortingEnabled(True)

    def _update_system(self, data):
        info = data["system"]
        values = [
            ("Computer name", info["computer"]),
            ("Operating system", info["os"]),
            ("OS version", info["version"]),
            ("Architecture", info["architecture"]),
            ("Processor", info["processor"]),
            ("Physical cores", info["physical_cores"]),
            ("Logical processors", info["logical_cores"]),
            ("Python version", info["python"]),
            ("Last boot", info["boot"]),
        ]
        self.system_table.setRowCount(len(values))
        for row, (key, value) in enumerate(values):
            put(self.system_table, row, 0, key)
            put(self.system_table, row, 1, value)

    def refresh_processes(self):
        try:
            self.process_rows = self.monitor.processes()
            self._filter_processes()
        except Exception as error:
            print("Process refresh error:", error)

    def _filter_processes(self):
        if not hasattr(self, "process_table"):
            return
        query = self.process_search.text().lower().strip()
        rows = [
            proc for proc in self.process_rows
            if query in proc["name"].lower() or query in str(proc["pid"])
        ]
        table = self.process_table
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for row, proc in enumerate(rows):
            values = [
                proc["name"], proc["pid"], f'{proc["cpu"]:.1f}%',
                fmt_bytes(proc["memory"]), proc["user"], proc["status"]
            ]
            for col, value in enumerate(values):
                put(table, row, col, value)
        table.setSortingEnabled(True)

    def end_process(self):
        row = self.process_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select a process", "Select a process first.")
            return
        pid_item = self.process_table.item(row, 1)
        name_item = self.process_table.item(row, 0)
        if not pid_item:
            return
        pid = int(pid_item.text())
        answer = QMessageBox.warning(
            self, "End process",
            f'End "{name_item.text()}" (PID {pid})? Unsaved work may be lost.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            psutil.Process(pid).terminate()
            QMessageBox.information(self, "Process ended", f"Termination requested for PID {pid}.")
            self.refresh_processes()
        except psutil.AccessDenied:
            QMessageBox.warning(self, "Access denied", "Windows denied access. Try running SystemScope with appropriate permissions.")
        except psutil.NoSuchProcess:
            QMessageBox.information(self, "Already closed", "That process has already exited.")
        except Exception as error:
            QMessageBox.warning(self, "Could not end process", str(error))

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SystemScope")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(APP_STYLE)
    window = SystemScope()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

