#!/bin/bash

# Check if file path was provided
if [ -z "$1" ]; then
    echo "Usage: $0 /path/to/video.mp4 [interval_in_minutes]"
    exit 1
fi

INPUT="$1"
INTERVAL_MINUTES="${2:-30}"  # Default to 30 minutes if not provided
CHUNK_DURATION=$((INTERVAL_MINUTES * 60))  # Convert to seconds

FILENAME=$(basename "$INPUT")
BASENAME="${FILENAME%.*}"
DIRNAME=$(dirname "$INPUT")
OUTPUT_DIR="${DIRNAME}/${BASENAME}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get total duration
DURATION=$(ffprobe -i "$INPUT" -show_entries format=duration -v quiet -of csv="p=0")
START=0
PART=1

# Split loop
while (( $(echo "$START < $DURATION" | bc -l) )); do
    OUTPUT="${OUTPUT_DIR}/${BASENAME}_part${PART}.mp4"
    echo "Creating $OUTPUT (start at $START sec, duration $CHUNK_DURATION sec)..."
    ffmpeg -i "$INPUT" -ss "$START" -t "$CHUNK_DURATION" -c copy "$OUTPUT"
    START=$(echo "$START + $CHUNK_DURATION" | bc)
    ((PART++))
done

echo "Done! Files are in: $OUTPUT_DIR"
