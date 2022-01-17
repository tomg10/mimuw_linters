from test_e2e import E2eTests
import load_balancer_api
import unittest
from schema import LinterRequest


class LoadBalancerTests(E2eTests):
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


if __name__ == "__main__":
    unittest.main()
