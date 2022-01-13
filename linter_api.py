import dataclasses

import requests

from schema import LinterRequest


def validate(url, request: LinterRequest, timeout: int = 1):
    return requests.post(f"{url}/validate", json=dataclasses.asdict(request), timeout = timeout).json()
