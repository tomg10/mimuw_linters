from fastapi import FastAPI
from multiprocessing import Lock

import linter_api
import machine_manager_api
from schema import LinterResponse, LinterRequest


load_balancer_app = FastAPI()
lock = Lock()

linter_number = 0
machine_manager_url = ""


@load_balancer_app.get("/")
def health_check() -> str:
    return "ok balancer"


@load_balancer_app.get("/set_machine_manager")
def set_machine_manager(machine_manager: str = "") -> None:
    global machine_manager_url

    machine_manager_url = machine_manager
    print(f"Machine manager set up on: {machine_manager_url}")


@load_balancer_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    global linter_number

    linters = machine_manager_api.get_linters(machine_manager_url)
    linters.sort(key=lambda linter: linter.instance_id)

    if len(linters) == 0:
        return LinterResponse(result="fail", errors=["No linter instance available"], debug=[])

    try:
        lock.acquire()

        if linter_number >= len(linters):
            linter_number = 0

        linter_number += 1
    finally:
        lock.release()

    return linter_api.validate(linters[linter_number - 1].address, request)
