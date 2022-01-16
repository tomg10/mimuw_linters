import dataclasses
import json

import requests

from schema import LinterRequest, LinterResponse


def validate(url, request: LinterRequest, machine_manager_url: str) -> LinterResponse:
    response = requests.post(f"{url}/validate?machine_manager_url={machine_manager_url}", json=dataclasses.asdict(request)).json()
    return LinterResponse.from_json(json.dumps(response))
