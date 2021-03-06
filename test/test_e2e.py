import unittest
from fastapi.testclient import TestClient
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import deploy_utils
import machine_manager_api
from linter import linter_app
from schema import LinterRequest

linter_client = TestClient(linter_app)


class E2eTests(unittest.TestCase):
    nonexistent_v = "1.0nonexistent"
    v_real = "0.0"  # Python + Java
    v1 = "1.0"  # Python
    v2 = "2.0"  # Java
    v3 = "3.0"  # Python + Java
    flawless_python_request = LinterRequest(language="python", code="x = 5")
    flawed_python_request = LinterRequest(language="python", code="x=5\nx =5\nx= 5")
    flawless_java_request = LinterRequest(language="java", code="class { x = 5; }")
    flawed_java_request = LinterRequest(language="java", code="x = 5")

    @staticmethod
    def set_linter_test_logging():
        os.environ["LINTER_TEST_LOGGING"] = "true"

    @staticmethod
    def unset_linter_test_logging():
        os.environ.pop("LINTER_TEST_LOGGING")

    @staticmethod
    def set_linter_test_aps_supported_versions():
        os.environ["LOCAL_DEPLOYER_SUPPORTED_VERSIONS"] = E2eTests.v_real + ":linter," + \
                                                          E2eTests.v1 + ":test_linter_1," + \
                                                          E2eTests.v2 + ":test_linter_2," + \
                                                          E2eTests.v3 + ":test_linter_3"

    def setUp(self) -> None:
        E2eTests.set_linter_test_logging()
        os.environ["MACHINE_MANAGER_DEPLOY_BACKEND"] = "local"
        E2eTests.set_linter_test_aps_supported_versions()
        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")

        os.environ["LOAD_BALANCER_MACHINE_MANAGER_URL"] = self.machine_manager_url
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")

        self.killable_linter_proxies = []

    def tearDown(self) -> None:
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        for linter in linters:
            machine_manager_api.kill_linter_instance(self.machine_manager_url, linter.instance_id)

        for proxy_process, proxy_url in self.killable_linter_proxies:
            deploy_utils.stop_fast_api_app(proxy_process)

        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        deploy_utils.stop_fast_api_app(self.machine_manager_process)

        E2eTests.unset_linter_test_logging()

    def restart_machine_manager_with_different_params(self, deploy_backend_name):
        deploy_utils.stop_fast_api_app(self.machine_manager_process)
        os.environ["MACHINE_MANAGER_DEPLOY_BACKEND"] = deploy_backend_name
        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")

        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        os.environ["LOAD_BALANCER_MACHINE_MANAGER_URL"] = self.machine_manager_url
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")

    def create_linter_instances(self, n: int, version: str, instance_id: str = None):
        for i in range(n):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, version, instance_id)


if __name__ == "__main__":
    unittest.main()
