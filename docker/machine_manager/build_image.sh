#!/bin/bash

# Must be run as ./build_image.sh
cd ..
cd ..
docker build -t machine_manager_image -f docker/machine_manager/Dockerfile .