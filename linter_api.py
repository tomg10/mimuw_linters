import dataclasses

import requests

from schema import LinterRequest


def validate(url, request: LinterRequest):
    return requests.post(f"{url}/validate", json=dataclasses.asdict(request)).json()


def set_binary(url, path_to_binary: str):
    return requests.post(f"{url}/set_binary?path_to_binary={path_to_binary}").json()
