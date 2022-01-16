log_config = {
    "version": 1,
    "formatters": {
        "main": {
            "format": "%(levelname)s::%(asctime)s:    %(module)s:%(process)d  ---  %(message)s"
        },
    },
    "handlers": {
        "killable_linter_proxy": {
            "class": "logging.FileHandler",
            "formatter": "main",
            "filename": "logs/killable_linter_proxy.log",
        },
    },
    "loggers": {
        "killable_linter_proxy_logger": {
            "level": "DEBUG",
            "handlers": ["killable_linter_proxy"],
        },
    },
    "disable_existing_loggers": False,
}
