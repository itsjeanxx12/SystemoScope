import psutil
import platform

def get_username():
    return psutil.Process().username().split("\\")[1]

def get_system_usage():
    return {
        "cpu":psutil.cpu_percent(interval=1),
        "ram":psutil.virtual_memory().percent,
        "disk":psutil.disk_usage("C:\\").percent
    }

def get_system_info():
    return {
        "os":platform.system() + " " + platform.release(),
        "cpu":platform.processor(),
        "ramsize":psutil.virtual_memory().total / (1024 ** 3),
        "name": psutil.Process().username().split("\\")[0]
    }