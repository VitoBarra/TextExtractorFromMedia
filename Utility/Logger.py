import logging

from rich.console import Console
from rich.logging import RichHandler

console = Console()

def setup_logger(name: str = "pipeline", level: str = "INFO", show_path_dev: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.handlers.clear()


    handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        show_level=True
    )
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False
    return logger

log = setup_logger()
# === Helper functions with Rich markup ===
def info(msg: str):
    log.info(f"[white]{msg}[/]")

def warning(msg: str):
    log.warning(f"[yellow]{msg}[/]")

def error(msg: str):
    log.error(f"[bold red]{msg}[/]")

def debug(msg: str):
    log.debug(f"[dim]{msg}[/]")

def critical(msg: str):
    log.critical(f"[bold red on white]{msg}[/]")
