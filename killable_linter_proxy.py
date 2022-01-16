from fastapi import FastAPI
import logging
from logging.config import dictConfig

from configs.linter_proxies.logging_config import log_config
import linter_api
from schema import LinterRequest, LinterResponse

dictConfig(log_config)
logger = logging.getLogger("killable_linter_proxy_logger")
killable_linter_proxy_app = FastAPI()

real_linter_url = None
is_killed = False


@killable_linter_proxy_app.get("/")
def health_check() -> str:
    return "ok"


@killable_linter_proxy_app.post("/set-is-killed")
def set_is_killed():
    global is_killed
    is_killed = True


@killable_linter_proxy_app.post("/set-linter-url")
def set_linter_url(linter_url):
    global real_linter_url
    real_linter_url = linter_url
    logger.info(f"Real linter url set: {real_linter_url}")


@killable_linter_proxy_app.post("/validate")
def validate_file(request: LinterRequest) -> LinterResponse:
    if is_killed:
        raise Exception("This linter is not working!")
    if real_linter_url is None:
        raise Exception("Real linter url is not set!")
    return linter_api.validate(url=real_linter_url, request=request)


logger.debug("started killable linter proxy instance!")
