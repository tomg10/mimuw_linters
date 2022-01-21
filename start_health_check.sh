#!/bin/bash

export HEALTH_CHECK_MACHINE_MANAGER_URL="$2"
uvicorn health_check:health_check_app --host=0.0.0.0 --port="$1"