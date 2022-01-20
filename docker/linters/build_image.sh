#!/bin/bash

# Must be run as ./build_image.sh {version}
cd ..
cd ..
docker build -t linter_image_"$1" -f docker/linters/Dockerfile .