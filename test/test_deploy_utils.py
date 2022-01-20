from test_e2e import E2eTests
import deploy_utils
import unittest


class DeployUtilsTests(E2eTests):
    @staticmethod
    def test_opening_application_on_already_occupied_socket():
        machine_manager_process, _ = deploy_utils.start_fast_api_app("machine_manager", port=5000)
        load_balancer_process, _ = deploy_utils.start_fast_api_app("load_balancer", port=5000)

        deploy_utils.stop_fast_api_app(machine_manager_process)
        deploy_utils.stop_fast_api_app(load_balancer_process)


if __name__ == "__main__":
    unittest.main()
