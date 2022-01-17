import time
import unittest
import os
from fastapi.testclient import TestClient

import deploy_utils
import health_check_api
import killable_linter_proxy_api
import linter_api
import update_manager_api
import load_balancer_api
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
    health_check_timeout = 0.5
    health_check_repetition_period = 1.2

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

    def start_health_check(self):
        os.environ["HEALTH_CHECK_TIMEOUT"] = str(E2eTests.health_check_timeout)
        os.environ["HEALTH_CHECK_REPETITION_PERIOD"] = str(E2eTests.health_check_repetition_period)
        self.hc_process, self.hc_url = deploy_utils.start_fast_api_app("health_check")

    def stop_health_check(self):
        deploy_utils.stop_fast_api_app(self.hc_process)
        os.environ.pop("HEALTH_CHECK_TIMEOUT")
        os.environ.pop("HEALTH_CHECK_REPETITION_PERIOD")

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

    def test_getting_linters_for_all_languages(self):
        self.create_linter_instances(2, E2eTests.v1)
        self.create_linter_instances(1, E2eTests.v2)
        result = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(3, len(result))

    def test_getting_linters_for_one_language(self):
        self.create_linter_instances(2, E2eTests.v1)
        self.create_linter_instances(1, E2eTests.v2)
        self.create_linter_instances(1, E2eTests.v3)

        result = machine_manager_api.get_linters(self.machine_manager_url, "python")
        self.assertEqual(3, len(result))
        result = machine_manager_api.get_linters(self.machine_manager_url, "java")
        self.assertEqual(2, len(result))

    def test_running_linter_binary_on_flawed_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, E2eTests.v_real)

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawed_python_request)
        self.assertEqual("fail", response.result)
        self.assertEqual(4, len(response.errors))

    def test_running_linter_binary_on_flawless_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, E2eTests.v_real)

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

    def test_linter_was_run_on_correct_language(self):
        self.create_linter_instances(1, E2eTests.v_real)

        request = LinterRequest(language="python", code=E2eTests.flawless_python_request.code)
        response = load_balancer_api.validate(self.load_balancer_url, request)
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

        request.language = "java"
        response = load_balancer_api.validate(self.load_balancer_url, request)
        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("Missing class keyword in the program!", response.errors[0])

    def test_running_two_supported_lanugages_on_one_linter(self):
        self.create_linter_instances(1, E2eTests.v_real)

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_java_request)
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

    def test_spawning_linters(self):
        self.create_linter_instances(3, E2eTests.v_real)
        result = machine_manager_api.get_linters(self.machine_manager_url)

        for linter_instance in result:
            response = linter_api.validate(linter_instance.address, E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))

    def test_replacing_linter_with_different_version(self):
        self.create_linter_instances(1, E2eTests.v1)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(E2eTests.v1, linters[0].version)

        self.create_linter_instances(1, E2eTests.v2, linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(E2eTests.v2, linters[0].version)

    def test_replacing_linter_with_nonexistent_version(self):
        self.create_linter_instances(1, E2eTests.v1)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(E2eTests.v1, linters[0].version)

        with self.assertRaises(Exception):
            self.create_linter_instances(1, E2eTests.nonexistent_v, linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(E2eTests.v1, linters[0].version)

    def test_killing_linters(self):
        self.create_linter_instances(2, E2eTests.v_real)

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        id1 = linters[0].instance_id
        id2 = linters[1].instance_id

        machine_manager_api.kill_linter_instance(self.machine_manager_url, id1)

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(id2, linters[0].instance_id)

    def test_load_balancer_with_no_linters(self):
        response = load_balancer_api.validate(self.load_balancer_url,
                                              E2eTests.flawless_python_request)

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available for language python.", response.errors[0])

    def test_load_balancer_with_no_linters_for_given_language(self):
        self.create_linter_instances(2, E2eTests.v1)

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_java_request)
        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available for language java.", response.errors[0])

    def test_load_balancer_equal_split(self):
        self.create_linter_instances(4, E2eTests.v1)

        for i in range(40):
            response = load_balancer_api.validate(self.load_balancer_url,
                                                  E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 4 + 1}", response.test_logging[0])

    def test_load_balancer_equal_split_across_one_language(self):
        self.create_linter_instances(2, E2eTests.v1)
        self.create_linter_instances(2, E2eTests.v2)

        for i in range(40):
            response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 2 + 1}", response.test_logging[0])

    def single_manager_update(self, n: int, version: str, step: float, last_step: bool = False):
        if last_step:
            with self.assertRaises(Exception):
                update_manager_api.update(self.update_manager_url, self.machine_manager_url, version)
        else:
            response = update_manager_api.update(self.update_manager_url, self.machine_manager_url, version)
            self.assertEqual(response, "ok")

        machines = machine_manager_api.get_linters(self.machine_manager_url)
        how_many_updated = len(list(filter(lambda machine: machine.version >= version, machines)))
        update_status = update_manager_api.status(self.update_manager_url, version)

        self.assertEqual(round(n * step), how_many_updated)
        self.assertEqual(update_status, step)

    def test_update_manager_single_update(self):
        n = 10
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, E2eTests.v1)

        for step in steps:
            self.single_manager_update(n, E2eTests.v2, step)

        self.single_manager_update(n, E2eTests.v2, steps[-1], True)

    def test_update_manager_double_update(self):
        n = 10
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, E2eTests.v1)
        for step in steps[:1]:
            self.single_manager_update(n, E2eTests.v2, step)
            self.single_manager_update(n, E2eTests.v3, step)

    def single_manager_rollback(self, version: str):
        update_manager_api.rollback(self.update_manager_url, self.machine_manager_url, version)
        machines = machine_manager_api.get_linters(self.machine_manager_url)
        how_many_updated = len(list(filter(lambda machine: machine.version > version, machines)))
        update_status = update_manager_api.status(self.update_manager_url, version)

        self.assertEqual(0, how_many_updated)
        self.assertEqual(update_status, 0)

    def test_single_rollback(self):
        n = 10
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, E2eTests.v1)

        self.single_manager_update(n, E2eTests.v2, steps[0])
        self.single_manager_rollback(E2eTests.v1)

    def test_double_rollback(self):
        n = 10
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, E2eTests.v1)

        self.single_manager_update(n, E2eTests.v2, steps[0])
        self.single_manager_update(n, E2eTests.v2, steps[1])
        self.single_manager_update(n, E2eTests.v3, steps[0])
        self.single_manager_rollback(E2eTests.v1)

    def test_update_rollback_update(self):
        n = 2
        steps = [0.1, 0.5, 1]

        self.create_linter_instances(n, E2eTests.v1)

        for step in steps:
            self.single_manager_update(n, E2eTests.v2, step)

        self.single_manager_rollback(E2eTests.v1)

        for step in steps:
            self.single_manager_update(n, E2eTests.v2, step)

    def test_killable_proxy_can_be_killed(self):
        self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
        linter_instance = machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version=E2eTests.v_real)
        response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)

        killable_linter_proxy_api.set_is_killed(linter_instance.address)
        response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
        self.assertEqual("fail", response.result)
        self.assertEqual(["No linter instance was able to handle request"], response.errors)

    def test_two_killed_linters_do_not_cause_outages(self):
        self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
        linter_instance1 = machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version=E2eTests.v_real)
        linter_instance2 = machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version=E2eTests.v_real)
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version=E2eTests.v_real)
        
        response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)
        
        killable_linter_proxy_api.set_is_killed(linter_instance1.address)
        killable_linter_proxy_api.set_is_killed(linter_instance2.address)
        for i in range(10):
            response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)

    def test_opening_application_on_already_occupied_socket(self):
        machine_manager_process, _ = deploy_utils.start_fast_api_app("machine_manager", port=5000)
        load_balancer_process, _ = deploy_utils.start_fast_api_app("load_balancer", port=5000)

        deploy_utils.stop_fast_api_app(machine_manager_process)
        deploy_utils.stop_fast_api_app(load_balancer_process)

    def test_health_check_when_linters_work(self):
        try:
            self.create_linter_instances(2, E2eTests.v1)
            self.start_health_check()
            time.sleep(2)

            time.sleep(E2eTests.health_check_timeout * 2 + E2eTests.health_check_repetition_period)
            self.assertEqual(0, health_check_api.get_failures(self.hc_url))
        finally:
            self.stop_health_check()

    def test_health_check_when_one_linter_doesnt_work(self):
        try:
            self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
            linter_instance1 = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                                          linter_version=E2eTests.v_real)
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version=E2eTests.v_real)
            killable_linter_proxy_api.set_is_killed(linter_instance1.address)

            self.start_health_check()
            time.sleep(2)

            time.sleep(E2eTests.health_check_timeout * 2 + E2eTests.health_check_repetition_period)
            self.assertEqual(1, health_check_api.get_failures(self.hc_url))
        finally:
            self.stop_health_check()

    def test_health_check_restarts_linter_when_dead(self):
        try:
            self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
            linter_instance1 = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                                          linter_version=E2eTests.v_real)
            killable_linter_proxy_api.set_is_killed(linter_instance1.address)

            self.start_health_check()
            time.sleep(2)

            time.sleep(E2eTests.health_check_timeout * 2 + E2eTests.health_check_repetition_period)
            for i in range(2):
                response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
                self.assertEqual("ok", response.result)

            self.assertEqual(1, health_check_api.get_failures(self.hc_url))
        finally:
            self.stop_health_check()


if __name__ == "__main__":
    unittest.main()
