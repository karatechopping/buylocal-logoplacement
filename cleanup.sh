#!/bin/bash
# Cleanup script for output images

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <image_path1> [image_path2] ..."
    echo "   or: $0 all  # to delete all output images"
    exit 1
fi

if [ "$1" == "all" ]; then
    echo "Deleting all output images..."
    rm -f outputs/output_*.png
    echo "All output images deleted."
else
    for file in "$@"; do
        if [ -f "$file" ]; then
            rm "$file"
            echo "Deleted: $file"
        else
            echo "File not found: $file"
        fi
    done
fi