from fastapi import FastAPI

import linter_api
import machine_manager_api
from schema import LinterResponse, LinterRequest

load_balancer_app = FastAPI()

machine_number = 0
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
    global machine_number

    machines = machine_manager_api.get_machines(machine_manager_url)

    if machine_number >= len(machines):
        machine_number = 0

    if len(machines) == 0:
        return LinterResponse(result="fail", errors=["No linter machine available"])

    machine_number += 1
    return linter_api.validate(machines[machine_number - 1].address, request)
