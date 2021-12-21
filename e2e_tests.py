import unittest

from fastapi.testclient import TestClient

import deploy_utils
import linter_api
import machine_manager_api
from linter import linter_app
from schema import LinterRequest, LinterResponse

linter_client = TestClient(linter_app)


class E2eTests(unittest.TestCase):
    @staticmethod
    def start_machine_manager():
        _, machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")
        return machine_manager_url

    def setUp(self) -> None:
        self.machine_manager_url = E2eTests.start_machine_manager()

    def test_spawning_linters(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0", None)
        result = machine_manager_api.get_machines(self.machine_manager_url)
        self.assertEqual(10, len(result))

        for linter_instance in result:
            response: LinterResponse = LinterResponse.from_dict(
                linter_api.validate(linter_instance.address, LinterRequest(language="python", code="x=5")))
            self.assertEqual("ok", response.result)
