import logging
from logging.config import dictConfig

from configs.machine_manager.logging_config import log_config
import deploy_utils
import killable_linter_proxy_api
import local_linter_deployer
from schema import ExistingInstance

dictConfig(log_config)
logger = logging.getLogger("killable_proxy_deployer_logger")

linters_proxies = {}
linters_proxies_urls = {}


def kill_linter_instance(instance_id):
    linters_proxies.pop(instance_id).kill()
    local_linter_deployer.kill_linter_instance(instance_id)


def deploy_linter_instance(linter_version, instance_id=None):
    logger.debug(f"deploying killable proxy with version {linter_version}")
    if instance_id is not None:
        linters_proxies.pop(instance_id).kill()

    linter_instance = local_linter_deployer.deploy_linter_instance(linter_version, instance_id)
    process, url = deploy_utils.start_fast_api_app("killable_linter_proxy")
    killable_linter_proxy_api.set_linter_url(url, linter_instance.address)
    linters_proxies[linter_instance.instance_id] = process
    linters_proxies_urls[linter_instance.instance_id] = url

    return ExistingInstance(instance_id=linter_instance.instance_id, version=linter_version,
                            address=linters_proxies_urls[linter_instance.instance_id], languages=[])
