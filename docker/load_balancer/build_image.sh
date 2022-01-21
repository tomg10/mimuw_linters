#!/bin/bash

# Must be run as ./build_image.sh
cd ..
cd ..
docker build -t load_balancer_image -f docker/load_balancer/Dockerfile .