#!/bin/bash

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <problem_path> <path_to_subset.txt>"
    exit 1
fi

# Assign arguments to variables
PROBLEM_PATH=$1
SUBSET_PATH=$2

# Ensure PROBLEM_PATH and SUBSET_PATH are valid
if [ ! -d "$PROBLEM_PATH" ]; then
    echo "Error: Directory $PROBLEM_PATH does not exist."
    exit 1
fi

if [ ! -f "$SUBSET_PATH" ]; then
    echo "Error: File $SUBSET_PATH does not exist."
    exit 1
fi

# Get the parent directory and base directory name of the problem path
PARENT_DIR=$(dirname "$PROBLEM_PATH")
BASE_NAME=$(basename "$PROBLEM_PATH")

# Create a new directory with the same base name but "_filtered" appended
FILTERED_DIR="$PARENT_DIR/${BASE_NAME}_filtered"
mkdir -p "$FILTERED_DIR"

# Copy files listed in subset.txt from the problem path to the new directory
while IFS= read -r line; do
    # Use sed to trim leading and trailing whitespace
    file=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

    # Check if the file exists before copying
    if [ -f "$PROBLEM_PATH/$file" ]; then
        cp "$PROBLEM_PATH/$file" "$FILTERED_DIR/"
    else
        echo "Warning: File $PROBLEM_PATH/$file does not exist."
    fi
done < "$SUBSET_PATH"

echo "Done copying files to $FILTERED_DIR."
