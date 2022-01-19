#!/bin/bash

cd ..
cd ..
docker build -t linter_image_"$1" -f docker/linters/Dockerfile .