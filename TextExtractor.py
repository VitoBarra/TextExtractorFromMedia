import os
import sys
from chardet.universaldetector import UniversalDetector
from bs4 import BeautifulSoup


def detect_encoding(file_path):
    if not os.path.isfile(file_path):
        print(f"Error: '{file_path}' is not a valid file.")
        return None

    detector = UniversalDetector()
    with open(file_path, 'rb') as f:
        for line in f:
            detector.feed(line)
            if detector.done:
                break
    detector.close()

    encoding = detector.result['encoding']
    if not encoding or encoding.lower() in ('ascii', 'unknown'):
        return 'utf-8'
    return encoding.lower()

def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def process_file(file_path, encoding):
    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        html = f.read()
    return extract_text_from_html(html)

def TextExtractor(input_path, output_file):

    output_text = ""

    if os.path.isdir(input_path):
        print("Input is a directory. Processing all .html files inside.")

        html_parts = []
        for fname in sorted(os.listdir(input_path)):
            if fname.endswith('.html'):
                fpath = os.path.join(input_path, fname)
                print(f"Reading: {fpath}")
                encoding = detect_encoding(fpath)
                text = process_file(fpath, encoding)
                html_parts.append(text)

        if not html_parts:
            print("No HTML files found in the directory.")
            sys.exit(1)

        output_text = '\n\n'.join(html_parts)

    elif os.path.isfile(input_path):
        print(f"Processing file: {input_path}")
        encoding = detect_encoding(input_path)
        output_text = process_file(input_path, encoding)

    else:
        print(f"Invalid input: {input_path}")
        sys.exit(1)

    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(output_text)

    print(f"Text extracted in: {output_file}")

if __name__ == '__main__':
    TextExtractor(os.path.join("transcript","11-Ramsac"), "output.txt")
