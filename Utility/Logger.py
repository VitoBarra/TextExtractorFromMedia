import logging
from enum import Enum
from rich.console import Console
from rich.logging import RichHandler


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class Logger:
    _console = Console()
    _logger: logging.Logger | None = None

    @staticmethod
    def setup(
        name: str = "pipeline",
        level: LogLevel = LogLevel.INFO,
        show_path_dev: bool = True,
    ) -> None:
        """
        Initialize the logger with Rich formatting.
        """
        logger = logging.getLogger(name)
        if logger.hasHandlers():
            logger.handlers.clear()

        handler = RichHandler(
            console=Logger._console,
            show_time=False,
            show_path=show_path_dev,
            markup=True,
            rich_tracebacks=True,
            show_level=True,
        )

        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        logger.setLevel(level.value)
        handler.setLevel(level.value)

        logger.addHandler(handler)
        logger.propagate = False

        Logger._logger = logger

    @staticmethod
    def _IsInitialized():
        if Logger._logger is None:
            raise RuntimeError("Logger not initialized. Call Logger.setup() first.")

    # === Static helper log methods ===
    @staticmethod
    def debug(msg: str):
        Logger._IsInitialized()
        Logger._logger.debug(f"[dim]{msg}[/]")

    @staticmethod
    def info(msg: str):
        Logger._IsInitialized()
        Logger._logger.info(f"[white]{msg}[/]")

    @staticmethod
    def warning(msg: str):
        Logger._IsInitialized()
        Logger._logger.warning(f"[yellow]{msg}[/]")

    @staticmethod
    def error(msg: str):
        Logger._IsInitialized()
        Logger._logger.error(f"[bold red]{msg}[/]")

    @staticmethod
    def critical(msg: str):
        Logger._IsInitialized()
        Logger._logger.critical(f"[bold red on white]{msg}[/]")

    @staticmethod
    def GetLogger() -> logging.Logger:
        Logger._IsInitialized()
        return Logger._logger

    @ staticmethod
    def GetConsole() -> Console:
        Logger._IsInitialized()
        return Logger._console
