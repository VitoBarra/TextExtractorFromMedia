from SpiltVideo import *
from TextExtractor import *
from VideoUploader import *

# --- Settings ---
VIDEO_FOLDER = "data"
OUTPUT_FOLDER = "transcript"

if __name__ == '__main__':
    SplitVideoInFolder(VIDEO_FOLDER, 30)
    UploadVideos(False, VIDEO_FOLDER, OUTPUT_FOLDER)
    ExtractTextFromFolder(OUTPUT_FOLDER)


