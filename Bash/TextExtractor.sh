
file_name="$0"

print_usage() {
    echo "usage:"
    echo "  $file_name input.html output.txt"
    echo "  $file_name input_folder/ output.txt"
}

# Funzione per determinare l'encoding di un file
detect_encoding() {
    local file="$1"

    # Check if the file exists
    if [ ! -f "$file" ]; then
        echo "Error: '$file' is not a valid file."
        return 1
    fi

    local encoding
    encoding=$(uchardet "$file" | tr '[:upper:]' '[:lower:]')

    # Check if encoding is uncertain or unknown
    if [ -z "$encoding" ] || echo "$encoding" | grep -Eq 'unknown|ascii'; then
        echo "utf-8"
    else
        echo "$encoding"
    fi
}

# Funzione per convertire il file a UTF-8 se necessario e applicare lynx
convert_and_extract() {
    local input="$1"
    local encoding="$2"
    local output="$3"

    if [ "$encoding" != "utf-8" ]; then
        echo "Converting file to UTF-8"
        tmp_file="$(mktemp).html"
        iconv -f "$encoding" -t utf-8 "$input" > "$tmp_file"
        lynx -dump -nolist "$tmp_file" > "$output"
        rm "$tmp_file"
    else
        echo "Encoding is UTF-8, processing directly"
        lynx -dump -nolist "$input" > "$output"
    fi
}

# Controllo numero argomenti
if [ "$#" -ne 2 ]; then
    print_usage
    exit 1
fi

input_path="$1"
output_file="$2"

# Se il primo argomento è una cartella
if [ -d "$input_path" ]; then
    echo "Input is a directory. Processing all .html files inside."

    tmp_concat="$(mktemp).html"

    for file in "$input_path"/*.html; do
        echo "Adding: $file"
        cat "$file" >> "$tmp_concat"
        echo "\n" >> "$tmp_concat"
    done


    if [ ! -s "$tmp_concat" ]; then
        echo "No HTML files found or concatenated file is empty."
        exit 1
    fi

    encoding=$(detect_encoding "$tmp_concat")
    echo "Encoding detected for combined file $tmp_concat: $encoding"

    convert_and_extract "$tmp_concat" "$encoding" "$output_file"
    rm "$tmp_concat"

else
    # Singolo file
    encoding=$(detect_encoding "$input_path")
    echo "Encoding detected for $input_path: $encoding"

    convert_and_extract "$input_path" "$encoding" "$output_file"
fi

echo "Text extracted in: $output_file"