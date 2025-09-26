from DataProcessing import RAW_VIDEO_FOLDER, RAW_AUDIO_FOLDER, \
    SPLITTED_AUDIO_FOLDER, SPLITTED_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT, ENHANCED_AUDIO_FOLDER
from DataProcessing.AudioEnhancer import EnhanceAudioFolder
from DataProcessing.AudioExtractor import AudioFormat
from DataProcessing.AudioToText import TranscribeAudioFolder
from DataProcessing.HTMLToMDConverter import ExtractTextFromFolder
from DataProcessing.MediaSplitter import SplitMediaInFolder
from WebScraper.VzardAIUploader import UploadVideoFolder

# --- Settings ---

HEADLESS_MODE = True

def ProcessVideo():
    # AudioFolderToVideo(RAW_AUDIO_FOLDER, RAW_VIDEO_FOLDER, VideoFormat.MP4, overwrite=False)
    SplitMediaInFolder(RAW_VIDEO_FOLDER, SPLITTED_VIDEO_FOLDER, 60 * 30)
    jobToDo = True
    while jobToDo:
        jobToDo = not UploadVideoFolder( RAW_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, HEADLESS_MODE)
    ExtractTextFromFolder(HTML_OUTPUT_FOLDER,OUTPUT_TRANSCRIPT)

def ProcessAudio():
    # VideoFolderToAudio(RAW_VIDEO_FOLDER, RAW_AUDIO_FOLDER, AudioFormat.WAV, overwrite=False)
    SplitMediaInFolder(RAW_AUDIO_FOLDER, SPLITTED_AUDIO_FOLDER, 60 * 15)
    EnhanceAudioFolder(SPLITTED_AUDIO_FOLDER, ENHANCED_AUDIO_FOLDER, AudioFormat.WAV,
        lowcut=100,
        highcut=6000,
        compress_threshold_db=-30,
        compress_ratio=4,
        gain_db=8,
    )
    TranscribeAudioFolder(ENHANCED_AUDIO_FOLDER, OUTPUT_TRANSCRIPT)

if __name__ == '__main__':
        ProcessVideo()
        ProcessAudio()



