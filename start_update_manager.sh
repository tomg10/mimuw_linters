#!/bin/bash

uvicorn update_manager:update_manager_app --host=0.0.0.0 --port="$1"