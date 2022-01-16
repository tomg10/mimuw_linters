from fastapi import FastAPI
from schema import LinterRequest, LinterResponse

test_linter_1_app = FastAPI()

@test_linter_1_app.get("/")
def health_check():
    return "ok"

@test_linter_1_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    return LinterResponse(result="ok", errors=[], debug=["version 1.0"])
