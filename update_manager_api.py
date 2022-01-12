import json

import requests

from schema import ExistingInstance


def update(url, machine_manager_url, version):
    full_url = f"{url}/update?machine_manager_url={machine_manager_url}&version={version}"
    return requests.post(full_url).json()


def status(url, version):
    full_url = f"{url}/status?version={version}"
    return requests.get(full_url).json()
