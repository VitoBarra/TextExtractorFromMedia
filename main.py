from DataProcessing import RAW_VIDEO_FOLDER, RAW_AUDIO_FOLDER, \
    SPLITTED_AUDIO_FOLDER, HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT, ENHANCED_AUDIO_FOLDER
from DataProcessing.AudioEnhancer import EnhanceAudioFolder
from DataProcessing.AudioExtractor import AudioFormat, VideoFolderToAudio
from DataProcessing.HTMLToMDConverter import ExtractTextFromFolder
from DataProcessing.MediaSplitter import SplitMediaInFolder
from Utility.Logger import setup_logger
from WebScraper.VzardAIUploader import UploadVideoFolder

# --- Settings ---

HEADLESS_MODE = True

if __name__ == '__main__':
    setup_logger()
    VideoFolderToAudio(RAW_VIDEO_FOLDER, RAW_AUDIO_FOLDER, AudioFormat.WAV, overwrite=False)
    SplitMediaInFolder(RAW_AUDIO_FOLDER, SPLITTED_AUDIO_FOLDER, 60 * 15)
    EnhanceAudioFolder(SPLITTED_AUDIO_FOLDER, ENHANCED_AUDIO_FOLDER, AudioFormat.WAV,
        lowcut=100,
        highcut=6000,
        compress_threshold_db=-30,
        compress_ratio=4,
        gain_db=8,
    )
    jobToDo = True
    while jobToDo:
        jobToDo = not UploadVideoFolder( SPLITTED_AUDIO_FOLDER, HTML_OUTPUT_FOLDER, HEADLESS_MODE)
    ExtractTextFromFolder(HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT)



