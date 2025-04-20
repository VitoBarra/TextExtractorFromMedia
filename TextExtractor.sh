#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Uso: ./estrai_testo.sh input.html output.txt"
    exit 1
fi

input_file="$1"
output_file="$2"

html2text "$input_file" > "$output_file"

echo "Testo estratto salvato in: $output_file"
