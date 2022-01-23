from test_e2e import E2eTests
import load_balancer_api
import unittest
import os
import deploy_utils


class LoadBalancerTests(E2eTests):
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

    def test_when_no_machine_manager_url(self):
        deploy_utils.stop_fast_api_app(self.load_balancer_process)
        os.environ.pop("LOAD_BALANCER_MACHINE_MANAGER_URL")
        self.load_balancer_process, self.load_balancer_url = deploy_utils.start_fast_api_app("load_balancer")

        with self.assertRaises(Exception) as cm:
            load_balancer_api.validate(self.load_balancer_url,
                                       E2eTests.flawless_python_request)

        self.assertEqual(
            "Error in update_manager: {'detail': \"LOAD_BALANCER_MACHINE_MANAGER_URL doesn't exist in environment\"}",
            str(cm.exception)
        )


if __name__ == "__main__":
    unittest.main()
