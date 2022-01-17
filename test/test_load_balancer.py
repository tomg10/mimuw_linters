from .test_e2e import E2eTests
import load_balancer_api
import unittest


class LoadBalancerTests(E2eTests):
    def test_load_balancer_with_no_linters(self):
        response = load_balancer_api.validate(self.load_balancer_url,
                                              E2eTests.flawless_python_request)

        self.assertEqual("fail", response.result)
        self.assertEqual(1, len(response.errors))
        self.assertEqual("No linter instance available", response.errors[0])

    def test_load_balancer_equal_split(self):
        self.create_linter_instances(10, E2eTests.v1)

        for i in range(100):
            response = load_balancer_api.validate(self.load_balancer_url,
                                                  E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))
            self.assertEqual(f"Current responses_count: {i // 10 + 1}", response.test_logging[0])


if __name__ == "__main__":
    unittest.main()
