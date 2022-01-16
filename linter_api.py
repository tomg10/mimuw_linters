import dataclasses
import json

import requests

from schema import LinterRequest, LinterResponse


def validate(url, request: LinterRequest, timeout: int = 1) -> LinterResponse:
    response = requests.post(f"{url}/validate", json=dataclasses.asdict(request), timeout=timeout).json()
    return LinterResponse.from_json(json.dumps(response))


def set_binary(url, path_to_binary: str):
    return requests.post(f"{url}/set_binary?path_to_binary={path_to_binary}").json()
