import unittest
import os

from fastapi.testclient import TestClient

import deploy_utils
import linter_api
import update_manager_api
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

        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")
        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")
        self.update_manager_process, self.update_manager_url = deploy_utils.start_fast_api_app("update_manager")
        load_balancer_api.set_machine_manager(self.load_balancer_url, self.machine_manager_url)

    def tearDown(self) -> None:
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        for linter in linters:
            machine_manager_api.kill_linter_instance(self.machine_manager_url, linter.instance_id)

        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        deploy_utils.stop_fast_api_app(self.machine_manager_process)
        deploy_utils.stop_fast_api_app(self.update_manager_process)

        E2eTests.unset_linter_debug_mode()

    def create_linter_instances(self, n: int, version: str, instance_id: str = None):
        for i in range(n):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, version, instance_id)

    def test_getting_linters(self):
        self.create_linter_instances(10, "1.0")
        result = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(10, len(result))

    def test_spawning_linters(self):
        self.create_linter_instances(10, "1.0")
        result = machine_manager_api.get_linters(self.machine_manager_url)

        for linter_instance in result:
            response: LinterResponse = LinterResponse.from_dict(
                linter_api.validate(linter_instance.address, LinterRequest(language="python", code="x=5")))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))

    def test_replacing_linter_with_different_version(self):
        self.create_linter_instances(1, "1.0")
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual("1.0", linters[0].version)

        self.create_linter_instances(1, "2.0", linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual("2.0", linters[0].version)

    def test_killing_linters(self):
        self.create_linter_instances(2, "1.0")

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        id1 = linters[0].instance_id
        id2 = linters[1].instance_id

        machine_manager_api.kill_linter_instance(self.machine_manager_url, id1)

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(id2, linters[0].instance_id)

    def test_load_balancer_with_no_linters(self):
        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url, LinterRequest(language="python", code="x=5")))

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available", response.errors[0])

    def test_load_balancer_equal_split(self):
        self.create_linter_instances(10, "1.0")

        for i in range(100):
            response: LinterResponse = LinterResponse.from_dict(
                load_balancer_api.validate(self.load_balancer_url, LinterRequest(language="python", code="x=5")))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 10 + 1}", response.debug[0])

    def single_manager_update(self, n: int, version: str, step: float, last_step: bool = False):
        response = update_manager_api.update(self.update_manager_url, self.machine_manager_url, version)
        machines = machine_manager_api.get_linters(self.machine_manager_url)
        how_many_updated = len(list(filter(lambda machine: machine.version >= version, machines)))
        update_status = update_manager_api.status(self.update_manager_url, version)

        if last_step:
            self.assertEqual(response["status_code"], 400)
            self.assertEqual(response["detail"], "Update already finished")
        else:
            self.assertEqual(response, "ok")

        self.assertEqual(n * step, how_many_updated)
        self.assertEqual(update_status, step)

    def test_update_manager_single_update(self):
        n = 10
        v1 = "1.0"
        v2 = "2.0"
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, v1)

        for step in steps:
            self.single_manager_update(n, v2, step)

        self.single_manager_update(n, v2, steps[-1], True)

    def test_update_manager_double_update(self):
        n = 10
        v1 = "1.0"
        v2 = "2.0"
        v3 = "3.0"
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, v1)

        for step in steps[:1]:
            self.single_manager_update(n, v2, step)
            self.single_manager_update(n, v3, step)

    def single_manager_rollback(self, version: str):
        update_manager_api.rollback(self.update_manager_url, self.machine_manager_url, version)
        machines = machine_manager_api.get_linters(self.machine_manager_url)
        how_many_updated = len(list(filter(lambda machine: machine.version > version, machines)))
        update_status = update_manager_api.status(self.update_manager_url, version)

        self.assertEqual(0, how_many_updated)
        self.assertEqual(update_status, 0)

    def test_single_rollback(self):
        n = 10
        v1 = "1.0"
        v2 = "2.0"
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, v1)

        self.single_manager_update(n, v2, steps[0])
        self.single_manager_rollback(v1)

    def test_double_rollback(self):
        n = 10
        v1 = "1.0"
        v2 = "2.0"
        v3 = "3.0"
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, v1)

        self.single_manager_update(n, v2, steps[0])
        self.single_manager_update(n, v2, steps[1])
        self.single_manager_update(n, v3, steps[0])
        self.single_manager_rollback(v1)


if __name__ == "__main__":
    unittest.main()
