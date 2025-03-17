import json


class ConfigLoader:
    """
    @brief The ConfigLoader class is used to load and validate the configuration and secrets files
    @param files A list of json files to load into the configuration
    """

    def __init__(self, files):
        """
        Initializes the ConfigLoader with a list of JSON configuration file paths.

        Args:
            files (list[str]): A list of paths to JSON configuration files.
        """
        self.files = files

    def load_config(self):
        """
        Loads and merges configuration from the specified JSON files.

        Opens each file from the instance's file list and updates a configuration dictionary with the JSON content.
        If a file cannot be read or its contents are not valid JSON, an exception is raised with an error message.
        If duplicate keys occur, values from later files override those from earlier ones.

        Returns:
            dict: The consolidated configuration dictionary containing data from all files.

        Raises:
            Exception: When a file fails to open or its JSON content cannot be parsed.
        """
        config = {}

        for file in self.files:
            try:
                with open(file, "r") as f:
                    config.update(json.load(f))
            except Exception as e:
                raise Exception(
                    f"[ERROR] Failed to load configuration file: {e}"
                ) from e

        return config
