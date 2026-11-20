# SystemoScope

SystemoScope is a lightweight Windows desktop system monitor built with Python and PySide6. It gives you a quick view of your computer's resources, hardware sensors, network activity, running processes, and installed applications.

## Features

- **Summary** — operating system, processor, memory, storage, and device overview.
- **Health** — battery status and health (when exposed by Windows), CPU/GPU temperatures, fan speeds, RAM, CPU, disk usage, and CPU temperature history.
- **Network** — live upload/download rates, total traffic, and network adapter information.
- **Performance** — CPU usage per logical processor, memory and swap usage, and a live process list.
- **Diagnostics** — basic checks for CPU, memory, storage, battery, and temperature sensor availability.
- **Software** — installed applications registered in Windows, with search.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- The packages listed in `requirements.txt`

## Installation

Clone the repository:

```bash
git clone https://github.com/itsjeanxx12/SystemoScope.git
cd SystemoScope
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run:

```bash
python main.py
```

## Hardware sensor notes

Windows does not expose every laptop's CPU temperature, GPU temperature, or fan speed through standard system APIs. For those readings, run **LibreHardwareMonitor** in the background. SystemoScope reads its local HTTP JSON endpoint at `http://127.0.0.1:8085/data.json`. In LibreHardwareMonitor, open **Options → Remote Web Server → Run** and keep it running while using SystemoScope. Some systems may require running LibreHardwareMonitor with administrator permissions.

NVIDIA GPU temperature can also be read through NVML when a supported NVIDIA driver is installed. If a sensor is not available, SystemoScope displays **Unavailable** instead of estimating a value.

Battery health depends on the battery information exposed by the laptop firmware and Windows.

## Bundling LibreHardwareMonitor

SystemoScope can use [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) to read hardware sensors that Windows does not expose through standard APIs, including CPU/GPU temperatures and fan speeds.

For a portable release, you can distribute LibreHardwareMonitor alongside SystemoScope:

```text
SystemoScope/
├── SystemoScope.exe
└── LibreHardwareMonitor/
    ├── LibreHardwareMonitor.exe
    └── other files from the official release
```

Use the complete contents of an official LibreHardwareMonitor release rather than copying only its executable. Users should run LibreHardwareMonitor with the permissions needed for their hardware sensors, then launch SystemoScope. Sensor availability still depends on the computer and its drivers.

LibreHardwareMonitor is a separate third-party project and is not included in the Python application itself. When redistributing it, include its applicable license and third-party notices, retain required copyright notices, and follow the [Mozilla Public License 2.0](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/blob/master/LICENSE) and any other applicable license terms. Check the license files included with the exact release you distribute.

## Built with

- Python
- PySide6
- psutil
- PyQtGraph
- WMI / LibreHardwareMonitor sensor interface
