from test_e2e import E2eTests
import machine_manager_api
import load_balancer_api
import killable_linter_proxy_api
import unittest


class FaultInjectionTests(E2eTests):
    def test_killing_linters(self):
        self.create_linter_instances(2, E2eTests.v_real)

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        id1 = linters[0].instance_id
        id2 = linters[1].instance_id

        machine_manager_api.kill_linter_instance(self.machine_manager_url, id1)

        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(id2, linters[0].instance_id)

    def test_killable_proxy_can_be_killed(self):
        self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
        linter_instance = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                                     linter_version=E2eTests.v_real)
        response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)

        killable_linter_proxy_api.set_is_killed(linter_instance.address)
        response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
        self.assertEqual("fail", response.result)
        self.assertEqual(["No linter instance was able to handle request"], response.errors)

    def test_two_killed_linters_do_not_cause_outages(self):
        self.restart_machine_manager_with_different_params(deploy_backend_name='killable_proxy')
        linter_instance1 = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                                      linter_version=E2eTests.v_real)
        linter_instance2 = machine_manager_api.deploy_linter_instance(self.machine_manager_url,
                                                                      linter_version=E2eTests.v_real)
        machine_manager_api.deploy_linter_instance(self.machine_manager_url, linter_version=E2eTests.v_real)

        response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
        self.assertEqual("ok", response.result)

        killable_linter_proxy_api.set_is_killed(linter_instance1.address)
        killable_linter_proxy_api.set_is_killed(linter_instance2.address)
        for i in range(10):
            response = load_balancer_api.validate(self.load_balancer_url, request=E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)


if __name__ == "__main__":
    unittest.main()
