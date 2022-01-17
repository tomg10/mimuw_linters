import requests


def get_failures(url) -> int:
    response = requests.get(f"{url}/get_failures").json()
    return response
