from fastapi import FastAPI

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
    print(f"Usage: {usage}")
    return LinterResponse(result="ok", errors=[])


@linter_app.get("/private/usage")
def get_usage() -> int:
    return usage


print("started linter instance!")
