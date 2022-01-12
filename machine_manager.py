from typing import List

from fastapi import FastAPI

import local_linter_deployer
from schema import ExistingInstance

machine_manager_app = FastAPI()

machines = {}


@machine_manager_app.get("/")
def get_health():
    return "ok machine_manager"


@machine_manager_app.get("/machines")
def get_machines() -> List[ExistingInstance]:
    return list(machines.values())


@machine_manager_app.post("/deploy-linter-version")
def deploy_linter_version(linter_version, instance_id=None) -> ExistingInstance:
    machine = local_linter_deployer.deploy_linter_instance(linter_version, instance_id)
    machines[machine.instance_id] = machine
    return machine


@machine_manager_app.post("/kill-linter")
def kill_linter_instance(instance_id) -> None:
    local_linter_deployer.kill_linter_instance(instance_id)
    machines.pop(instance_id)
