from test_e2e import E2eTests
import machine_manager_api
import load_balancer_api
import unittest
from schema import LinterRequest


class LinterTests(E2eTests):
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

    def test_running_two_supported_languages_on_one_linter(self):
        self.create_linter_instances(1, E2eTests.v_real)

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

        response = load_balancer_api.validate(self.load_balancer_url, E2eTests.flawless_java_request)
        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))

    def test_linter_on_unknown_language(self):
        self.create_linter_instances(1, E2eTests.v_real)
        request = LinterRequest(language="Ruby", code=E2eTests.flawless_python_request.code)
        response = load_balancer_api.validate(self.load_balancer_url, request)

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available for language Ruby.", response.errors[0])

    def test_special_characters_in_request(self):
        self.create_linter_instances(1, E2eTests.v_real)
        request = LinterRequest(language="python", code="e<!@#$%%^&*(>'\" = 5")
        response = load_balancer_api.validate(self.load_balancer_url, request)

        self.assertEqual("ok", response.result)
        self.assertEqual(0, len(response.errors))


if __name__ == "__main__":
    unittest.main()
