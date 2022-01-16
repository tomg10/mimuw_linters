from fastapi import FastAPI
from schema import LinterRequest, LinterResponse

test_linter_3_app = FastAPI()


@test_linter_3_app.get("/")
def health_check():
    return "ok"


@test_linter_3_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    return LinterResponse(result="ok", errors=[], test_logging=["version 3.0"])
