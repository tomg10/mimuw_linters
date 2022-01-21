#!/bin/bash

gcloud config set project mimuw-linters
gcloud auth activate-service-account mimuw-linters-auth@mimuw-linters.iam.gserviceaccount.com --key-file=key.json
uvicorn machine_manager:machine_manager_app --host=0.0.0.0 --port="$1"
