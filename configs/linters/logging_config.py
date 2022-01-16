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
        "killable_linter_proxy": {
            "class": "logging.FileHandler",
            "formatter": "main",
            "filename": "logs/killable_linter_proxy.log",
        },
    },
    "loggers": {
        "linter_logger": {
            "level": "DEBUG",
            "handlers": ["linter"],
        },
        "killable_linter_proxy_logger": {
            "level": "DEBUG",
            "handlers": ["killable_linter_proxy"],
        },
    },
    "disable_existing_loggers": False,
}
