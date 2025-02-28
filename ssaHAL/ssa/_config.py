import json

class ConfigLoader:
    """
    @brief The ConfigLoader class is used to load and validate the configuration and secrets files
    @param files A list of json files to load into the configuration
    """
    def __init__(self, files):
        self.files = files

    def load_config(self):
        """
        @brief Load the configuration file
        @return The merged configuration dictionary of all the files
        """
        config = {}

        for file in self.files:
            try:
                with open(file, 'r') as f:
                    config.update(json.load(f))
            except Exception as e:
                raise Exception(f"[ERROR] Failed to load configuration file: {e}") from e

        return config
