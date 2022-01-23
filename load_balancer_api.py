import dataclasses
import json

import requests

from schema import LinterRequest, LinterResponse


def validate(url, request: LinterRequest) -> LinterResponse:
    response = requests.post(f"{url}/validate", json=dataclasses.asdict(request))
    if response.status_code != 200:
        raise Exception(f"Error in update_manager: {response.json()}")

    return LinterResponse.from_json(json.dumps(response.json()))
