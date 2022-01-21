from fastapi import FastAPI, HTTPException
from multiprocessing import Lock
import logging
from logging.config import dictConfig

from configs.linters.logging_config import log_config
import simple_python_linter
import simple_java_linter
import simple_c_linter
from services_addresses import get_env_or_raise
from schema import LinterRequest, LinterResponse

dictConfig(log_config)
logger = logging.getLogger("linter_logger")
linter_app = FastAPI()
lock = Lock()

responses_count = 0


@linter_app.get("/")
def health_check() -> str:
    return "ok"


@linter_app.get("/supported_languages")
def get_supported_languages() -> [str]:
    return ["python", "java", "c"]


@linter_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    global responses_count

    test_logging = []
    try:
        lock.acquire()

        responses_count += 1
        logger.debug(f"Response count now at {responses_count}.")

        if get_env_or_raise("LINTER_TEST_LOGGING"):
            test_logging = [
                f"Current responses_count: {responses_count}",
            ]
    finally:
        lock.release()

    if request.language == "python":
        response = simple_python_linter.lint(request)
    elif request.language == "java":
        response = simple_java_linter.lint(request)
    elif request.language == "c":
        response = simple_c_linter.lint(request)
    else:
        raise HTTPException(status_code=400, detail=f"Linter instance does not support {request.language} language.")

    response.test_logging = test_logging
    return response


logger.debug("Started linter instance!")
