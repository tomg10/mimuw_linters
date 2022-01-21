import time
import requests


def is_healthy(url):
    try:
        result = requests.get(url + "/", timeout=0.1).json()
        return result == "ok"
    except:
        return False


def wait_for_healthy_state(url, sleep=0.1):
    for i in range(50):
        if is_healthy(url):
            return
        time.sleep(sleep)
    raise Exception(f"App on {url} is not healthy!")