import unittest
import os
from fastapi.testclient import TestClient

import deploy_utils
import killable_linter_proxy_api
import linter_api
import update_manager_api
import load_balancer_api
import machine_manager_api
from linter import linter_app
from schema import LinterRequest

linter_client = TestClient(linter_app)


class E2eTests(unittest.TestCase):
    @staticmethod
    def set_linter_test_logging():
        os.environ["LINTER_TEST_LOGGING"] = "true"

    @staticmethod
    def unset_linter_test_logging():
        os.environ.pop("LINTER_TEST_LOGGING")

    def setUp(self) -> None:
        E2eTests.set_linter_test_logging()
        os.environ["MACHINE_MANAGER_DEPLOY_BACKEND"] = "local"
        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")
        os.environ["LOAD_BALANCER_MACHINE_MANAGER_URL"] = self.machine_manager_url
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")
        self.update_manager_process, self.update_manager_url = deploy_utils.start_fast_api_app("update_manager")
        self.killable_linter_proxies = []

    def tearDown(self) -> None:
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        for linter in linters:
            machine_manager_api.kill_linter_instance(self.machine_manager_url, linter.instance_id)

        for proxy_process, proxy_url in self.killable_linter_proxies:
            deploy_utils.stop_fast_api_app(proxy_process)

        deploy_utils.stop_fast_api_app(self.update_manager_process)
        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        deploy_utils.stop_fast_api_app(self.machine_manager_process)

        E2eTests.unset_linter_test_logging()

    def restart_machine_manager_with_deploy_backend(self, deploy_backend_name):
        deploy_utils.stop_fast_api_app(self.machine_manager_process)
        os.environ["MACHINE_MANAGER_DEPLOY_BACKEND"] = deploy_backend_name
        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")

        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        os.environ["LOAD_BALANCER_MACHINE_MANAGER_URL"] = self.machine_manager_url
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")

    def create_linter_instances(self, n: int, version: str, instance_id: str = None):
        for i in range(n):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, version, instance_id)

    def test_getting_linters(self):
        self.create_linter_instances(10, "1.0")
        result = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(10, len(result))

    def test_running_linter_binary_on_flawed_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")

        response = load_balancer_api.validate(self.load_balancer_url,
                                              LinterRequest(language="python", code="x=5\nx =5\nx= 5"))
        self.assertEqual("fail", response.result)
        self.assertEqual(4, len(response.errors))

    def test_running_linter_binary_on_flawless_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")

        response = load_balancer_api.validate(self.load_balancer_url,
                                              LinterRequest(language="python", code="x = 5"))
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

    def test_spawning_linters(self):
        self.create_linter_instances(10, "1.0")
        result = machine_manager_api.get_linters(self.machine_manager_url)

        for linter_instance in result:
            response = linter_api.validate(linter_instance.address,
                                           LinterRequest(language="python", code="x = 5"))
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

    def test_replacing_linter_with_nonexistent_version(self):
        self.create_linter_instances(1, "1.0")
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual("1.0", linters[0].version)

        with self.assertRaises(Exception):
            self.create_linter_instances(1, "1.0_nonexistent", linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual("1.0", linters[0].version)

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
        response = load_balancer_api.validate(self.load_balancer_url,
                                              LinterRequest(language="python", code="x = 5"))

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available", response.errors[0])

    def test_load_balancer_equal_split(self):
        self.create_linter_instances(10, "1.0")

        for i in range(100):
            response = load_balancer_api.validate(self.load_balancer_url,
                                                  LinterRequest(language="python", code="x = 5"))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 10 + 1}", response.test_logging[0])

    def test_setting_path_to_linter_binary(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, "1.0")

        response = load_balancer_api.validate(self.load_balancer_url,
                                              LinterRequest(language="python", code="x = 5"))
        self.assertEqual("Current path to linter binary: ./linters/python/bin/linter_1.0", response.test_logging[1])

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

        self.assertEqual(round(n * step), how_many_updated)
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

    # TODO update -> rollback -> update

    def test_killable_proxy_can_be_killed(self):
        self.restart_machine_manager_with_deploy_backend(deploy_backend_name='killable_proxy')
        linter_instance = machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version='1.0')
        response = load_balancer_api.validate(self.load_balancer_url,
                                              request=LinterRequest(code='var x = a', language='python'))
        self.assertEqual("ok", response.result)
        killable_linter_proxy_api.set_is_killed(linter_instance.address)
        response = load_balancer_api.validate(self.load_balancer_url,
                                              request=LinterRequest(code='var x = a', language='python'))
        self.assertEqual("fail", response.result)
        self.assertEqual(["No linter instance was able to handle request"], response.errors)

    def test_two_killed_linters_do_not_cause_outages(self):
        self.restart_machine_manager_with_deploy_backend(deploy_backend_name='killable_proxy')
        linter_instance1 = machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version='1.0')
        linter_instance2 = machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version='1.0')
        linter_instance3 = machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version='1.0')
        response = load_balancer_api.validate(self.load_balancer_url,
                                              request=LinterRequest(code='var x = a', language='python'))
        self.assertEqual("ok", response.result)
        killable_linter_proxy_api.set_is_killed(linter_instance1.address)
        killable_linter_proxy_api.set_is_killed(linter_instance2.address)
        for i in range(10):
            response = load_balancer_api.validate(self.load_balancer_url,
                                                  request=LinterRequest(code='var x = a', language='python'))
            self.assertEqual("ok", response.result)


if __name__ == "__main__":
    unittest.main()
