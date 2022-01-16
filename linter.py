import os
from fastapi import FastAPI, HTTPException
from multiprocessing import Lock
import subprocess
import random

from services_addresses import get_env_or_raise
from schema import LinterRequest, LinterResponse

linter_app = FastAPI()
lock = Lock()

responses_count = 0
languages_binaries_paths = {}


@linter_app.get("/")
def health_check() -> str:
    return "ok"


@linter_app.post("/set_binary")
def set_binary(language: str, path_to_binary: str) -> None:
    global languages_binaries_paths

    try:
        lock.acquire()
        languages_binaries_paths[language] = path_to_binary
    finally:
        lock.release()


@linter_app.post("/validate")
def validate_file(request: LinterRequest):
    global responses_count

    test_logging = []
    path_to_binary = ""
    try:
        lock.acquire()

        responses_count += 1

        if request.language not in languages_binaries_paths:
            return HTTPException(status_code=400,
                                 detail=f"This linter does not support {request.language} language. "
                                        f"Supported languages: {languages_binaries_paths}")
        path_to_binary = languages_binaries_paths[request.language]

        if get_env_or_raise("LINTER_TEST_LOGGING"):
            test_logging = [
                f"Current responses_count: {responses_count}",
                f"Current languages with linter binaries: {languages_binaries_paths}",
            ]
    finally:
        lock.release()

    # We can get a collision with another instance, but I don't think it is important (prob. is low).
    tmp_file_name = f'tmp{random.randint(1, 1000000000)}.txt'
    with open(tmp_file_name, "w") as f:
        f.write(request.code)

    with open(tmp_file_name, "r") as f:
        result = subprocess.run([f"{path_to_binary}"], text=True, stdin=f, stdout=subprocess.PIPE)
    os.remove(tmp_file_name)

    if result.returncode == 0:
        return LinterResponse(result="ok", errors=[], test_logging=test_logging)

    errors = result.stdout.strip().split('\n')
    return LinterResponse(result="fail", errors=errors, test_logging=test_logging)


print("started linter instance!")
