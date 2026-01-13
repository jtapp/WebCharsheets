#!/usr/bin/env bash

# Check if an input file was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

INPUT_FILE="$1"

# Use jq to transform the input JSON to the desired JSON schema format
jq '[.shapes[] | {
    input_rect: [.points[] | map(floor)],
    input_name: .label,
    input_type: "text"
}]' "$INPUT_FILE"