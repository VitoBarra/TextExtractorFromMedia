from pathlib import Path

DATA_PROC_BASE_DIR = Path(__file__).parent
OUTPUT_TRANSCRIPT = DATA_PROC_BASE_DIR / "Transcript"
HTML_OUTPUT_FOLDER = DATA_PROC_BASE_DIR / "HTML"

RAW_VIDEO_FOLDER = DATA_PROC_BASE_DIR / "VIDEO_1RawData"
SPLITTED_VIDEO_FOLDER = DATA_PROC_BASE_DIR / "VIDEO_2Splitted"


folders = [OUTPUT_TRANSCRIPT, HTML_OUTPUT_FOLDER   ,
           RAW_VIDEO_FOLDER , SPLITTED_VIDEO_FOLDER]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)

VIDEO_EXTENSIONS = (".mp4", ".mov", ".3gp", ".avi", ".mkv")


