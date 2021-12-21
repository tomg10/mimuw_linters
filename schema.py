from dataclasses import dataclass
from typing import List

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class LinterRequest:
    code: str
    language: str


@dataclass_json
@dataclass
class LinterResponse:
    result: str
    errors: List[str]


@dataclass_json
@dataclass
class ExistingInstance:
    instance_id: str
    address: str
