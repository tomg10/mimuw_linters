import json

import requests

from schema import ExistingInstance


def get_linters(url):
    result_raw = requests.get(f"{url}/linters").json()
    print(result_raw)
    return [ExistingInstance.from_json(json.dumps(elem)) for elem in result_raw]


def deploy_linter_instance(url, linter_version, instance_id=None):
    full_url = f"{url}/deploy-linter-version?linter_version={linter_version}"
    if instance_id:
        full_url += f"&instance_id={instance_id}"
    return requests.post(full_url).json()


def kill_linter_instance(url, instance_id):
    return requests.post(f"{url}/kill-linter?instance_id={instance_id}").json()
