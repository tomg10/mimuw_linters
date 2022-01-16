import json
import uuid
import os
import logging

import deploy_utils
from schema import ExistingInstance

logger = logging.getLogger("local_linter_deployer_logger")

linters = {}

versions_string = os.environ.get("LOCAL_DEPLOYER_SUPPORTED_VERSIONS", "1.0:linter")
versions = {}
for version in versions_string.split(','):
    versions[version.split(":")[0]] = version.split(":")[1]
logger.debug(f"supported_linter_versions: {json.dumps(versions, indent=2)}")


def kill_linter_instance(instance_id):
    logger.debug(f"killing instance {instance_id}")
    linters.pop(instance_id).kill()


def deploy_linter_instance(linter_version, instance_id=None):
    # If we don't start the new linter properly we keep the old one alive.
    scheduled_to_kill = False
    if instance_id is None:
        instance_id = str(uuid.uuid4())
    else:
        scheduled_to_kill = True

    if linter_version not in versions:
        raise Exception(f"unsupported linter version: {linter_version}")

    logger.debug(f"deploying linter instance with version {linter_version} on instance {instance_id}")
    process, address = deploy_utils.start_fast_api_app(versions[linter_version])

    if scheduled_to_kill:
        logger.debug(f"killing linter with instance_id {instance_id}, to start a new one with version {linter_version}")
        kill_linter_instance(instance_id)

    linters[instance_id] = process

    return ExistingInstance(instance_id=instance_id, address=address, version=linter_version)
