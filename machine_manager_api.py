import json
import requests

from typing import Union
from schema import ExistingInstance

def get_linters(url):
    full_url = f"{url}/linters"
    result_raw = requests.get(full_url).json()
    return [ExistingInstance.from_json(json.dumps(elem)) for elem in result_raw]


def deploy_linter_instance(url, linter_version, instance_id=None) -> ExistingInstance:
    full_url = f"{url}/deploy-linter-version?linter_version={linter_version}"
    if instance_id is not None:
        full_url += f"&instance_id={instance_id}"
    response = requests.post(full_url)

    if response.status_code == 200:
        return ExistingInstance.from_json(json.dumps(response.json()))
    else:
        raise Exception(response.json())


def kill_linter_instance(url, instance_id):
    return requests.post(f"{url}/kill-linter?instance_id={instance_id}").json()
