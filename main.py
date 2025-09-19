from DataProcessing import RAW_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT
from DataProcessing.SplitVideo import SplitVideoInFolder
from DataProcessing.TextExtractor import ExtractTextFromFolder
from WebScraper.VideoUploader import UploadVideos

# --- Settings ---

HEADLESS_MODE = True

if __name__ == '__main__':
    SplitVideoInFolder(RAW_VIDEO_FOLDER, 30)
    jobToDo = True
    while jobToDo:
        jobToDo = not UploadVideos(False, RAW_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, HEADLESS_MODE)
    ExtractTextFromFolder(HTML_OUTPUT_FOLDER,OUTPUT_TRANSCRIPT)


