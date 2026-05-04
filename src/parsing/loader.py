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
    def _default_content() -> dict[str, Any]:
        return {
            "highscore_filename": "highscore.json",
            "level": [
                {"name": "easy", "width": 8, "height": 10,
                    "level_max_time": 90, "pacgum": 15},
                {"name": "medium", "width": 10, "height": 20,
                    "level_max_time": 120, "pacgum": 30},
                {"name": "medium2", "width": 20, "height": 10,
                    "level_max_time": 240, "pacgum": 30},
                {"name": "hard"}
            ],
            "lives": 3,
            "points_per_pacgum": 10,
            "points_per_super_pacgum": 50,
            "points_per_ghost": 200,
            "seed": 42,
            "fov": 90.0,
            "highscore": [],
        }

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

        content = re.sub(r"(\/\/.*|\/\*[\s\S]*?\*\/|#.*)", "", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {file_path}: {e}")

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
            try:
                content = ConfigLoader._loadfile(file_path)
            except ValueError as e:
                Logger.warning(str(e))
                content = ConfigLoader._default_content()
        else:
            content = ConfigLoader._default_content()

        if not content:
            Logger.warning("Content of the json is empty.")
            content = ConfigLoader._default_content()

        content.setdefault("highscore", [])

        Logger.debug(f"Config loaded: {json.dumps(content, indent=2)}")

        try:
            return ConfigModel(**content)
        except ValidationError as etc:
            error = etc.errors()[0]
            Logger.warning(f"Invalid config: {error['msg']}")
            return ConfigModel()
