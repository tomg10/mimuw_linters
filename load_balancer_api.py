import dataclasses
import json

import requests

from schema import LinterRequest, LinterResponse


def validate(url, request: LinterRequest):
    response = requests.post(f"{url}/validate", json=dataclasses.asdict(request)).json()
    return LinterResponse.from_json(json.dumps(response))
