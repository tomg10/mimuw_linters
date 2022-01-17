from .test_e2e import E2eTests
import machine_manager_api
import load_balancer_api
import unittest


class LinterTests(E2eTests):
    def test_getting_linters(self):
        self.create_linter_instances(3, E2eTests.v1)
        result = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(3, len(result))

    def test_running_linter_binary_on_flawed_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, E2eTests.v1)

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawed_python_request)
        self.assertEqual("fail", response.result)
        self.assertEqual(4, len(response.errors))

    def test_running_linter_binary_on_flawless_input(self):
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, E2eTests.v1)

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))


if __name__ == "__main__":
    unittest.main()
