log_config = {
    "version": 1,
    "formatters": {
        "main": {
            "format": "%(levelname)s::%(asctime)s:    %(module)s  ---  %(message)s"
        },
    },
    "handlers": {
        "health_check": {
            "class": "logging.FileHandler",
            "formatter": "main",
            "filename": "logs/health_check.log",
        },
    },
    "loggers": {
        "health_check_logger": {
            "level": "DEBUG",
            "handlers": ["health_check"],
        },
    },
    "disable_existing_loggers": False,
}
