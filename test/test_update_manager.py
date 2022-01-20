from test_e2e import E2eTests
import update_manager_api
import machine_manager_api
import deploy_utils
import unittest


class UpdateManagerTests(E2eTests):
    def setUp(self) -> None:
        super(UpdateManagerTests, self).setUp()
        self.update_manager_process, self.update_manager_url = deploy_utils.start_fast_api_app("update_manager")

    def tearDown(self) -> None:
        deploy_utils.stop_fast_api_app(self.update_manager_process)
        super(UpdateManagerTests, self).tearDown()

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


if __name__ == "__main__":
    unittest.main()
