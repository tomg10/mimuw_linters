import typing

import google.cloud.compute_v1 as compute_v1

project_id, zone = "mimuw-linters", "europe-central2-a"
instance_client = compute_v1.InstancesClient()


instance_list = instance_client.list(project=project_id, zone=zone)
print(instance_list)

