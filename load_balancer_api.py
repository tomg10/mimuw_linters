import dataclasses
import requests

from schema import LinterRequest


def validate(url, request: LinterRequest, machine_manager_url: str):
    return requests.post(f"{url}/validate/?machine_manager_url={machine_manager_url}", json=dataclasses.asdict(request)).json()
