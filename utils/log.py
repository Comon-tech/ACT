import logging
import logging.config
from typing import cast

from colorama import Fore, init
from uvicorn.logging import AccessFormatter, DefaultFormatter

init(autoreset=True)


# ----------------------------------------------------------------------------------------------------
# * Act Logger
# ----------------------------------------------------------------------------------------------------
class ActLogger(logging.Logger):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    SUCCESS = 21
    LOADING = 22
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        logging.addLevelName(self.SUCCESS, "SUCCESS")
        logging.addLevelName(self.LOADING, "LOADING")

    def success(self, msg, *args, **kwargs):
        self.log(self.SUCCESS, msg, *args, **kwargs)

    def loading(self, msg, *args, **kwargs):
        self.log(self.LOADING, msg, *args, **kwargs)


# ----------------------------------------------------------------------------------------------------
# * Formatters
# ----------------------------------------------------------------------------------------------------
class ActDefaultFormatter(DefaultFormatter):
    LEVEL_ICONS = {
        ActLogger.DEBUG: "🐞",
        ActLogger.INFO: "ℹ️",
        ActLogger.SUCCESS: "✅",
        ActLogger.LOADING: "⏳",
        ActLogger.WARNING: "⚠️",
        ActLogger.ERROR: "❌",
        ActLogger.CRITICAL: "💀",
    }

    LEVEL_COLORS = {
        ActLogger.DEBUG: Fore.LIGHTBLACK_EX,
        ActLogger.INFO: Fore.LIGHTBLUE_EX,
        ActLogger.SUCCESS: Fore.LIGHTGREEN_EX,
        ActLogger.LOADING: Fore.LIGHTBLACK_EX,
        ActLogger.WARNING: Fore.LIGHTYELLOW_EX,
        ActLogger.ERROR: Fore.LIGHTRED_EX,
        ActLogger.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        level_icon = self.LEVEL_ICONS.get(record.levelno, "")
        level_color = self.LEVEL_COLORS.get(record.levelno, Fore.RESET)
        if record.name == "uvicorn.error":
            return super().format(record)
        record.name = f"{level_color}[{record.name}]{Fore.RESET}"
        record.levelname = level_icon
        if (
            record.levelno == ActLogger.SUCCESS
            or record.levelno == ActLogger.LOADING
            or record.levelno >= ActLogger.ERROR
        ):
            record.msg = f"{level_color}{record.msg}{Fore.RESET}"
        return super().format(record)


class ActAccessFormatter(ActDefaultFormatter, AccessFormatter):
    pass


# ----------------------------------------------------------------------------------------------------
# * Filters
# ----------------------------------------------------------------------------------------------------
class NameFilter(logging.Filter):
    def __init__(self, name):
        super().__init__()
        self.name_to_filter = name

    def filter(self, record):
        return not record.name == self.name_to_filter


# ----------------------------------------------------------------------------------------------------
# * Config
# ----------------------------------------------------------------------------------------------------
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": ActDefaultFormatter,
            "format": "%(levelname)s %(name)s %(message)s",
            "use_colors": True,
        },
        "access": {
            "()": ActAccessFormatter,
            "fmt": "%(levelname)s %(name)s [%(request_line)s] %(client_addr)s %(status_code)s",
            "use_colors": True,
        },
    },
    "filters": {
        "name_filter": {
            "()": NameFilter,
            "name": "uvicorn.error",
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stderr",
            "filters": ["name_filter"],
        },
        "access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "handlers": ["default"],
            "level": "INFO",
        },
        "discord": {"handlers": ["default"], "level": "WARNING", "propagate": False},
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {"level": "INFO"},
    },
}

# ----------------------------------------------------------------------------------------------------
# * Apply Logging Configuration
# ----------------------------------------------------------------------------------------------------
logging.setLoggerClass(ActLogger)
logging.config.dictConfig(LOG_CONFIG)


# ----------------------------------------------------------------------------------------------------
# * Create Logger
# ----------------------------------------------------------------------------------------------------
def logger(name=""):
    """Return a logger. The name is recommended to be __name__ for the current module."""
    return cast(ActLogger, logging.getLogger(name))
