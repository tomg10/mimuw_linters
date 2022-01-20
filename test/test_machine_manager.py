from test_e2e import E2eTests
import machine_manager_api
import load_balancer_api
import killable_linter_proxy_api
import linter_api
import unittest


class MachineManagerTests(E2eTests):
    def test_spawning_linters(self):
        self.create_linter_instances(3, E2eTests.v_real)
        result = machine_manager_api.get_linters(self.machine_manager_url)

        for linter_instance in result:
            response = linter_api.validate(linter_instance.address, E2eTests.flawless_python_request)
            self.assertEqual("ok", response.result)
            self.assertEqual(0, len(response.errors))

    def test_replacing_linter_with_different_version(self):
        self.create_linter_instances(1, E2eTests.v1)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(E2eTests.v1, linters[0].version)

        self.create_linter_instances(1, E2eTests.v2, linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(E2eTests.v2, linters[0].version)

    def test_replacing_linter_with_nonexistent_version(self):
        self.create_linter_instances(1, E2eTests.v1)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(E2eTests.v1, linters[0].version)

        with self.assertRaises(Exception):
            self.create_linter_instances(1, E2eTests.nonexistent_v, linters[0].instance_id)
        linters = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(1, len(linters))
        self.assertEqual(E2eTests.v1, linters[0].version)

    def test_getting_linters_for_all_languages(self):
        self.create_linter_instances(2, E2eTests.v1)
        self.create_linter_instances(1, E2eTests.v2)
        result = machine_manager_api.get_linters(self.machine_manager_url)
        self.assertEqual(3, len(result))

    def test_getting_linters_for_one_language(self):
        self.create_linter_instances(2, E2eTests.v1)
        self.create_linter_instances(1, E2eTests.v2)
        self.create_linter_instances(1, E2eTests.v3)

        result = machine_manager_api.get_linters(self.machine_manager_url, "python")
        self.assertEqual(3, len(result))
        result = machine_manager_api.get_linters(self.machine_manager_url, "java")
        self.assertEqual(2, len(result))


if __name__ == "__main__":
    unittest.main()
