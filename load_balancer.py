import os
from fastapi import FastAPI
from multiprocessing import Lock
import logging
from logging.config import dictConfig

from configs.load_balancer.logging_config import log_config
import linter_api
import machine_manager_api
from schema import LinterResponse, LinterRequest

dictConfig(log_config)
logger = logging.getLogger("load_balancer_logger")
load_balancer_app = FastAPI()
lock = Lock()

linter_number = 0
machine_manager_url = os.environ.get("LOAD_BALANCER_MACHINE_MANAGER_URL")


@load_balancer_app.get("/")
def health_check() -> str:
    return "ok"


@load_balancer_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    global linter_number

    linters = machine_manager_api.get_linters(machine_manager_url, request.language)
    linters.sort(key=lambda linter: linter.instance_id)

    if len(linters) == 0:
        return LinterResponse(result="fail",
                              errors=[f"No linter instance available for language {request.language}."],
                              test_logging=[])

    retries_count = int(os.environ.get("LOAD_BALANCER_RETRIES_COUNT", 3))
    for retry_number in range(retries_count):
        lock.acquire()
        local_linter_number = linter_number

        linter_number += 1
        if linter_number >= len(linters):
            linter_number = 0
        lock.release()

        try:
            return linter_api.validate(linters[local_linter_number - 1].address, request)
        except:
            logger.exception("Load balancer did not get a response from linter. Number of try: %d", retry_number + 1)
            continue

    return LinterResponse(result="fail", errors=["No linter instance was able to handle request"], test_logging=[])
