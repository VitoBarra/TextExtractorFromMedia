import os
from pathlib import Path

from DataProcessing import RAW_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT, RAW_AUDIO_FOLDER, \
    OUTPUT_PROCESSED_AUDIO, AUDIO_EXTENSIONS
from DataProcessing.AudioCleaner import enhance_audio_in_chunks
from DataProcessing.SplitVideo import SplitVideoInFolder
from DataProcessing.TextExtractor import ExtractTextFromFolder
from WebScraper.VideoUploader import UploadVideos

# --- Settings ---

HEADLESS_MODE = True

def ProcessVideo():
    SplitVideoInFolder(RAW_VIDEO_FOLDER, 30)
    jobToDo = True
    while jobToDo:
        jobToDo = not UploadVideos(False, RAW_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, HEADLESS_MODE)
    ExtractTextFromFolder(HTML_OUTPUT_FOLDER,OUTPUT_TRANSCRIPT)

def ProcessAudio():
    files = [Path(f) for f in os.listdir(RAW_AUDIO_FOLDER) if os.path.isfile(RAW_AUDIO_FOLDER/ f)]

    for f in files:
        enhance_audio_in_chunks(
            input_file=RAW_AUDIO_FOLDER/ f.name,
            output_file=OUTPUT_PROCESSED_AUDIO/f.stem/f"{f.stem}.wav",
            raw_chunk_dir=OUTPUT_PROCESSED_AUDIO/f.stem/"RawAudioChunk",
            enhanced_chunk_dir=OUTPUT_PROCESSED_AUDIO/f.stem/"enhancedAudioChunk",
            chunk_duration=20,
            lowcut=100,
            highcut=6000,
            compress_threshold_db=-30,
            compress_ratio=4,
            gain_db=8,
        )

if __name__ == '__main__':
        # ProcessVideo()
        ProcessAudio()


