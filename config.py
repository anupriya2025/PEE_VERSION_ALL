

import sys
import json
import configparser
from pathlib import Path
from threading import Lock

class ConfigLoader:
    """Thread-safe singleton config loader for INI (and optional JSON) configs."""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConfigLoader, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):

        # Determine base directory (EXE or script)
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
        else:
            base_dir = Path(__file__).resolve().parent

        # --------- Load ONLY INI first so we can read preferred_path ----------
        temp_ini_path = Path(base_dir) / "config.ini"
        fallback_ini_path = base_dir / "PPE_HELVES" / "config.ini"

        config_temp = configparser.ConfigParser(strict=False)

        # Load whichever INI exists
        if temp_ini_path.exists():
            config_temp.read(temp_ini_path, encoding="utf-8")
        elif fallback_ini_path.exists():
            config_temp.read(fallback_ini_path, encoding="utf-8")

        # Read preferred path from INI
        preferred_path_str = config_temp.get("MAIN", "preferred_path", fallback=None)
        preferred_path = Path(preferred_path_str) if preferred_path_str else None

        # --------- Determine config directory ----------
        if preferred_path and preferred_path.exists():
            self.config_dir = preferred_path
        else:
            # fallback path near exe or script
            self.config_dir = base_dir / "PPE_HELVES"
            self.config_dir.mkdir(parents=True, exist_ok=True)
            print(f"Preferred config path not found! Using fallback: {self.config_dir}")

        print(f"Using config directory: {self.config_dir}")

        # Paths
        self.ini_path = self.config_dir / "config.ini"
        self.json_path = self.config_dir / "config.json"

        # Load configs now
        self.ini_data = self._load_ini()
        self.json_data = self._load_json()

    # --------------------------- #
    # INI LOADER
    # --------------------------- #
    def _load_ini(self):
        if not self.ini_path.exists():
            print(f" INI file not found: {self.ini_path}")
            return {}

        config = configparser.ConfigParser(strict=False)
        try:
            config.read(self.ini_path, encoding="utf-8")
            return {section: dict(config[section]) for section in config.sections()}

        except configparser.DuplicateSectionError as e:
            print(f" Duplicate section in INI file: {e.section}. Fix file.")
            return {}
        except Exception as e:
            print(f" Failed to load INI: {e}")
            return {}

    # --------------------------- #
    # JSON LOADER
    # --------------------------- #
    def _load_json(self):
        if not self.json_path.exists():
            return {}

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f" Failed to load JSON: {e}")
            return {}

    # --------------------------- #
    # GET VALUE
    # --------------------------- #
    def get(self, key: str, default=None, file_type="ini"):
        data = self.json_data if file_type == "json" else self.ini_data
        for part in key.split("."):
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return default
        return data

    # --------------------------- #
    # UPDATE VALUE IN INI
    # --------------------------- #
    def update_ini_key(self, key: str, new_value):
        if not self.ini_path.exists():
            print(f"INI file not found at {self.ini_path}")
            return

        config = configparser.ConfigParser(strict=False)
        config.read(self.ini_path, encoding="utf-8")

        try:
            section, subkey = key.split(".")
            if not config.has_section(section):
                config.add_section(section)

            config.set(section, subkey, str(new_value))

            with open(self.ini_path, "w", encoding="utf-8") as f:
                config.write(f)

            self.ini_data = self._load_ini()
            print(f"Updated {section}.{subkey} = {new_value}")
        except Exception as e:
            print(f"Failed to update INI key '{key}': {e}")

