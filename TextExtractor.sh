#!/bin/bash

file_name="$0"

if [ "$#" -ne 2 ]; then
    echo "usage: $file_name input.html output.txt"
    exit 1
fi

input_file="$1"
output_file="$2"


# Detect the encoding
encoding=$(file -bi "$input_file" | sed -n 's/.*charset=\(.*\)/\1/p')

# Normalize encoding name to lowercase
encoding=$(echo "$encoding" | tr '[:upper:]' '[:lower:]')

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
