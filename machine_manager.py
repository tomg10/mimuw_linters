from typing import List

from fastapi import FastAPI

import local_linter_deployer
from schema import ExistingInstance

machine_manager_app = FastAPI()

linters = {}


@machine_manager_app.get("/")
def get_health():
    return "ok manager"


@machine_manager_app.get("/linters")
def get_linters() -> List[ExistingInstance]:
    return list(linters.values())


@machine_manager_app.post("/deploy-linter-version")
def deploy_linter_version(linter_version, instance_id=None) -> ExistingInstance:
    linter = local_linter_deployer.deploy_linter_instance(linter_version, instance_id)
    linters[linter.instance_id] = linter
    return linter


@machine_manager_app.post("/kill-linter")
def kill_linter_instance(instance_id) -> None:
    local_linter_deployer.kill_linter_instance(instance_id)
    linters.pop(instance_id)
