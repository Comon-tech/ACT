import logging

from colorama import Fore, init
from uvicorn.logging import AccessFormatter, DefaultFormatter

init(autoreset=True)

# ----------------------------------------------------------------------------------------------------
# * Logger
# ----------------------------------------------------------------------------------------------------
logging.__dict__["SUCCESS"] = 21
logging.__dict__["LOADING"] = 22
logging.addLevelName(logging.SUCCESS, "SUCCESS")
logging.addLevelName(logging.LOADING, "LOADING")


def success(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.SUCCESS):
        self._log(logging.SUCCESS, message, args, **kwargs)


def loading(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.LOADING):
        self._log(logging.LOADING, message, args, **kwargs)


logging.Logger.success = success
logging.Logger.loading = loading


# ----------------------------------------------------------------------------------------------------
# * Formatters
# ----------------------------------------------------------------------------------------------------
class ActDefaultFormatter(DefaultFormatter):
    LEVEL_ICONS = {
        logging.DEBUG: "🐞",
        logging.INFO: "ℹ️",
        logging.SUCCESS: "✅",
        logging.LOADING: "⏳",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "💀",
    }

    LEVEL_COLORS = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,
        logging.INFO: Fore.LIGHTBLUE_EX,
        logging.SUCCESS: Fore.LIGHTGREEN_EX,
        logging.LOADING: Fore.LIGHTBLACK_EX,
        logging.WARNING: Fore.LIGHTYELLOW_EX,
        logging.ERROR: Fore.LIGHTRED_EX,
        logging.CRITICAL: Fore.MAGENTA,
    }

    def format(self, record):
        level_icon = self.LEVEL_ICONS.get(record.levelno, "")
        level_color = self.LEVEL_COLORS.get(record.levelno, Fore.RESET)
        if record.name == "uvicorn.error":
            return super().format(record)
        record.name = f"{level_color}[{record.name}]{Fore.RESET}"
        record.levelname = level_icon
        if (
            record.levelno == logging.SUCCESS
            or record.levelno == logging.LOADING
            or record.levelno >= logging.ERROR
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
# * Ceeate Logger
# ----------------------------------------------------------------------------------------------------
logging.config.dictConfig(LOG_CONFIG)


def logger(name=""):
    """Return a logger. The name is recommended to be __name__ for the current module."""
    return logging.getLogger(name)
