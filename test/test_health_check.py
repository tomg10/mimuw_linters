from test_e2e import E2eTests
import os
import unittest
import time
import health_check_api
import killable_linter_proxy_api
import load_balancer_api
import machine_manager_api
import deploy_utils


class HealthCheckTests(E2eTests):
    health_check_timeout = 0.5
    health_check_repetition_period = 1.2

    def tearDown(self) -> None:
        self.stop_health_check()
        super(HealthCheckTests, self).tearDown()

    # Don't call it in setUp, as it should be started after we change backed of machine manager to killable proxy.
    # Otherwise we would get a connection reset by peer error.
    def start_health_check(self):
        os.environ["HEALTH_CHECK_TIMEOUT"] = str(HealthCheckTests.health_check_timeout)
        os.environ["HEALTH_CHECK_REPETITION_PERIOD"] = str(HealthCheckTests.health_check_repetition_period)
        self.hc_process, self.hc_url = deploy_utils.start_fast_api_app("health_check")
        time.sleep(2)

    def stop_health_check(self):
        deploy_utils.stop_fast_api_app(self.hc_process)
        os.environ.pop("HEALTH_CHECK_TIMEOUT")
        os.environ.pop("HEALTH_CHECK_REPETITION_PERIOD")

    def wait_for_hearthbeat(self):
        # It is not ideal, but it works. We want 2 times timeout because we have 2 machines in tests and one repetition
        # period to ensure hearthbeat will be called at least once.
        time.sleep(HealthCheckTests.health_check_timeout * 2 + HealthCheckTests.health_check_repetition_period)

    def test_health_check_when_linters_work(self):
        self.create_linter_instances(2, E2eTests.v1)
        self.start_health_check()

        self.wait_for_hearthbeat()
        self.assertEqual(0, health_check_api.get_failures(self.hc_url))

    def test_health_check_when_one_linter_doesnt_work(self):
        self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
        linter_instance1 = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                                      linter_version=E2eTests.v_real)
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version=E2eTests.v_real)
        killable_linter_proxy_api.set_is_killed(linter_instance1.address)

        self.start_health_check()

        self.wait_for_hearthbeat()
        self.assertEqual(1, health_check_api.get_failures(self.hc_url))

    def test_health_check_restarts_linter_when_dead(self):
        self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
        linter_instance1 = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                                      linter_version=E2eTests.v_real)
        killable_linter_proxy_api.set_is_killed(linter_instance1.address)

        self.start_health_check()

        self.wait_for_hearthbeat()
        for i in range(2):
            response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)

        self.assertEqual(1, health_check_api.get_failures(self.hc_url))

        [linter_instance1] = machine_manager_api.get_linters(self.machine_manager_url)
        killable_linter_proxy_api.set_is_killed(linter_instance1.address)

        self.wait_for_hearthbeat()
        for i in range(2):
            response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)

        self.assertEqual(2, health_check_api.get_failures(self.hc_url))


if __name__ == "__main__":
    unittest.main()
