from pydantic import ValidationError
import json
import re
from typing import Any

from ..logger import Logger
from .model import ConfigModel


class ConfigLoader:
    """Utility to load and validate configuration files into ConfigModel.

    Provides a simple JSON loader that strips comments and returns a
    validated `ConfigModel` instance.
    """
    @staticmethod
    def _loadfile(file_path: str) -> Any:
        """Read and parse a JSON config file, stripping comments.

        Args:
            file_path: Path to the JSON config file.

        Returns:
            Parsed content as Python objects, or empty dict on error.
        """
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except Exception as e:
            Logger.warning(Logger.remove_errno(str(e)))
            return {}

        content = re.sub(r"(\/\/.*|\/\*[\s\S]*?\*\/)", "", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            Logger.warning(f"Error decoding JSON from {file_path}: {e}")
            return {}

    @staticmethod
    def load_config(file_path: str | None) -> ConfigModel:
        """Load the configuration file and return a `ConfigModel`.

        If the provided file path is None or loading/validation fails,
        returns a default `ConfigModel` instance.

        Args:
            file_path: Optional path to the configuration file.

        Returns:
            A validated `ConfigModel` instance.
        """
        if file_path:
            content = ConfigLoader._loadfile(file_path)
        else:
            content = {}

        Logger.debug(f"Config loaded: {json.dumps(content, indent=2)}")

        try:
            return ConfigModel(**content)
        except ValidationError as etc:
            error = etc.errors()[0]
            Logger.warning(f"Invalid config: {error['msg']}")
            return ConfigModel()
