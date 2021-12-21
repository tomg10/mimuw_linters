from fastapi import FastAPI

from schema import LinterResponse, LinterRequest

load_balancer_app = FastAPI()


@load_balancer_app.get("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    return LinterResponse(result="ok", errors=[])
