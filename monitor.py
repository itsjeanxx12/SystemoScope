import psutil
import platform
import getpass


def get_username():
    return getpass.getuser()


def get_system_usage():
    return {
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("C:\\").percent
    }


def get_system_info():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")

    return {
        "os": platform.system() + " " + platform.release(),
        "cpu": platform.processor() or "Unknown",
        "ramsize": round(memory.total / (1024 ** 3)),
        "ramused": round(memory.used / (1024 ** 3), 1),
        "ramfree": round(memory.available / (1024 ** 3), 1),
        "disk": round(disk.total / (1024 ** 3)),
        "diskused": round(disk.used / (1024 ** 3)),
        "diskfree": round(disk.free / (1024 ** 3)),
        "name": platform.node(),
        "username": get_username(),
        "architecture": platform.machine(),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True)
    }