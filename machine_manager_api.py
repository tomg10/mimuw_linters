import json
import requests
import dataclasses

from schema import ExistingInstance


def get_linters(url, language=None):
    full_url = f"{url}/linters"
    if language:
        full_url += f"?language={language}"

    result_raw = requests.get(full_url).json()
    return [ExistingInstance.from_json(json.dumps(elem)) for elem in result_raw]


def deploy_linter_instance(url, languages, instance_id=None):
    full_url = f"{url}/deploy-linter-version"
    if instance_id:
        full_url += f"?instance_id={instance_id}"
    return requests.post(full_url, json=languages).json()


def kill_linter_instance(url, instance_id):
    return requests.post(f"{url}/kill-linter?instance_id={instance_id}").json()
