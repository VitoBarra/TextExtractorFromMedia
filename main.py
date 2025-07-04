from SpiltVideo import *
from TextExtractor import *
from VideoUploader import *

# --- Settings ---
VIDEO_FOLDER = "data"
OUTPUT_FOLDER = "transcript"


HEADLESS_MODE = True


if __name__ == '__main__':
    SplitVideoInFolder(VIDEO_FOLDER, 30)
    jobToDo= True
    while jobToDo:
        jobToDo = not UploadVideos(False, VIDEO_FOLDER, OUTPUT_FOLDER, HEADLESS_MODE)
    ExtractTextFromFolder(OUTPUT_FOLDER)


