import os
from pathlib import Path

from DataProcessing import RAW_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT, RAW_AUDIO_FOLDER, \
    OUTPUT_PROCESSED_AUDIO, AUDIO_EXTENSIONS
from DataProcessing.AudioCleaner import enhance_audio_in_chunks
from DataProcessing.AudioToText import transcribe_audio
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
    audioProjects = [Path(dir).name for dir in os.listdir(OUTPUT_PROCESSED_AUDIO) if os.path.isdir(OUTPUT_PROCESSED_AUDIO / dir)]
    files_NotEnhanced = [f for f in files if f.stem not in audioProjects]

    for f in files_NotEnhanced:
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

    for f in files:
        transcribe_audio(OUTPUT_PROCESSED_AUDIO/f.stem/f"{f.stem}.wav", model_size="medium",
                         save_to=OUTPUT_TRANSCRIPT/f.stem/"transcript.md")

if __name__ == '__main__':
        # ProcessVideo()
        ProcessAudio()


