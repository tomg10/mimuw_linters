from fastapi import FastAPI

from services_addresses import get_env_or_raise
from schema import LinterRequest, LinterResponse

linter_app = FastAPI()

usage = 0


@linter_app.get("/")
def health_check() -> str:
    return "ok linter"


@linter_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    global usage

    usage += 1

    debug = []
    if get_env_or_raise("LINTER_DEBUG"):
        debug = [f"Current usage: {usage}"]

    return LinterResponse(result="ok", errors=[], debug=debug)


print("started linter instance!")
