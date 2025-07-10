#!/bin/bash

BRANCH=$(git rev-parse --abbrev-ref HEAD | sed 's/[^a-zA-Z0-9]/-/g')

COMMIT=$(git rev-parse --short HEAD)

IMAGE_NAME="bom_checker_app"
TAG="${BRANCH}-${COMMIT}"

docker build -t $IMAGE_NAME:$TAG .

echo "Built image with tag: $IMAGE_NAME:$TAG"