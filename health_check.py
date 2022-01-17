import requests
import os
import logging
from logging.config import dictConfig
from fastapi import FastAPI
from multiprocessing import Lock
from fastapi_utils.tasks import repeat_every

from configs.health_check.logging_config import log_config
from configs.health_check import hearthbeat_config
import machine_manager_api

dictConfig(log_config)
logger = logging.getLogger("health_check_logger")
health_check_app = FastAPI()
lock = Lock()


machine_manager_url = os.environ.get("LOAD_BALANCER_MACHINE_MANAGER_URL")
failures = 0

timeout = hearthbeat_config.timeout
if "HEALTH_CHECK_TIMEOUT" in os.environ:
    timeout = float(os.environ["HEALTH_CHECK_TIMEOUT"])

repetition_period = hearthbeat_config.repetition_period
if "HEALTH_CHECK_REPETITION_PERIOD" in os.environ:
    repetition_period = float(os.environ["HEALTH_CHECK_REPETITION_PERIOD"])


@health_check_app.get("/")
def health_check() -> str:
    return "ok"


@health_check_app.get("/get_failures")
def get_failures() -> int:
    try:
        lock.acquire()
        return failures
    finally:
        lock.release()


@health_check_app.on_event("startup")
@repeat_every(seconds=repetition_period, wait_first=True, logger=logger)
def do_health_check():
    logger.info("Starting healthcheck...")
    linters = machine_manager_api.get_linters(machine_manager_url)
    for linter in linters:
        try:
            lock.acquire()
            hearthbeat(linter)
        finally:
            lock.release()


def hearthbeat(linter):
    global failures

    response = requests.get(f"{linter.address}/", timeout=timeout).json()
    if response != "ok":
        failures += 1
        logger.info(f"Restarting linter {linter.instance_id} at address {linter.address} because got response "
                    f"{response}. Current failure count: {failures}")

        # This will restart the linter.
        machine_manager_api.deploy_linter_instance(machine_manager_url, linter.version, linter.instance_id)


logger.debug("Health check service started.")
