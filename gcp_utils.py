import subprocess
import logging
from logging.config import dictConfig

import health_utils
from gcp import config as gcp_config
from google.cloud import compute_v1

from configs.machine_manager.logging_config import log_config

dictConfig(log_config)
logger = logging.getLogger("gcp_linter_deployer_logger")


def create_machine(machine_name):
    completed_process = subprocess.run(f"gcloud compute instances create {machine_name}"
                                       f" --project={gcp_config.project_id}"
                                       f" --zone={gcp_config.zone}"
                                       f" --machine-type=f1-micro"
                                       f" --network-interface=network-tier=PREMIUM,subnet=default"
                                       f" --maintenance-policy=MIGRATE"
                                       f" --service-account=mimuw-linters-auth@mimuw-linters.iam.gserviceaccount.com"
                                       f" --scopes=https://www.googleapis.com/auth/cloud-platform"
                                       f" --tags=http-server"
                                       f" --create-disk=auto-delete=yes,boot=yes,device-name={machine_name},"
                                       f"image=projects/mimuw-linters/global/images/machine-image-for-all,mode=rw,"
                                       f"size=10,"
                                       "type=projects/mimuw-linters/zones/europe-central2-a/diskTypes/pd-standard"
                                       " --no-shielded-secure-boot"
                                       " --shielded-vtpm"
                                       " --shielded-integrity-monitoring"
                                       " --reservation-affinity=any",
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

    logger.info(f"Finished creating machine with name {machine_name}."
                f"\nStdout: {completed_process.stdout}\nStderr: {completed_process.stderr}")

    client = compute_v1.InstancesClient()
    for _ in range(30):
        try:
            instance = client.get(project=gcp_config.project_id, zone=gcp_config.zone, instance=machine_name, timeout=4)
            return instance.network_interfaces[0].network_i_p
        except:
            logger.exception(f"Exception during querying new machine {machine_name} for ip address.")
            pass

    raise Exception(f"New machine {machine_name} is not responding!")


def delete_machine(machine_name):
    # Taken from: https://cloud.google.com/compute/docs/instances/deleting-instance#python
    instances_client = compute_v1.InstancesClient()
    operation_client = compute_v1.ZoneOperationsClient()
    operation = instances_client.delete_unary(
        project=gcp_config.project_id, zone=gcp_config.zone, instance=machine_name
    )

    waiting_count = gcp_config.killing_machine_waiting_count
    while operation.status != compute_v1.Operation.Status.DONE:
        operation = operation_client.wait(
            operation=operation.name, zone=gcp_config.zone, project=gcp_config.project_id
        )

        waiting_count -= 1
        if waiting_count == 0:
            break

    if operation.error:
        logger.error(f"Error during deletion: {operation.error}")
    if operation.warnings:
        logger.warning(f"Warning during deletion: {operation.warnings}")
    logger.info(f"Instance {machine_name} deleted.")


def run_remote_command(machine_name, command):
    completed_process = None
    for _ in range(gcp_config.ssh_retries_count):
        completed_process = subprocess.run(f"gcloud compute ssh --zone {gcp_config.zone} "
                                           f"{gcp_config.gcp_user}@{machine_name} --command '{command}'",
                                           shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
        if "Connection refused" not in completed_process.stderr.decode("utf-8"):
            break

    return completed_process.stdout, completed_process.stderr


def start_linter(machine_ip, machine_name, linter_version, port):
    linter_image = f"{gcp_config.images_repo}/{gcp_config.linter_image_prefix}_{linter_version}"

    stdout, stderr = run_remote_command(machine_name, f"docker pull {linter_image}")
    logger.info(f"Linter image for version {linter_version} pulled to machine {machine_name}."
                f"\nStdout: {stdout}"
                f"\nStderr: {stderr}")

    stdout, stderr = run_remote_command(machine_name,
                                        f"docker run -dp {port}:{port} --stop-signal SIGINT {linter_image} {port}")
    logger.info(f"Linter start initiated for version {linter_version} on machine {machine_name}."
                f"\nStdout: {stdout}"
                f"\nStderr: {stderr}")

    container_id = stdout.decode("utf-8").strip()
    health_utils.wait_for_healthy_state(f"http://{machine_ip}:{port}", 1)

    return container_id


def kill_linter(machine_name, container_id):
    stdout, stderr = run_remote_command(machine_name, f"docker stop {container_id}")
    logger.info(f"Linter kill command issued for container id {container_id} on machine {machine_name}."
                f"\nStdout: {stdout}"
                f"\nStderr: {stderr}")

    stdout, stderr = run_remote_command(machine_name, f"docker container prune --force")
    logger.info(f"Pruning stopped containers on machine {machine_name}."
                f"\nStdout: {stdout}"
                f"\nStderr: {stderr}")
