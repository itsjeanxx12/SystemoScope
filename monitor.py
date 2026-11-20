import os
import platform
import socket
import getpass
import subprocess
import time
from datetime import datetime

import psutil


def _run_powershell(command, timeout=4):
    if os.name != "nt":
        return ""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True, text=True, timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _hardware_sensors():
    result = {"cpu_temp": None, "gpu_temp": None, "fans": []}
    try:
        import wmi
        for namespace in (r"root\LibreHardwareMonitor", r"root\OpenHardwareMonitor"):
            try:
                client = wmi.WMI(namespace=namespace)
                for sensor in client.Sensor():
                    kind = str(getattr(sensor, "SensorType", "")).lower()
                    name = str(getattr(sensor, "Name", ""))
                    value = getattr(sensor, "Value", None)
                    if value is None:
                        continue
                    value = float(value)
                    label = name.lower()
                    if kind == "temperature":
                        if "cpu" in label and result["cpu_temp"] is None:
                            result["cpu_temp"] = value
                        elif "gpu" in label and result["gpu_temp"] is None:
                            result["gpu_temp"] = value
                    elif kind == "fan":
                        result["fans"].append({"name": name, "rpm": value})
                if result["cpu_temp"] is not None or result["gpu_temp"] is not None or result["fans"]:
                    break
            except Exception:
                continue
    except Exception:
        pass

    if result["gpu_temp"] is None:
        try:
            import pynvml
            pynvml.nvmlInit()
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                result["gpu_temp"] = float(
                    pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                )
            finally:
                pynvml.nvmlShutdown()
        except Exception:
            pass
    return result


def _battery_details():
    try:
        battery = psutil.sensors_battery()
    except Exception:
        battery = None
    data = {
        "present": battery is not None,
        "percent": round(battery.percent, 1) if battery else None,
        "plugged": battery.power_plugged if battery else None,
        "seconds_left": battery.secsleft if battery else None,
        "health": None,
        "design_capacity": None,
        "full_capacity": None,
    }
    if os.name == "nt":
        design_output = _run_powershell(
            "Get-CimInstance -Namespace root\\wmi -ClassName BatteryStaticData -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 -ExpandProperty DesignedCapacity"
        )
        full_output = _run_powershell(
            "Get-CimInstance -Namespace root\\wmi -ClassName BatteryFullChargedCapacity -ErrorAction SilentlyContinue | "
            "Select-Object -First 1 -ExpandProperty FullChargedCapacity"
        )
        try:
            design = int(design_output)
            charged = int(full_output)
            if design > 0 and charged > 0:
                data["design_capacity"] = design
                data["full_capacity"] = charged
                data["health"] = round(charged / design * 100, 1)
        except (TypeError, ValueError):
            pass
    return data


def _disk_details():
    disks = []
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in part.opts.lower():
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mount": part.mountpoint,
                "filesystem": part.fstype or "Unknown",
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except (PermissionError, OSError):
            continue
    io = psutil.disk_io_counters()
    io_data = {
        "read": io.read_bytes if io else 0,
        "write": io.write_bytes if io else 0,
        "read_count": io.read_count if io else 0,
        "write_count": io.write_count if io else 0,
    }
    return disks, io_data


def _network_adapters():
    adapters = []
    addresses = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for name, entries in addresses.items():
        state = stats.get(name)
        ipv4 = next((entry.address for entry in entries if entry.family == socket.AF_INET), "—")
        if ipv4.startswith("127."):
            continue
        adapters.append((
            name,
            "Up" if state and state.isup else "Down",
            ipv4,
            f"{state.speed} Mbps" if state and state.speed else "Unknown"
        ))
    return adapters


def _system_details():
    uname = platform.uname()
    try:
        boot = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
    except Exception:
        boot = "Unavailable"
    processor = platform.processor()
    if os.name == "nt":
        processor_name = _run_powershell(
            "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)"
        )
        if processor_name:
            processor = processor_name
    return {
        "computer": platform.node(),
        "os": f"{uname.system} {uname.release}",
        "version": platform.version(),
        "architecture": platform.machine(),
        "processor": processor or "Unavailable",
        "python": platform.python_version(),
        "boot": boot,
        "physical_cores": psutil.cpu_count(logical=False) or "Unknown",
        "logical_cores": psutil.cpu_count(logical=True) or "Unknown",
    }


class SystemMonitor:
    def __init__(self):
        self._last_net = psutil.net_io_counters()
        self._last_time = time.monotonic()
        self._system_cache = _system_details()
        psutil.cpu_percent(interval=None)
        for process in psutil.process_iter():
            try:
                process.cpu_percent(None)
            except (psutil.Error, OSError):
                pass

    def static_info(self):
        info = self._system_cache
        memory = psutil.virtual_memory()
        try:
            disk = psutil.disk_usage(os.environ.get("SystemDrive", "C:") + os.sep)
        except Exception:
            disk = None
        return {
            "os": info["os"],
            "cpu": info["processor"],
            "cores": info["physical_cores"],
            "threads": info["logical_cores"],
            "ramsize": round(memory.total / (1024 ** 3), 1),
            "ramused": round(memory.used / (1024 ** 3), 1),
            "ramfree": round(memory.available / (1024 ** 3), 1),
            "disk": round(disk.total / (1024 ** 3), 1) if disk else "N/A",
            "diskused": round(disk.used / (1024 ** 3), 1) if disk else "N/A",
            "diskfree": round(disk.free / (1024 ** 3), 1) if disk else "N/A",
            "name": info["computer"],
            "username": getpass.getuser(),
            "architecture": info["architecture"],
        }

    def snapshot(self):
        now = time.monotonic()
        elapsed = max(now - self._last_time, 0.001)
        cpu = psutil.cpu_percent(interval=None)
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        battery = _battery_details()
        sensors = _hardware_sensors()
        disks, disk_io = _disk_details()
        net = psutil.net_io_counters()
        net_rates = {
            "sent": max(0, net.bytes_sent - self._last_net.bytes_sent) / elapsed if net and self._last_net else 0,
            "recv": max(0, net.bytes_recv - self._last_net.bytes_recv) / elapsed if net and self._last_net else 0,
        }
        self._last_net = net
        self._last_time = now
        processes = self.processes()
        return {
            "time": datetime.now().strftime("%H:%M:%S"),
            "cpu": cpu,
            "per_cpu": per_cpu,
            "cpu_temp": sensors["cpu_temp"],
            "gpu_temp": sensors["gpu_temp"],
            "fans": sensors["fans"],
            "ram_percent": memory.percent,
            "ram_used": memory.used,
            "ram_total": memory.total,
            "ram_available": memory.available,
            "swap_percent": swap.percent,
            "battery": battery,
            "disks": disks,
            "disk_io": disk_io,
            "process_count": len(psutil.pids()),
            "processes": processes,
            "net_rates": net_rates,
            "net_totals": {
                "sent": net.bytes_sent if net else 0,
                "recv": net.bytes_recv if net else 0,
            },
            "network_adapters": _network_adapters(),
            "system": self._system_cache,
        }

    @staticmethod
    def processes():
        rows = []
        for process in psutil.process_iter(["pid", "name", "username", "memory_info", "status"]):
            try:
                info = process.info
                rows.append({
                    "pid": info.get("pid"),
                    "name": info.get("name") or "Unknown",
                    "user": (info.get("username") or "").split("\\")[-1],
                    "memory": info["memory_info"].rss if info.get("memory_info") else 0,
                    "status": info.get("status") or "Unknown",
                    "cpu": process.cpu_percent(None),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, OSError):
                continue
        return sorted(rows, key=lambda item: item["cpu"], reverse=True)
