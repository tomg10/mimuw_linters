log_config = {
    "version": 1,
    "formatters": {
        "main": {
            "format": "%(levelname)s::%(asctime)s:    %(module)s  ---  %(message)s"
        },
    },
    "handlers": {
        "load_balancer": {
            "class": "logging.FileHandler",
            "formatter": "main",
            "filename": "logs/load_balancer.log",
        },
    },
    "loggers": {
        "load_balancer_logger": {
            "level": "DEBUG",
            "handlers": ["load_balancer"],
        },
    },
    "disable_existing_loggers": False,
}
