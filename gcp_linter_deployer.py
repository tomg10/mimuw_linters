import uuid
import logging
import random
from logging.config import dictConfig

from configs.machine_manager.logging_config import log_config
from configs.machine_manager import config
from schema import ExistingInstance
import gcp_utils

dictConfig(log_config)
logger = logging.getLogger("gcp_linter_deployer_logger")

linters = {}  # instance_id -> (machine_name, docker_container_id)
machines = {}  # machine_name -> [machine_ip, number_of_linters_on_machine]
next_machine_number = 1


def kill_linter_instance(instance_id):
    logger.debug(f"killing instance {instance_id}")

    machine_name = linters[instance_id][0]
    container_id = linters[instance_id][1]
    gcp_utils.kill_linter(machine_name, container_id)

    linters.pop(instance_id)
    machines[machine_name][1] -= 1

    if machines[machine_name][1] <= 0:
        logger.info(f"Machine {machine_name} killed its last linter. Destroying the machine to not go bankrupt!")
        gcp_utils.delete_machine(machine_name)
        machines.pop(machine_name)


def find_or_create_free_machine():
    global next_machine_number

    for name, info in machines.items():
        if info[1] < config.max_linters_on_machine:
            return info[0], name

    new_machine_name = f"linter-machine-{next_machine_number}"
    logger.info(f"Creating new machine with name {new_machine_name} as others are full of linters!")
    ip = gcp_utils.create_machine(new_machine_name)
    next_machine_number += 1

    machines[new_machine_name] = [ip, 0]
    return ip, new_machine_name


def deploy_linter_instance(linter_version, instance_id=None):
    # If we don't start the new linter properly we keep the old one alive.
    scheduled_to_kill = False
    if instance_id is None:
        instance_id = str(uuid.uuid4())
    else:
        scheduled_to_kill = True

    logger.info(f"deploying linter instance with version {linter_version} on instance {instance_id}")
    ip, name = find_or_create_free_machine()
    logger.debug(f"deploying linter on machine {machines}")
    port = random.randint(10000, 20000)
    container_id = gcp_utils.start_linter(ip, name, linter_version, port)

    machines[name][1] += 1
    logger.info(f"Deployment of linter version {linter_version} on machine {name} with ip {ip} successful.")

    if scheduled_to_kill:
        logger.debug(f"killing linter with instance_id {instance_id}, to start a new one with version {linter_version}")
        kill_linter_instance(instance_id)

    linters[instance_id] = (name, container_id)

    return ExistingInstance(instance_id=instance_id,
                            address=f"http://{ip}:{port}",
                            version=linter_version,
                            languages=[])
