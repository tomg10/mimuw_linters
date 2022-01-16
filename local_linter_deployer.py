import uuid
import os
import traceback

import deploy_utils
import linter_api
from schema import ExistingInstance

linters = {}


def kill_linter_instance(instance_id):
    print(f"killing instance {instance_id}")
    deploy_utils.stop_fast_api_app(linters.pop(instance_id))


def deploy_linter_instance(languages, instance_id=None):
    # If we don't start the new linter properly we keep the old one alive.
    scheduled_to_kill = False
    if instance_id is None:
        instance_id = str(uuid.uuid4())
    else:
        scheduled_to_kill = True

    print(f"deploying linter instance with languages {languages} on instance {instance_id}")
    process, address = deploy_utils.start_fast_api_app("linter")

    try:
        for language, version in languages.items():
            path_to_binary = f"./linters/{language}/bin/linter_{version}"
            if not os.path.exists(path_to_binary):
                raise ValueError(f"Linter version {version} for language {language} does not exist in path {path_to_binary}!")

            linter_api.set_binary(address, language, path_to_binary)

        if scheduled_to_kill:
            print(f"killing linter with instance_id {instance_id}, to start a new one with languages {languages}")
            kill_linter_instance(instance_id)
    except Exception as ex:
        print(traceback.format_exc())
        print(f"Linter setup was not successful due to an error. Killing linter with instance_id {instance_id}...")
        deploy_utils.stop_fast_api_app(process)
        raise ex

    linters[instance_id] = process

    return ExistingInstance(instance_id=instance_id, address=address, languages=languages)
