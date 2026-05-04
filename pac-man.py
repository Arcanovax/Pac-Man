from sys import exit

from src.logger import Logger


if __name__ == "__main__":
    try:
        from src.__main__ import main

        main()
    except ModuleNotFoundError as error:
        Logger.error(
            "Missing Python package. Install dependencies with `uv sync` "
            "before running pac-man."
        )
        Logger.error(str(error))
        exit(1)
