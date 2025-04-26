#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Uso: ./estrai_testo.sh input.html output.txt"
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
    echo "using temp file with UTF-8 encoding"
    tmp_file=$(mktemp)
    iconv -f "$encoding" -t utf-8 "$input_file" > "$tmp_file"
    html2text "$tmp_file" > "$output_file"
    rm "$tmp_file"
else
    echo "converting directly"
    html2text "$input_file" > "$output_file"
fi

echo "Testo estratto salvato in: $output_file"