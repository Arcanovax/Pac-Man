from sys import stderr
import os
from dotenv import load_dotenv
import re

from .color import Color


load_dotenv()


class Logger:
    """Simple console logger with level filtering and colored output.

    Provides class methods for common log levels (info, success, warning,
    error, debug) and a helper to normalize error messages.
    """
    LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "WARNING": 30,
        "ERROR": 40,
        "NONE": 100
    }

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def _get_log_level(cls, level: str) -> bool:
        """Return whether the provided level should be logged.

        Args:
            level: The log level name to check (e.g. 'INFO', 'DEBUG').

        Returns:
            True if messages at `level` should be emitted given the
            current `LOG_LEVEL` setting, False otherwise.
        """
        current = cls.LEVELS.get(cls.LOG_LEVEL, 20)
        target = cls.LEVELS.get(level, 20)
        return target >= current

    @classmethod
    def info(cls, message: str) -> None:
        """Log an informational message to stdout."""
        if cls._get_log_level("INFO"):
            print(f"[{Color.BLUE}{Color.BOLD}INFO{Color.RESET}] {message}")

    @classmethod
    def success(cls, message: str) -> None:
        """Log a success message to stdout."""
        if cls._get_log_level("SUCCESS"):
            print(f"[{Color.GREEN}{Color.BOLD}SUCCESS{Color.RESET}] {message}")

    @classmethod
    def warning(cls, message: str) -> None:
        """Log a warning message to stderr."""
        if cls._get_log_level("WARNING"):
            print(
                f"[{Color.YELLOW}{Color.BOLD}WARNING{Color.RESET}] {message}",
                file=stderr
            )

    @classmethod
    def error(cls, message: str) -> None:
        """Log an error message to stderr."""
        if cls._get_log_level("ERROR"):
            print(
                f"[{Color.RED}{Color.BOLD}ERROR{Color.RESET}] {message}",
                file=stderr
            )

    @classmethod
    def debug(cls, message: str) -> None:
        """Log a debug message to stderr when debug is enabled."""
        if cls._get_log_level("DEBUG"):
            print(
                f"[{Color.MAGENTA}{Color.BOLD}DEBUG{Color.RESET}] {message}",
                file=stderr
            )

    @staticmethod
    def remove_errno(message: str) -> str:
        """Remove leading '[Errno N]' annotations from exception messages.

        Args:
            message: The original exception or message string.

        Returns:
            The cleaned string without the errno prefix.
        """
        return re.sub(r"\[Errno \d+\]\s*", "", str(message))
