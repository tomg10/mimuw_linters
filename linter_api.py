import dataclasses

import requests

from schema import LinterRequest


def validate(url, request: LinterRequest):
    return requests.post(f"{url}/validate", json=dataclasses.asdict(request)).json()
