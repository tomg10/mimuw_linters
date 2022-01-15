import deploy_utils
import killable_linter_proxy_api
import local_linter_deployer
from schema import ExistingInstance

linters = {}
linters_urls = {}


def kill_linter_instance(instance_id):
    linters.pop(instance_id).kill()
    local_linter_deployer.kill_linter_instance(instance_id)


def deploy_linter_instance(linter_version, instance_id=None):
    print(f"deploying killable proxy with version {linter_version}")
    linter_instance = local_linter_deployer.deploy_linter_instance(linter_version, instance_id)
    if instance_id is None:
        process, url = deploy_utils.start_fast_api_app("killable_linter_proxy")
        killable_linter_proxy_api.set_linter_url(url, linter_instance.address)
        linters[linter_instance.instance_id] = process
        linters_urls[linter_instance.instance_id] = url
    return ExistingInstance(instance_id=linter_instance.instance_id, version=linter_version,
                            address=linters_urls[linter_instance.instance_id])
