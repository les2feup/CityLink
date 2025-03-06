import json


class ConfigLoader:

    def __init__(self, files):
        self.files = files

    def load_config(self):
        config = {}
        for file in self.files:
            try:
                with open(file, 'r') as f:
                    config.update(json.load(f))
            except Exception as e:
                raise Exception(
                    f'[ERROR] Failed to load configuration file: {e}') from e
        return config
