import time

import requests


def is_healthy(url):
    try:
        result = requests.get(url + "/").json()
        return result.split()[0] == "ok"
    except:
        return False


def wait_for_healthy_state(url):
    for i in range(50):
        if is_healthy(url):
            return
        time.sleep(0.1)
    raise Exception(f"App on {url} is not healthy!")