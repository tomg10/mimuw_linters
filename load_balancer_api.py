import dataclasses

import requests

from schema import LinterRequest


def set_machine_manager(url, machine_manager_url: str):
    return requests.get(f"{url}/set_machine_manager/?machine_manager={machine_manager_url}").json()


def validate(url, request: LinterRequest):
    return requests.post(f"{url}/validate", json=dataclasses.asdict(request)).json()
