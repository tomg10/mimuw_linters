log_config = {
    "version": 1,
    "formatters": {
        "main": {
            "format": "%(levelname)s::%(asctime)s:    %(module)s  ---  %(message)s"
        },
    },
    "handlers": {
        "update_manager": {
            "class": "logging.FileHandler",
            "formatter": "main",
            "filename": "logs/update_manager.log",
        },
    },
    "loggers": {
        "update_manager_logger": {
            "level": "DEBUG",
            "handlers": ["update_manager"],
        },
    },
    "disable_existing_loggers": False,
}
