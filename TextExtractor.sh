#!/bin/bash

file_name="$0"

if [ "$#" -ne 2 ]; then
    echo "usage: $file_name input.html output.txt"
    exit 1
fi

input_file="$1"
output_file="$2"

# Detect encoding using uchardet
encoding=$(uchardet "$input_file" | tr '[:upper:]' '[:lower:]')

# Normalize or fallback to UTF-8 if uncertain
if [ -z "$encoding" ] || [[ "$encoding" =~ unknown|ascii ]]; then
    echo "Encoding uncertain or unknown, defaulting to UTF-8"
    encoding="utf-8"
fi

echo "Encoding detected for $input_file: $encoding"

# Only convert if it's not already utf-8
if [ "$encoding" != "utf-8" ]; then
    echo "Using temp file with UTF-8 encoding"
    tmp_file=$(mktemp)
    iconv -f "$encoding" -t utf-8 "$input_file" > "$tmp_file"
    lynx -dump -nolist "$tmp_file" > "$output_file"
    rm "$tmp_file"
else
    echo "Converting directly"
    lynx -dump -nolist "$input_file" > "$output_file"
fi

echo "text extracted in : $output_file"
