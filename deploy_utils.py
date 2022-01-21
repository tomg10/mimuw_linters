import random
import subprocess
import signal
import socket
import health_utils


# https://stackoverflow.com/a/52872579
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_fast_api_app(app_name, base_package="", port: int = None):
    if port is None:
        port = random.randint(10000, 20000)
    while is_port_in_use(port):
        port = random.randint(10000, 20000)

    address = f"http://localhost:{port}"
    process = subprocess.Popen(["uvicorn", f"{base_package}{app_name}:{app_name}_app", f"--port={port}"])
    health_utils.wait_for_healthy_state(address)
    return process, address


def stop_fast_api_app(process):
    process.send_signal(signal.SIGINT)
