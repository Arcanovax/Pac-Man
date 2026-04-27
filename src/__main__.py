from sys import argv

from .logger import Logger
from .parsing import ConfigLoader
from .ui.menu import run_main_menu


def main() -> None:
    if len(argv) > 2:
        Logger.error("Too many arguments provided. Using the first one.")
        return
    elif len(argv) < 2:
        Logger.warning("No argument provided. Running default config.")
        file = None
    else:
        file = argv[1]

    if file and len(file) > 0:
        Logger.info(f"Path provided: {file}")

    try:
        config = ConfigLoader.load_config(file)
    except Exception as e:
        Logger.error(f"Error loading config: {e}")
        return

    Logger.debug(str(config))

    print(config)
    run_main_menu(config)


if __name__ == "__main__":
    main()
