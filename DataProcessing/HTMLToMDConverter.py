import os
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from chardet.universaldetector import UniversalDetector

from DataProcessing import OUTPUT_TRANSCRIPT, HTML_OUTPUT_FOLDER
from Utility.Logger import info, warning, error


def detect_encoding(file_path: str) -> str:
    """Detects the encoding of a file using chardet."""
    if not os.path.isfile(file_path):
        error(f"'{file_path}' is not a valid file.")
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


def extract_text_from_html(html_content: str) -> str:
    """Extract plain text from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()


def process_file(file_path: str, encoding: str) -> str:
    """Read a file with given encoding and extract text."""
    with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
        html = f.read()
    return extract_text_from_html(html)


def TextExtractor(input_path: Path, output_file: Path):
    """Extract text from a single file or all HTML files in a folder."""
    output_text = ""

    if input_path.is_dir():
        info(f"Input is a directory. Processing all .html files inside '{input_path}'.")

        html_parts = []
        for fname in sorted(os.listdir(input_path)):
            if fname.endswith('.html'):
                fpath = input_path / fname
                info(f"Reading: {fpath}")
                encoding = detect_encoding(str(fpath))
                text = process_file(str(fpath), encoding)
                html_parts.append(text)

        if not html_parts:
            error("No HTML files found in the directory.")
            sys.exit(1)

        output_text = '\n\n'.join(html_parts)

    elif input_path.is_file():
        info(f"Processing file: {input_path}")
        encoding = detect_encoding(str(input_path))
        output_text = process_file(str(input_path), encoding)

    else:
        error(f"Invalid input: {input_path}")
        sys.exit(1)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write(output_text)

    info(f"Text extracted to: {output_file}")


def ExtractTextFromFolder(input_HTML_dir: Path = HTML_OUTPUT_FOLDER,
                          transcript_dir: Path = OUTPUT_TRANSCRIPT):
    """Extracts text from all subfolders containing HTML files."""
    input_HTML_dir = Path(input_HTML_dir)
    transcript_dir = Path(transcript_dir)
    transcript_dir.mkdir(parents=True, exist_ok=True)

    subdirectories = [d for d in os.listdir(input_HTML_dir) if (input_HTML_dir / d).is_dir()]

    if not subdirectories:
        warning(f"No subdirectories found in '{input_HTML_dir}' to process.")
        return

    for subdir in subdirectories:
        input_path = input_HTML_dir / subdir
        output_file = transcript_dir / f"{subdir}.md"
        info(f"Processing folder: {subdir}")
        TextExtractor(input_path, output_file)
