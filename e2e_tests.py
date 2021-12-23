import unittest
import os

from fastapi.testclient import TestClient

import deploy_utils
import linter_api
import load_balancer_api
import machine_manager_api
from linter import linter_app
from schema import LinterRequest, LinterResponse

linter_client = TestClient(linter_app)


class E2eTests(unittest.TestCase):
    @staticmethod
    def set_linter_debug_mode():
        os.environ["LINTER_DEBUG"] = "true"

    @staticmethod
    def unset_linter_debug_mode():
        os.environ.pop("LINTER_DEBUG")

    def setUp(self) -> None:
        E2eTests.set_linter_debug_mode()

        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")
        load_balancer_api.set_machine_manager(self.load_balancer_url, self.machine_manager_url)

    def tearDown(self) -> None:
        linters = machine_manager_api.get_machines(self.machine_manager_url)
        for linter in linters:
            machine_manager_api.kill_linter_instance(self.machine_manager_url, linter.instance_id)

        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        deploy_utils.stop_fast_api_app(self.machine_manager_process)

        E2eTests.unset_linter_debug_mode()

    def test_getting_linters(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")
        result = machine_manager_api.get_machines(self.machine_manager_url)
        self.assertEqual(10, len(result))

    def test_spawning_linters(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")
        result = machine_manager_api.get_machines(self.machine_manager_url)

        for linter_instance in result:
            response: LinterResponse = LinterResponse.from_dict(
                linter_api.validate(linter_instance.address, LinterRequest(language="python", code="x=5")))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))

    def test_replacing_linter_with_different_version(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")
        machines = machine_manager_api.get_machines(self.machine_manager_url)
        self.assertEqual("1.0", machines[0].version)

        machine_manager_api.deploy_linter_instance(self.machine_manager_url, "2.0", machines[0].instance_id)
        machines = machine_manager_api.get_machines(self.machine_manager_url)
        self.assertEqual(1, len(machines))
        self.assertEqual("2.0", machines[0].version)

    def test_killing_linters(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")

        machines = machine_manager_api.get_machines(self.machine_manager_url)
        id1 = machines[0].instance_id
        id2 = machines[1].instance_id

        machine_manager_api.kill_linter_instance(self.machine_manager_url, id1)

        machines = machine_manager_api.get_machines(self.machine_manager_url)
        self.assertEqual(1, len(machines))
        self.assertEqual(id2, machines[0].instance_id)

    def test_load_balancer_with_no_machines(self):
        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url, LinterRequest(language="python", code="x=5")))

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter machine available", response.errors[0])

    def test_load_balancer_equal_split(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")

        for i in range(100):
            response: LinterResponse = LinterResponse.from_dict(
                load_balancer_api.validate(self.load_balancer_url, LinterRequest(language="python", code="x=5")))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 10 + 1}", response.debug[0])

