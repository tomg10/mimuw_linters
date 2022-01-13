import machine_manager_api
import random

from fastapi import FastAPI, HTTPException
from multiprocessing import Lock

update_manager_app = FastAPI()
lock = Lock()

updates_progress = {}

STEPS = [0, 0.1, 0.5, 1]


@update_manager_app.get("/")
def get_health():
    return "ok update_manager"


@update_manager_app.post("/update")
def update(machine_manager_url: str, version: str):
    try:
        lock.acquire()
        current_progress = updates_progress.get(version, 0)
        current_step = STEPS.index(current_progress)

        if current_step == len(STEPS) - 1:
            return HTTPException(status_code=400, detail="Update already finished")

        machines_list = machine_manager_api.get_machines(machine_manager_url)
        # Random machines list to not make any assumption about list of machines, can be commented
        random.shuffle(machines_list)
        machines_len = len(machines_list)

        next_progress = STEPS[current_step + 1]
        newer_machines = list(filter(lambda machine: machine.version >= version, machines_list))
        older_machines = list(filter(lambda machine: machine.version < version, machines_list))

        all_to_update = round(next_progress * machines_len)
        already_updated = len(newer_machines)
        rest_to_update = all_to_update - already_updated

        for machine in older_machines[:rest_to_update]:
            machine_manager_api.deploy_linter_instance(machine_manager_url, version, machine.instance_id)

        updates_progress[version] = next_progress

    finally:
        lock.release()

    return "ok"


@update_manager_app.post("/rollback")
def rollback(machine_manager_url: str, version: str):
    try:
        lock.acquire()

        machines_list = machine_manager_api.get_machines(machine_manager_url)

        # Random machines list to not make any assumption about list of machines, can be commented
        random.shuffle(machines_list)

        newer_machines = list(filter(lambda machine: machine.version > version, machines_list))

        for machine in newer_machines:
            print("rollback machine: ", machine.instance_id)
            machine_manager_api.deploy_linter_instance(machine_manager_url, version, machine.instance_id)

        for key in updates_progress:
            if key > version:
                updates_progress[key] = 0
    finally:
        lock.release()

    return "ok"


@update_manager_app.get("/status")
def status(version: str):
    global updates_progress

    try:
        lock.acquire()

        update_progress = updates_progress.get(version, 0)
    finally:
        lock.release()

    return update_progress


