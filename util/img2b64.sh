#!/usr/bin/env bash

# Check if an argument was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_image>"
    exit 1
fi

IMAGE_PATH="$1"
IMAGE_TYPE=""

# Temporarily enable case-insensitive pattern matching for extension check
shopt -s nocasematch
if [[ $IMAGE_PATH =~ \.jpe?g$ ]]; then
    IMAGE_TYPE="jpeg"
elif [[ $IMAGE_PATH =~ \.png$ ]]; then
    IMAGE_TYPE="png"
else
    echo "Unsupported file type. Please use a PNG or JPEG image."
    shopt -u nocasematch
    exit 1
fi
# Revert to case-sensitive pattern matching after the check
shopt -u nocasematch

# Encode the image to base64 and prepend the data URI prefix
echo -n "data:image/${IMAGE_TYPE};base64,"
base64 "$IMAGE_PATH"
