# MIMUW Linters

## Installation

You can use a simple virtual environment and install dependencies from the `requirements.txt` file.
Example steps:

```shell
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

To run application locally just run script: `run_local.sh`
It starts a `uvicorn` application on a localhost with port 5000.

## Testing

To run *current* tests run the following command from the main directory (from virtual environment):

```shell
python -m unittest e2e_tests.py
```
