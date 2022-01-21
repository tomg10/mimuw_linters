import requests


def update(url, machine_manager_url, version):
    full_url = f"{url}/update?machine_manager_url={machine_manager_url}&version={version}"
    response = requests.post(full_url)

    if response.status_code != 200:
        raise Exception(f"Error in update_manager: {response.json()}")

    return response.json()


def rollback(url, machine_manager_url, version):
    full_url = f"{url}/rollback?machine_manager_url={machine_manager_url}&version={version}"
    return requests.post(full_url).json()


def status(url, version):
    full_url = f"{url}/status?version={version}"
    return requests.get(full_url).json()
