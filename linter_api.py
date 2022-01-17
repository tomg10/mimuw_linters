import dataclasses
import json
import requests

from schema import LinterRequest, LinterResponse


def validate(url, request: LinterRequest, timeout: int = 1) -> LinterResponse:
    response = requests.post(f"{url}/validate", json=dataclasses.asdict(request), timeout=timeout).json()
    return LinterResponse.from_json(json.dumps(response))


def get_supported_languages(url) -> [str]:
    response = requests.get(f"{url}/supported_languages").json()
    return response
