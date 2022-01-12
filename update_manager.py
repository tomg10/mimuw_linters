from fastapi import FastAPI, HTTPException
import random
import machine_manager_api

update_manager_app = FastAPI()

updates_progress = {}

STEPS = [0, 0.1, 0.5, 1]
# STEPS = [0, 0.5, 1]

@update_manager_app.get("/")
def get_health():
    return "ok update_manager"

@update_manager_app.post("/update")
def update(machine_manager_url: str, version: str):
    print("machine_manager_url:", machine_manager_url)
    print("version:", version)

    current_progress = updates_progress.get(version, 0)
    current_step = STEPS.index(current_progress)

    print("current_step:", current_step)
    print("len(STEPS):", len(STEPS))
    if current_step == len(STEPS) - 1:
        return HTTPException(status_code=400, detail="Update already finished")

    machines_list = machine_manager_api.get_machines(machine_manager_url)
    # Random machines list to not make any assumption about list of machines, can be commented
    random.shuffle(machines_list)
    machines_len = len(machines_list)

    print("machines_len: ", machines_len)
    print("machines_list: ", machines_list)



    next_progress = STEPS[current_step + 1]
    newer_machines = list(filter(lambda machine: machine.version >= version, machines_list))
    older_machines = list(filter(lambda machine: machine.version < version, machines_list))

    all_to_update = round(next_progress * machines_len)
    already_updated = len(newer_machines)
    rest_to_update = all_to_update - already_updated

    print("all_to_update: ", all_to_update)
    print("already_updated: ", already_updated)
    print("rest_to_update: ", rest_to_update)
    print("len(older_machines): ", len(older_machines))
    print("older_machines:", len(older_machines))
    print("next_progress", next_progress)

    for i in range(rest_to_update):
        machine = older_machines[i]

        print("update machine: ", machine.instance_id)
        machine_manager_api.deploy_linter_instance(machine_manager_url, version, machine.instance_id)

    updates_progress[version] = next_progress

    return "ok"

@update_manager_app.get("/status")
def status(version: str):
    global updates_progress

    return updates_progress.get(version, 0)
