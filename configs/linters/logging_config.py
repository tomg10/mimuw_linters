log_config = {
    "version": 1,
    "formatters": {
        "main": {
            "format": "%(levelname)s::%(asctime)s:    %(module)s:%(process)d  ---  %(message)s"
        },
    },
    "handlers": {
        "linter": {
            "class": "logging.FileHandler",
            "formatter": "main",
            "filename": "logs/linter.log",
        },
    },
    "loggers": {
        "linter_logger": {
            "level": "DEBUG",
            "handlers": ["linter"],
        },
    },
    "disable_existing_loggers": False,
}
