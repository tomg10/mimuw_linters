import unittest

from fastapi.testclient import TestClient

import deploy_utils
import linter_api
import load_balancer_api
import machine_manager_api
from linter import linter_app
from schema import LinterRequest, LinterResponse

linter_client = TestClient(linter_app)


class E2eTests(unittest.TestCase):
    def stop_machine_manager(self):
        deploy_utils.stop_fast_api_app(self.machine_manager_process)

    def stop_load_balancer(self):
        deploy_utils.stop_fast_api_app(self.load_balancer_process)

    def setUp(self) -> None:
        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")
        load_balancer_api.set_machine_manager(self.load_balancer_url, self.machine_manager_url)

    def tearDown(self) -> None:
        self.stop_load_balancer()
        self.stop_machine_manager()

    def test_spawning_linters(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0", None)
        result = machine_manager_api.get_machines(self.machine_manager_url)
        self.assertEqual(10, len(result))

        for linter_instance in result:
            response: LinterResponse = LinterResponse.from_dict(
                linter_api.validate(linter_instance.address, LinterRequest(language="python", code="x=5")))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))

    def test_load_balancer_with_no_machines(self):
        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url, LinterRequest(language="python", code="x=5")))

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter machine available", response.errors[0])

    def test_load_balancer(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0", None)
        result = machine_manager_api.get_machines(self.machine_manager_url)

        for i in range(100):
            response: LinterResponse = LinterResponse.from_dict(
                load_balancer_api.validate(self.load_balancer_url, LinterRequest(language="python", code="x=5")))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))

        for linter_instance in result:
            response: int = linter_api.get_linter_usage(linter_instance.address)
            self.assertEqual(10, response)

