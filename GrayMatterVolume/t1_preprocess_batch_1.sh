#!/bin/bash

# Maximum number of threads (can be adjusted as needed)
MAX_THREADS=40
# Get the absolute path of the directory where the current script is located
SCRIPT_DIR=$(dirname "$(realpath "$0")")
# Input directory (the directory where all subject data is stored)
INPUT_DIR="/media/shulab/Getea/zhe2/NC/sorted"
# Output directory (the path to save the results)
OUTPUT_DIR="/media/shulab/Getea/zhe2/NC/results"
# Path to the atlas file (modify according to the actual situation)
ATLAS="$SCRIPT_DIR/atlas/desikan-killiany_1mm.nii.gz"

# Create the output directory
mkdir -p "$OUTPUT_DIR"

# Initialize the thread counter
THREAD_COUNT=0

# Iterate through all subject folders (excluding the current directory itself)
find "$INPUT_DIR" -mindepth 1 -maxdepth 1 -type d -name '*' | while read -r subject_folder; do
    subject_id=$(basename "$subject_folder")
    echo "Processing subject: $subject_id"

    # Generate the full command line
    cmd="$SCRIPT_DIR/t1_preprocess.sh '$subject_folder' '$OUTPUT_DIR/$subject_id' '$ATLAS'"
    echo "Executing command: $cmd"

    # Call the preprocessing script
    eval "$cmd" &

    ((THREAD_COUNT++))

    # Control the number of concurrent threads
    if [ "$THREAD_COUNT" -ge "$MAX_THREADS" ]; then
        wait -n
        ((THREAD_COUNT--))
    fi
done

# Wait for all tasks to complete
wait

echo "All subjects processed."    