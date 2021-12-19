import os

def get_env_or_raise(var_name):
    value = os.environ.get(var_name)
    if not value:
        raise Exception(f"please set {var_name} env variable")
    else:
        return value

def get_machine_manager_url():
    return get_env_or_raise("MACHINE_MANAGER_URL")