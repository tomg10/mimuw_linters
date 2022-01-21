import os
from typing import List
from multiprocessing import Lock
from fastapi import FastAPI, HTTPException
import logging
from logging.config import dictConfig

import linter_api
from configs.machine_manager.logging_config import log_config
import killable_proxy_deployer
import local_linter_deployer
import gcp_linter_deployer
from schema import ExistingInstance

dictConfig(log_config)
logger = logging.getLogger("machine_manager_logger")
machine_manager_app = FastAPI()
lock = Lock()

linters = {}
deploy_backend_type = os.environ.get("MACHINE_MANAGER_DEPLOY_BACKEND", "local")
logger.info(f"Starting machine manager with backend {deploy_backend_type}")


@machine_manager_app.get("/")
def get_health():
    return "ok"


@machine_manager_app.get("/linters")
def get_linters(language: str = None) -> List[ExistingInstance]:
    try:
        lock.acquire()

        if language:
            return list(filter(lambda instance: language in instance.languages, linters.values()))
        return list(linters.values())
    finally:
        lock.release()


@machine_manager_app.post("/deploy-linter-version")
def deploy_linter_version(linter_version, instance_id=None) -> ExistingInstance:
    try:
        lock.acquire()
        if deploy_backend_type == 'killable_proxy':
            linter = killable_proxy_deployer.deploy_linter_instance(linter_version, instance_id)
        elif deploy_backend_type == 'local':
            linter = local_linter_deployer.deploy_linter_instance(linter_version, instance_id)
        elif deploy_backend_type == "gcp":
            linter = gcp_linter_deployer.deploy_linter_instance(linter_version, instance_id)

        linter.languages = linter_api.get_supported_languages(linter.address)
        linters[linter.instance_id] = linter
        logger.debug(f"Linter {linter.instance_id} supports the following languages: {linter.languages}.")

        return linter
    except:
        logger.exception(f"Deployment of linter with version {linter_version} and instance ID {instance_id} failed.")
        raise HTTPException(status_code=400, detail=f"Could not (re)start linter with version {linter_version}")
    finally:
        lock.release()


@machine_manager_app.post("/kill-linter")
def kill_linter_instance(instance_id) -> None:
    try:
        lock.acquire()
        if deploy_backend_type == 'killable_proxy':
            killable_proxy_deployer.kill_linter_instance(instance_id)
        elif deploy_backend_type == 'local':
            local_linter_deployer.kill_linter_instance(instance_id)
        elif deploy_backend_type == "gcp":
            gcp_linter_deployer.kill_linter_instance(instance_id)

        linters.pop(instance_id)
    finally:
        lock.release()
