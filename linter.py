from dataclasses import dataclass
from typing import Optional, List

from fastapi import FastAPI

from schema import LinterRequest, LinterResponse

linter_app = FastAPI()


@linter_app.get("/")
def health_check() -> str:
    return "ok"


@linter_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    return LinterResponse(result="ok", errors=[])

print("started linter instance!")