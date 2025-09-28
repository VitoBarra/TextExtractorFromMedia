import argparse

from DataProcessing import RAW_VIDEO_FOLDER, RAW_AUDIO_FOLDER, \
    SPLITTED_AUDIO_FOLDER, HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT, ENHANCED_AUDIO_FOLDER, SPLITTED_VIDEO_FOLDER
from DataProcessing.AudioEnhancer import EnhanceAudioFolder
from DataProcessing.AudioExtractor import AudioFormat, VideoFolderToAudio
from DataProcessing.HTMLToMDConverter import ExtractTextFromFolder
from DataProcessing.MediaSplitter import SplitMediaInFolder
from DataProcessing.VideoCreator import AudioFolderToVideo
from DataProcessing.ffmpegUtil import VideoFormat
from Utility.Logger import setup_logger, console, info
from WebScraper.VzardAIUploader import UploadVideoFolder

# --- Settings ---
HEADLESS_MODE = True

def AudioPipeline(split_minutes: int):
    info("Converting videos to audio...")
    VideoFolderToAudio(RAW_VIDEO_FOLDER, RAW_AUDIO_FOLDER, AudioFormat.WAV, overwrite=False)
    info("Video-to-audio conversion complete.")

    info(f"Splitting audio files into {split_minutes}-minute chunks...")
    SplitMediaInFolder(RAW_AUDIO_FOLDER, SPLITTED_AUDIO_FOLDER, 60 * split_minutes)
    info("Audio splitting complete.")

    info("Enhancing audio files (filtering, compression, gain)...")
    EnhanceAudioFolder(
        SPLITTED_AUDIO_FOLDER,
        ENHANCED_AUDIO_FOLDER,
        AudioFormat.WAV,
        lowcut=100,
        highcut=6000,
        compress_threshold_db=-30,
        compress_ratio=4,
        gain_db=8,
    )
    info("Audio enhancement complete.")

    info("Uploading audio chunks for transcription...")
    jobToDo = True
    while jobToDo:
        jobToDo = not UploadVideoFolder(SPLITTED_AUDIO_FOLDER, HTML_OUTPUT_FOLDER, HEADLESS_MODE)
    info("Upload complete.")

    info("Extracting transcript from uploaded results...")
    ExtractTextFromFolder(HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT)
    info("Transcript extraction complete.")


def VideoPipeline(split_minutes: int):
    info("Converting audio to video...")
    AudioFolderToVideo(RAW_AUDIO_FOLDER, RAW_VIDEO_FOLDER, VideoFormat.MP4, overwrite=False)
    info("Audio-to-video conversion complete.")

    info(f"Splitting videos into {split_minutes}-minute chunks...")
    SplitMediaInFolder(RAW_VIDEO_FOLDER, SPLITTED_VIDEO_FOLDER, 60 * split_minutes)
    info("Video splitting complete.")

    info("Uploading video chunks for transcription...")
    jobToDo = True
    while jobToDo:
        jobToDo = not UploadVideoFolder(SPLITTED_VIDEO_FOLDER, HTML_OUTPUT_FOLDER, HEADLESS_MODE)
    info("Upload complete.")

    info("Extracting transcript from uploaded results...")
    ExtractTextFromFolder(HTML_OUTPUT_FOLDER, OUTPUT_TRANSCRIPT)
    info("Transcript extraction complete.")


def main():
    parser = argparse.ArgumentParser(description="Media Processing Pipelines")
    parser.add_argument(
        "-p", "--pipeline",
        choices=["audio", "video"],
        help="Choose which pipeline to run: 'audio' or 'video'"
    )
    parser.add_argument(
        "-s", "--split",
        type=int,
        default=15,
        help="Split length in minutes for audio/video chunks (default: 30)"
    )
    args = parser.parse_args()

    split_minutes = args.split

    if not args.pipeline:
        console.print("Select a pipeline to run:")
        console.print("1) Audio Pipeline (Video → Audio → Transcript)")
        console.print("2) Video Pipeline (Audio → Video → Transcript)")
        choice = input("Enter choice [1/2]: ").strip()

        if choice == "1":
            args.pipeline = "audio"
        elif choice == "2":
            args.pipeline = "video"
        else:
            console.print("Invalid choice. Exiting.")
            return

    if args.pipeline == "audio":
        info("Starting Audio Pipeline...\n")
        AudioPipeline(split_minutes)
    elif args.pipeline == "video":
        info("Starting Video Pipeline...\n")
        VideoPipeline(split_minutes)


if __name__ == '__main__':
    setup_logger()
    main()
