#!/bin/bash

# Must be run as ./build_image.sh
cd ..
cd ..
docker build -t update_manager_image -f docker/update_manager/Dockerfile .