import requests


def set_is_killed(url):
    requests.post(url + '/set-is-killed', timeout=1)


def set_linter_url(url, linter_url):
    requests.post(url + f'/set-linter-url?linter_url={linter_url}', timeout=1)
