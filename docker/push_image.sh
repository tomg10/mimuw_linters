#!/bin/bash

# ./push_image {image_name}

docker tag "$1" eu.gcr.io/mimuw-linters/"$1"
docker push eu.gcr.io/mimuw-linters/"$1"
