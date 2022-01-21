#!/bin/bash

export LOAD_BALANCER_MACHINE_MANAGER_URL="$2"
uvicorn load_balancer:load_balancer_app --host=0.0.0.0 --port="$1"