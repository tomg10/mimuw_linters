import os
from fastapi import FastAPI
from multiprocessing import Lock
import subprocess
import random
import logging
from logging.config import dictConfig

from configs.linters.logging_config import log_config
import simple_python_linter
from services_addresses import get_env_or_raise
from schema import LinterRequest, LinterResponse

dictConfig(log_config)
logger = logging.getLogger("linter_logger")
linter_app = FastAPI()
lock = Lock()

responses_count = 0
linter_path_to_binary = ""


@linter_app.get("/")
def health_check() -> str:
    return "ok"


@linter_app.post("/set_binary")
def set_binary(path_to_binary: str) -> None:
    global linter_path_to_binary

    try:
        lock.acquire()
        linter_path_to_binary = path_to_binary
    finally:
        lock.release()


@linter_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    global responses_count

    test_logging = []
    local_linter_path_to_binary = ""
    try:
        lock.acquire()

        responses_count += 1
        local_linter_path_to_binary = linter_path_to_binary

        logger.debug(f"Response count now at {responses_count}.")

        if get_env_or_raise("LINTER_TEST_LOGGING"):
            test_logging = [
                f"Current responses_count: {responses_count}",
                f"Current path to linter binary: {linter_path_to_binary}",
            ]
    finally:
        lock.release()

    response = simple_python_linter.lint(request)
    response.test_logging = test_logging
    return response


logger.debug("Started linter instance!")
