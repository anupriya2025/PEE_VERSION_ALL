import configparser
import json
import torch
from threading import Lock


class ConfigLoader:
    _instance = None
    _lock = Lock()  # For thread safety

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of the class is created (singleton pattern)."""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(ConfigLoader, cls).__new__(cls, *args, **kwargs)

                    # Initialize configurations
                    cls._instance.ini_data = cls._instance.load_config('ini')
                    cls._instance.json_data = cls._instance.load_config('json')

        return cls._instance

    @staticmethod
    def load_config(file_type):
        """Static method to load the configuration from an INI or JSON file.

        Args:
            file_type (str): Type of the configuration file ('ini' or 'json').

        Returns:
            dict: Parsed configuration dictionary or None if the file is missing/invalid.
        """
        try:
            if file_type == 'ini':
                config = configparser.ConfigParser()
                config.read('Config/config.ini')

                if not config.sections():
                    raise FileNotFoundError("No sections found in INI file. Ensure the file exists and is properly formatted.")

                # Parsing the parameters from the INI file
                parsed_config = {
                    'MODEL_NAME': config['MODEL']['MODEL_NAME'],
                    'PRECISION': config['MODEL']['PRECISION'],
                    'DEVICE': torch.device(config['MODEL']['DEVICE']),
                    'TARGET_CLASSES': config['TRACKING']['TARGET_CLASSES'].split(", "),
                    'START_TRACKING_POINTS': eval(config['TRACKING']['START_TRACKING_POINTS']),
                    'END_TRACKING_POINTS': eval(config['TRACKING']['END_TRACKING_POINTS']),
                    'ENTRY_LINE_Y': int(config['TRACKING']['ENTRY_LINE_Y']),
                    'EXIT_LINE_Y': int(config['TRACKING']['EXIT_LINE_Y']),
                    'OUTPUT_SHAPES': [eval(config['OUTPUT']['OUTPUT_SHAPES'])],
                    'COCO_LABELS': config['COCO']['COCO_LABELS'].split(", ")
                }
                return parsed_config

            elif file_type == 'json':
                with open('Config/config.json', 'r') as file:
                    config = json.load(file)

                # Parsing the parameters from the JSON file
                parsed_config = {
                    "app_name": config.get("app_name", ""),
                    "version": config.get("version", ""),
                    "settings": config.get("settings", {}),
                    "audio": config.get("audio", "OFF"),
                    "ffmpeg_lib_path":config.get("ffmpeg_lib_path",""),
                    "selected_audio_file": config.get("selected_audio_file", ""),
                    "database": {
                        "server": config["database"]["server"],
                        "dsn": config["database"]["dsn"],
                        "user": config["database"]["user"],
                        "password": config["database"]["password"],
                        "db_name": config["database"]["db_name"]
                    },
                    "model_details": {
                        "license_plate_detection_model_path": config["model_details"]["license_plate_detection_model_path"]
                    },
                    "ocr_details": {
                        "lang": config["ocr_details"]["lang"],
                        "use_angle_cls": config["ocr_details"]["use_angle_cls"]
                    },
                    "log_file_path": config.get("log_file_path", ""),
                    "tables": config.get("tables", {}),
                    "log_level": config.get("log_level", "info"),
                    "log_type": config.get("log_type", "low")
                }
                return parsed_config

            else:
                raise ValueError("Unsupported configuration file type. Use 'ini' or 'json'.")

        except FileNotFoundError as e:
            print(f"Error: {e}")
            return None
        except KeyError as e:
            print(f"Missing key in {file_type.upper()} file: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error while loading {file_type.upper()} file: {e}")
            return None

    def update_json_key(self, key, new_value):
        try:
            # Load the JSON data from the file
            with open('Config/config.json', 'r') as file:
                data = json.load(file)

            # Update the key's value
            if key in data:
                data[key] = new_value
                print(f"Updated '{key}' to '{new_value}'.")
            else:
                print(f"Key '{key}' not found. Adding it to the JSON.")
                data[key] = new_value

            # Write the updated JSON back to the file
            with open('Config/config.json', 'w') as file:
                json.dump(data, file, indent=4)

            print("JSON file updated successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")


    def get(self, key: str, default=None, file_type='json'):
        """
        this will find the specified key
        :return value of given key
        """
        if file_type == 'json':
            keys = key.split('.')
            value = self.json_data
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                return default
        else:
            keys = key.split('.')
            value = self.ini_data
            try:
                for k in keys:
                    value = value[k]
                return value
            except (KeyError, TypeError):
                return default


