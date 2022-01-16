import os
from fastapi import FastAPI
from multiprocessing import Lock
import subprocess
import random

import simple_python_linter
from services_addresses import get_env_or_raise
from schema import LinterRequest, LinterResponse

linter_app = FastAPI()
lock = Lock()

responses_count = 0
linter_path_to_binary = ""


@linter_app.get("/")
def health_check() -> str:
    return "ok linter"


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

    debug = []
    local_linter_path_to_binary = ""
    try:
        lock.acquire()

        responses_count += 1
        local_linter_path_to_binary = linter_path_to_binary

        if get_env_or_raise("LINTER_DEBUG"):
            debug = [
                f"Current responses_count: {responses_count}",
                f"Current path to linter binary: {linter_path_to_binary}",
            ]
    finally:
        lock.release()

    response = simple_python_linter.lint(request)
    response.debug = debug
    return response


print("started linter instance!")
