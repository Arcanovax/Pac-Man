from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
    model_validator
)
from typing import Any
import json

from ..logger import Logger


class LevelModel(BaseModel):
    """Pydantic model describing a single game level configuration.

    Fields include dimensions, max time for the level and number of pac-gums.
    """
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1)
    width: int = Field(gt=0, default=15)
    height: int = Field(gt=0, default=20)
    level_max_time: int = Field(gt=0, default=90)
    pacgum: int = Field(gt=0, default=42)

    @field_validator(
        "pacgum", "level_max_time",
        mode="before"
    )
    @classmethod
    def _validate_positive(cls, v: Any, info: Any) -> Any:
        """Validator to coerce a value to positive integer or use the default.

        Args:
            v: The incoming raw value to validate.
            info: Pydantic validator info containing field metadata.

        Returns:
            A valid positive integer for the field or the field default.
        """
        field_name = info.field_name

        try:
            v = int(v)
        except Exception:
            Logger.warning(f"'{field_name}' invalid, using default")
            return cls.model_fields[field_name].default

        if v <= 0:
            Logger.warning(f"'{field_name}' must be > 0, using default")
            return cls.model_fields[field_name].default

        return v

    @field_validator(
        "width", "height",
        mode="before"
    )
    @classmethod
    def _validate_size(cls, v: Any, info: Any) -> Any:
        """Validator to coerce a value to positive integer or use the default.

        Args:
            v: The incoming raw value to validate.
            info: Pydantic validator info containing field metadata.

        Returns:
            A valid positive integer for the field or the field default.
        """
        field_name = info.field_name

        try:
            v = int(v)
        except Exception:
            Logger.warning(f"'{field_name}' invalid, using default")
            return cls.model_fields[field_name].default

        if v <= 0:
            Logger.warning(f"'{field_name}' must be > 0, using default")
            return cls.model_fields[field_name].default

        if v <= 20:
            Logger.warning(f"'{field_name}' must be < 20, using default")
            return cls.model_fields[field_name].default

        return v


class ConfigModel(BaseModel):
    """Pydantic model representing the whole configuration object.

    Contains defaults for game settings and validates numeric fields.
    """
    model_config = ConfigDict(extra="ignore")

    highscore_filename: str = Field(min_length=1, default="highscore.json")
    level: list[LevelModel] = Field(default=[
        LevelModel(name="easy"),
        LevelModel(name="medium"),
        LevelModel(name="hard"),
    ])
    lives: int = Field(gt=0, default=3)
    points_per_pacgum: int = Field(gt=0, default=10)
    points_per_super_pacgum: int = Field(gt=0, default=50)
    points_per_ghost: int = Field(gt=0, default=200)
    seed: int = Field(default=42)
    highscore: list[dict[str, int | str]] = Field(default=[])
    mouse_sensitivity: float = Field(default=80.0)
    fov: float = Field(default=90.0)

    def __str__(self) -> str:
        """Return a human-readable string representation of the config.

        Useful for debugging and logging the current configuration.
        """
        return (
            "Config Object: {\n"
            f"\tHighscore filename: {self.highscore_filename}\n"
            f"\tLevel: {self.level}\n"
            f"\tLives: {self.lives}\n"
            f"\tPoints per Pacgum: {self.points_per_pacgum}\n"
            f"\tPoints per Super Pacgum: {self.points_per_super_pacgum}\n"
            f"\tPoints per Ghost: {self.points_per_ghost}\n"
            f"\tSeed: {self.seed}\n"
            f"\tHigh Score: {self.highscore}\n"
            "}\n"
        )

    @field_validator(
        "lives",
        "points_per_pacgum", "points_per_super_pacgum",
        "points_per_ghost",
        mode="before"
    )
    @classmethod
    def _validate_positive(cls, v: Any, info: Any) -> Any:
        """Validator to ensure numeric fields are positive integers.

        Mirrors the LevelModel validator behavior for other numeric fields.
        """
        field_name = info.field_name

        try:
            v = int(v)
        except Exception:
            Logger.warning(f"'{field_name}' invalid, using default")
            return cls.model_fields[field_name].default

        if v <= 0:
            Logger.warning(f"'{field_name}' must be > 0, using default")
            return cls.model_fields[field_name].default

        return v

    @field_validator(
        "mouse_sensitivity",
        "fov",
        mode="before"
    )
    @classmethod
    def _validate_float_positive(cls, v: Any, info: Any) -> Any:
        field_name = info.field_name
        limit = {
            "fov": (50.0, 120.0),
            "mouse_sensitivity": (20.0, 80.0),
        }

        try:
            v = float(v)
        except Exception:
            Logger.warning(f"'{field_name}' invalid, using default")
            return cls.model_fields[field_name].default

        min_value, max_value = limit[field_name]
        if v < min_value or v > max_value:
            Logger.warning(
                f"'{field_name}' must be between {min_value} and {max_value}, "
                "using default"
            )
            return cls.model_fields[field_name].default

        return v

    @field_validator("seed", mode="before")
    @classmethod
    def _seed_validator(cls, v: Any) -> Any:
        if v is None:
            Logger.warning("'seed' not provided, using default (42)")
            return 42

        try:
            return int(v)
        except Exception:
            Logger.warning("'seed' invalid, using default (42)")
            return 42

    @field_validator("level", mode="before")
    @classmethod
    def _validate_levels(cls, v: Any) -> Any:
        if not isinstance(v, list) or len(v) == 0:
            Logger.warning("'level' invalid, using default levels")
            return cls.model_fields["level"].default
        return v

    @field_validator("highscore_filename", mode="before")
    @classmethod
    def _validate_string(cls, v: Any) -> Any:
        if not isinstance(v, str):
            Logger.warning("'highscore_filename' invalid, using default")
            return cls.model_fields["highscore_filename"].default
        return v

    @model_validator(mode="after")
    def load_highscore(self) -> Any:
        try:
            with open(self.highscore_filename, "r") as f:
                self.highscore = sorted(
                    json.load(f),
                    key=lambda x: x["score"],
                    reverse=True
                )
        except Exception:
            Logger.warning("Failed to parse highscore file, using default")
            self.highscore = []
        return self
