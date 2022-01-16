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
    def set_linter_test_logging():
        os.environ["LINTER_TEST_LOGGING"] = "true"

    @staticmethod
    def unset_linter_test_logging():
        os.environ.pop("LINTER_TEST_LOGGING")

    def setUp(self) -> None:
        E2eTests.set_linter_test_logging()

        self.machine_manager_process, self.machine_manager_url = deploy_utils.start_fast_api_app("machine_manager")
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")
        self.update_manager_process, self.update_manager_url = deploy_utils.start_fast_api_app("update_manager")

    def tearDown(self) -> None:
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        for linter in linters:
            machine_manager_api.kill_linter_instance(self.machine_manager_url, linter.instance_id)

        deploy_utils.stop_fast_api_app(self.update_manager_process)
        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        deploy_utils.stop_fast_api_app(self.machine_manager_process)

        E2eTests.unset_linter_test_logging()

    def test_getting_linters_for_all_languages(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        result = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(10, len(result))

    def test_getting_linters_for_one_language(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"java": "1.0"})
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0", "java": "1.0"})

        result = machine_manager_api.get_linters(self.machine_manager_url, "python")
        self.assertEqual(3, len(result))
        result = machine_manager_api.get_linters(self.machine_manager_url, "java")
        self.assertEqual(2, len(result))

    def test_running_linter_binary_on_flawed_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})

        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="python", code="x=5\nx =5\nx= 5"),
                                       self.machine_manager_url))
        self.assertEqual("fail", response.result)
        self.assertEqual(4, len(response.errors))

    def test_running_linter_binary_on_flawless_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})

        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="python", code="x = 5"),
                                       self.machine_manager_url))
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

    def test_running_linter_binary_on_unknown_language(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})

        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="Kotlin", code="x = 5"),
                                       self.machine_manager_url))
        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available for Kotlin language at the moment.", response.errors[0])

    def test_running_linter_binary_on_two_languages(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0", "java": "1.0"})

        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="python", code="x = 5"),
                                       self.machine_manager_url))
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="java", code="int x = 5"),
                                       self.machine_manager_url))
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

    def test_spawning_linters(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        result = machine_manager_api.get_linters(self.machine_manager_url)

        for linter_instance in result:
            response: LinterResponse = LinterResponse.from_dict(
                linter_api.validate(linter_instance.address,
                                    LinterRequest(language="python", code="x = 5")))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))

    def test_replacing_linter_with_different_nonexistent_version(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual("1.0", linters[0].languages["python"])

        response = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                              {"python": "1.0_nonexistent"},
                                                              linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual("1.0", linters[0].languages["python"])

        self.assertEqual(response["status_code"], 400)
        self.assertIn("Could not (re)start linter", response["detail"])
        self.assertIn("1.0_nonexistent", response["detail"])

    def test_replacing_linter_with_different_version(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual("1.0", linters[0].languages["python"])

        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "2.0"}, linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual("2.0", linters[0].languages["python"])

    def test_killing_linters(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        id1 = linters[0].instance_id
        id2 = linters[1].instance_id

        machine_manager_api.kill_linter_instance(self.machine_manager_url, id1)

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(id2, linters[0].instance_id)

    def test_load_balancer_with_no_linters(self):
        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="python", code="x = 5"),
                                       self.machine_manager_url))

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available for python language at the moment.", response.errors[0])

    def test_load_balancer_with_no_linters_for_language(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})

        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="java", code="x = 5"),
                                       self.machine_manager_url))

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available for java language at the moment.", response.errors[0])

    def test_load_balancer_equal_split(self):
        for i in range(10):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})

        for i in range(100):
            response: LinterResponse = LinterResponse.from_dict(
                load_balancer_api.validate(self.load_balancer_url,
                                           LinterRequest(language="python", code="x = 5"),
                                           self.machine_manager_url))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 10 + 1}", response.test_logging[0])

    def test_load_balancer_equal_split_across_one_language(self):
        for i in range(5):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"java": "1.0"})

        for i in range(100):
            response: LinterResponse = LinterResponse.from_dict(
                load_balancer_api.validate(self.load_balancer_url,
                                           LinterRequest(language="python", code="x = 5"),
                                           self.machine_manager_url))
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 5 + 1}", response.test_logging[0])

    def test_setting_path_to_linter_binary(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"})

        response: LinterResponse = LinterResponse.from_dict(
            load_balancer_api.validate(self.load_balancer_url,
                                       LinterRequest(language="python", code="x = 5"),
                                       self.machine_manager_url))
        self.assertEqual("Current languages with linter binaries: {'python': './linters/python/bin/linter_1.0'}",
                         response.test_logging[1])
        
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
        version = "2.0"
        steps = [0.1, 0.5, 1]

        for i in range(n):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"}, None)

        for step in steps:
            self.single_manager_update(n, version, step)

        self.single_manager_update(n, version, steps[-1], True)

    def test_update_manager_double_update(self):
        n = 10
        version1 = "2.0"
        version2 = "3.0"
        steps = [0.1, 0.5, 1]

        for i in range(n):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"}, None)

        for step in steps:
            self.single_manager_update(n, version1, step)
            self.single_manager_update(n, version2, step)

        self.single_manager_update(n, version1, steps[-1], True)

    def single_manager_rollback(self, version: str):
        update_manager_api.rollback(self.update_manager_url, self.machine_manager_url, version)
        machines = machine_manager_api.get_linters(self.machine_manager_url)
        how_many_updated = len(list(filter(lambda machine: machine.version > version, machines)))
        update_status = update_manager_api.status(self.update_manager_url, version)

        self.assertEqual(0, how_many_updated)
        self.assertEqual(update_status, 0)

    def test_single_rollback(self):
        n = 10
        version = "2.0"
        steps = [0.1, 0.5, 1]

        for i in range(n):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"}, None)

        self.single_manager_update(n, version, steps[0])
        self.single_manager_rollback("1.0")

    def test_double_rollback(self):
        n = 10
        version1 = "2.0"
        version2 = "3.0"
        steps = [0.1, 0.5, 1]

        for i in range(n):
            machine_manager_api.deploy_linter_instance(self.machine_manager_url, {"python": "1.0"}, None)

        self.single_manager_update(n, version1, steps[0])
        self.single_manager_update(n, version2, steps[0])
        self.single_manager_update(n, version1, steps[1])
        self.single_manager_rollback("1.0")

    #TODO update -> rollback -> update

if __name__ == "__main__":
    unittest.main()
