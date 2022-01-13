import random
import subprocess
import signal

import health_utils


def start_fast_api_app(app_name):
    port = random.randint(10000, 20000)
    address = f"http://localhost:{port}"
    process = subprocess.Popen(["uvicorn", f"{app_name}:{app_name}_app", f"--port={port}"])
    health_utils.wait_for_healthy_state(address)
    return process, address


def stop_fast_api_app(process):
    process.send_signal(signal.SIGINT)
