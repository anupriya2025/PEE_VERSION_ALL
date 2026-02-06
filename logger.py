import os
import sys
import json
import psutil
import logging
import inspect 
import platform
import GPUtil
from datetime import datetime, timedelta
from config import ConfigLoader
from logging.handlers import TimedRotatingFileHandler

class CustomFormatter(logging.Formatter):
    """Formats logs with class/function/line metadata."""
    def format(self, record):
        try:
            frame = next(
                f for f in inspect.stack()[1:]
                if "logging" not in f.filename
            )
            obj = frame.frame.f_locals.get("self", None)
            record.class_name = obj.__class__.__name__ if obj else "None"
        except Exception:
            record.class_name = "Unknown"
        return super().format(record)


class LoggerUtility:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False   # << FIX
        return cls._instance

    def __init__(self):
        if self._initialized:   # clean and safe
            return

        # Load config, setup logging parameters
        self.config = ConfigLoader()
        self.app_name = "PPE"
        path=self.config.get("MAIN.log_path")
        self.log_dir = path
        log_level_str = 'INFO'.upper()
        self.log_level = getattr(logging, log_level_str, logging.INFO)

        self.log_type = 'low'
        self.backup_count = 15
        self.console_output = False
        os.makedirs(self.log_dir, exist_ok=True)
        self._setup_logging()
        # self._log_system_info()
        self._initialized = True

    def get_log_file(self):
        return os.path.join(self.log_dir, f"{self.app_name}.log")

    def _setup_logging(self):
        root = logging.getLogger()
        root.setLevel(self.log_level)
        root.handlers.clear()

        file_handler = TimedRotatingFileHandler(
            filename=self.get_log_file(),
            when="midnight",
            interval=1,
            backupCount=self.backup_count,
            utc=False
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(CustomFormatter(
            '%(asctime)s | %(levelname)s | %(name)s |C:F| %(class_name)s : %(funcName)s : %(lineno)-4d |T| %(threadName)s | %(message)s',
            datefmt='%d-%m-%Y %H:%M:%S'
        ))
        root.addHandler(file_handler)

        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(CustomFormatter('%(asctime)s | %(levelname)-8s | %(message)s'))
            root.addHandler(console_handler)

        logger = logging.getLogger(__name__)
        logger.info("Logger initialized with 30MB size limit")
        next_rotation = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        logger.info(f"Next log rotation at: {next_rotation}")



    def _log_system_info(self):
        logger = logging.getLogger(__name__)

        # System info
        system = platform.system()
        platform_info = platform.platform()
        python_version = platform.python_version()
        processor = platform.processor()
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # GPU info
        gpus = GPUtil.getGPUs()
        gpu_info_list = []
        for gpu in gpus:
            gpu_info_list.append({
                "id": gpu.id,
                "name": gpu.name,
                "load": f"{gpu.load * 100:.1f}%",
                "memory_total": f"{gpu.memoryTotal}MB",
                "memory_used": f"{gpu.memoryUsed}MB",
                "temperature": f"{gpu.temperature} °C"
            })

        info = {
            "System": system,
            "Platform": platform_info,
            "Python Version": python_version,
            "Processor": processor,
            "Total Memory (GB)": f"{memory.total / (1024 ** 3):.2f}",
            "Available Memory (GB)": f"{memory.available / (1024 ** 3):.2f}",
            "Memory Usage (%)": f"{memory.percent}%",
            "Disk Total (GB)": f"{disk.total / (1024 ** 3):.2f}",
            "Disk Used (GB)": f"{disk.used / (1024 ** 3):.2f}",
            "Disk Free (GB)": f"{disk.free / (1024 ** 3):.2f}",
            "Disk Usage (%)": f"{disk.percent}%",
            "Log File": self.get_log_file(),
            "Log Level": logging.getLevelName(self.log_level),
            "Rotation": "Midnight (System Time)",
            "Max File Size": "30 MB",
            "Backups": self.backup_count
            # "GPUs": gpu_info_list or "No GPUs detected"
        }

        logger.info("System Info:\n" + json.dumps(info, indent=2))

    def get_logger(self, name=None):
        return logging.getLogger(name)

