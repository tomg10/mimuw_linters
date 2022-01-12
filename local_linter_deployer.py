import uuid

import deploy_utils
from schema import ExistingInstance

linters = {}


def kill_linter_instance(instance_id):
    print(f"killing instance {instance_id}")
    linters.pop(instance_id).kill()


def deploy_linter_instance(linter_version, instance_id=None):
    if instance_id is None:
        instance_id = str(uuid.uuid4())
    else:
        print(f"killing linter with instance_id {instance_id}, to start a new one with version {linter_version}")
        kill_linter_instance(instance_id)
    print(f"deploying linter instance with version {linter_version} on instance {instance_id}")
    process, address = deploy_utils.start_fast_api_app("linter")
    linters[instance_id] = process

    return ExistingInstance(instance_id=instance_id, address=address, version=linter_version)
