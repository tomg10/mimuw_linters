import uuid
import os

import deploy_utils
import linter_api
from schema import ExistingInstance
from fastapi import HTTPException

linters = {}


def kill_linter_instance(instance_id):
    print(f"killing instance {instance_id}")
    linters.pop(instance_id).kill()


def deploy_linter_instance(linter_version, instance_id=None):
    # If we don't start the new linter properly we keep the old one alive.
    scheduled_to_kill = False
    if instance_id is None:
        instance_id = str(uuid.uuid4())
    else:
        scheduled_to_kill = True

    print(f"deploying linter instance with version {linter_version} on instance {instance_id}")
    process, address = deploy_utils.start_fast_api_app("linter")

    path_to_binary = f"./linters/python/bin/linter_{linter_version}"
    if not os.path.exists(path_to_binary):
        raise HTTPException(status_code=400, detail=f"Linter version {linter_version} does not exist in path {path_to_binary}!")

    if scheduled_to_kill:
        print(f"killing linter with instance_id {instance_id}, to start a new one with version {linter_version}")
        kill_linter_instance(instance_id)

    linter_api.set_binary(address, path_to_binary)
    linters[instance_id] = process

    return ExistingInstance(instance_id=instance_id, address=address, version=linter_version)
