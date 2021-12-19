import os
import random
import subprocess
import time
import uuid

import deploy_utils
from schema import ExistingInstance

machines = {}

def kill_linter_instance(instance_id):
    print(f"killing instance {instance_id}")
    machines.pop(instance_id).kill()

def deploy_linter_instance(linter_version, instance_id = None):
    if instance_id is None:
        instance_id = str(uuid.uuid4())
    else:
        kill_linter_instance(instance_id)
    print(f"deploying linter instance with version {linter_version} on instance {instance_id}")
    process, address = deploy_utils.start_fast_api_app("linter")
    machines[instance_id] = process
    return ExistingInstance(instance_id=instance_id, address=address)