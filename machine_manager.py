from typing import List
from multiprocessing import Lock
from fastapi import FastAPI, HTTPException

import local_linter_deployer
from schema import ExistingInstance

machine_manager_app = FastAPI()
lock = Lock()

linters = {}


@machine_manager_app.get("/")
def get_health():
    return "ok machine_manager"


@machine_manager_app.get("/linters")
def get_linters() -> List[ExistingInstance]:
    try:
        lock.acquire()
        return list(linters.values())
    finally:
        lock.release()


@machine_manager_app.post("/deploy-linter-version")
def deploy_linter_version(linter_version, instance_id=None):
    try:
        lock.acquire()

        linter = local_linter_deployer.deploy_linter_instance(linter_version, instance_id)
        linters[linter.instance_id] = linter
        return linter
    except:
        return HTTPException(status_code=400, detail=f"Could not (re)start linter with version {linter_version}")
    finally:
        lock.release()


@machine_manager_app.post("/kill-linter")
def kill_linter_instance(instance_id) -> None:
    try:
        lock.acquire()
        local_linter_deployer.kill_linter_instance(instance_id)
        linters.pop(instance_id)
    finally:
        lock.release()
