import dataclasses

import requests

from schema import LinterRequest


def validate(url, request: LinterRequest):
    return requests.post(f"{url}/validate", json=dataclasses.asdict(request)).json()


def get_linter_usage(url):
    return requests.get(f"{url}/private/usage").json()

