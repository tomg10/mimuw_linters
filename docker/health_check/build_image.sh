#!/bin/bash

# Must be run as ./build_image.sh
cd ..
cd ..
docker build -t health_check_image -f docker/health_check/Dockerfile .