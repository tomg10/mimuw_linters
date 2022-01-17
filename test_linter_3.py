from fastapi import FastAPI
from multiprocessing import Lock

from schema import LinterRequest, LinterResponse

test_linter_3_app = FastAPI()
lock = Lock()

responses_count = 0


@test_linter_3_app.get("/")
def health_check():
    return "ok"


@test_linter_3_app.get("/supported_languages")
def get_supported_languages() -> [str]:
    return ["python", "java"]


@test_linter_3_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    global responses_count

    try:
        lock.acquire()
        responses_count += 1
    finally:
        lock.release()

    return LinterResponse(result="ok", errors=[], test_logging=[f"Current responses_count: {responses_count}"])
