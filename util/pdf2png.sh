#!/usr/bin/env bash
set -x

# Check if an argument was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_pdf>"
    exit 1
fi

PDF_FILE=$1
# Extract the filename without the extension
BASENAME=$(basename "$PDF_FILE" .pdf)

# Directory for temporary PNG files
TMP_DIR=$(mktemp -d)
echo "Temporary directory created at $TMP_DIR"

# Convert each page of the PDF to PNG at 250 DPI
pdftoppm -png -r 200 "$PDF_FILE" "$TMP_DIR/$BASENAME"

# Concatenate all pages vertically
convert "$TMP_DIR"/*.png -append "$BASENAME.png"

echo "Output saved to $BASENAME.png"

# Cleanup temporary files
rm -rf "$TMP_DIR"
echo "Temporary files cleaned up."
