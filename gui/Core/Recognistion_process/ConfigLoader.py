import json
from pathlib import Path

class ConfigLoader:
    """
        This class will load the specified config file
    """

    def __init__(self, config_file: str= r"Config/config.json"):

        self.config_file = config_file
        self.config = {}
        self._load_config()
        self.config_path=r"Config/config.json"

    def _load_config(self):
        config_path = Path(self.config_file)
        if not config_path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        with open(self.config_file, 'r') as file:
            try:
                self.config = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing JSON file: {e}")


    def get(self, key: str, default=None):
        """
        this will find the specified key
        :return value of given key
        """
        keys = key.split('.')
        value = self.config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def update_json_key(self, key, new_value):
        try:
            # Load the JSON data from the file
            with open(self.config_path, 'r') as file:
                data = json.load(file)

            # Update the key's value
            if key in data:
                data[key] = new_value
                print(f"Updated '{key}' to '{new_value}'.")
            else:
                print(f"Key '{key}' not found. Adding it to the JSON.")
                data[key] = new_value

            # Write the updated JSON back to the file
            with open(self.config_path, 'w') as file:
                json.dump(data, file, indent=4)

            print("JSON file updated successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")



