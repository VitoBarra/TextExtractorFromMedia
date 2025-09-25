import os
from pathlib import Path

from DataProcessing import RAW_VIDEO_FOLDER, RAW_AUDIO_FOLDER, \
    SPLITTED_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT, ENHANCED_AUDIO_FOLDER
from DataProcessing.AudioEnhancer import enhance_audio_in_chunks
from DataProcessing.AudioToText import transcribe_audio
from DataProcessing.HTMLToMDConverter import ExtractTextFromFolder
from DataProcessing.MediaSplitter import SplitVideoInFolder
from WebScraper.VzardAIUploader import UploadVideoFolder



# --- Settings ---

HEADLESS_MODE = True

def ProcessVideo():
    SplitVideoInFolder(RAW_VIDEO_FOLDER,SPLITTED_VIDEO_FOLDER, 30)
    jobToDo = True
    while jobToDo:
        jobToDo = not UploadVideoFolder( RAW_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, HEADLESS_MODE)
    ExtractTextFromFolder(HTML_OUTPUT_FOLDER,OUTPUT_TRANSCRIPT)

def ProcessAudio():
    files = [Path(f) for f in os.listdir(RAW_AUDIO_FOLDER) if os.path.isfile(RAW_AUDIO_FOLDER/ f)]
    audioProjects = [Path(dir).name for dir in os.listdir(ENHANCED_AUDIO_FOLDER) if os.path.isdir(ENHANCED_AUDIO_FOLDER / dir)]
    files_NotEnhanced = [f for f in files if f.stem not in audioProjects]

    for f in files_NotEnhanced:
        enhance_audio_in_chunks(
            input_file=RAW_AUDIO_FOLDER/ f.name,
            output_file=ENHANCED_AUDIO_FOLDER/f.stem/f"{f.stem}.wav",
            raw_chunk_dir=ENHANCED_AUDIO_FOLDER/f.stem/"RawAudioChunk",
            enhanced_chunk_dir=ENHANCED_AUDIO_FOLDER/f.stem/"enhancedAudioChunk",
            chunk_duration=60*15,
            lowcut=100,
            highcut=6000,
            compress_threshold_db=-30,
            compress_ratio=4,
            gain_db=8,
        )

    for f in files:
        transcribe_audio(ENHANCED_AUDIO_FOLDER/f.stem/f"{f.stem}.wav", model_size="medium",
                         save_to=OUTPUT_TRANSCRIPT/f.stem/"transcript.md")

if __name__ == '__main__':
        # ProcessVideo()
        ProcessAudio()


