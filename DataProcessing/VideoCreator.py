from pathlib import Path
from moviepy import AudioFileClip, ColorClip

from DataProcessing import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS
from DataProcessing.ffmpegUtil import get_video_settings, VideoFormat
from Utility.Logger import Logger

VIDEO_SIZE = (1280, 720)
VIDEO_COLOR = (0, 0, 0)  # black


def CreateVideoFromAudio(input_audio_path, output_video_path, video_format=VideoFormat.MP4):
    """
    Converts an audio file to a video file using a black screen.
    """
    try:
        audio_clip = AudioFileClip(input_audio_path)

        # Create black screen clip with same duration as audio
        black_clip = ColorClip(size=VIDEO_SIZE, color=VIDEO_COLOR, duration=audio_clip.duration)
        black_clip = black_clip.with_fps(24).with_audio(audio_clip)

        video_codec, audio_codec = get_video_settings(video_format)
        black_clip.write_videofile(output_video_path, codec=video_codec, audio_codec=audio_codec)

        black_clip.close()
        audio_clip.close()
        Logger.info(f"Video created: {output_video_path}")

    except Exception as e:
        Logger.error(f"An error occurred while creating video from '{input_audio_path}': {e}")
        raise


def AudioFolderToVideo(
    input_directory: Path,
    out_dir: Path,
    video_format: VideoFormat = VideoFormat.MP4,
    overwrite: bool = False,
):
    """
    Converts all audio files in a folder to videos with a black screen.
    Skips if a video with the same base name already exists in any format.
    """
    input_directory = Path(input_directory)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect audio files
    files_to_process = [
        f for f in input_directory.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    ]
    if not files_to_process:
        Logger.warning(f"No audio files found in directory: '{input_directory}'")
        return

    Logger.info(f"Found {len(files_to_process)} files to process in '{input_directory}'")

    failed_files = []

    for idx, file_path in enumerate(files_to_process, start=1):
        basename = file_path.stem
        video_output_path = out_dir / f"{basename}.{video_format.value}"

        Logger.info(f"Processing file [{idx}/{len(files_to_process)}]: {file_path.name}")

        # Skip if a video already exists
        existing = list(out_dir.glob(f"{basename}.*"))
        if any(f.suffix.lower() in VIDEO_EXTENSIONS for f in existing) and not overwrite:
            Logger.info(f"A video with name '{basename}' already exists. Skipping.")
            continue

        try:
            CreateVideoFromAudio(str(file_path), str(video_output_path), video_format=video_format)
        except Exception:
            failed_files.append(file_path.name)

    Logger.info("Audio to video conversion complete.")

    if failed_files:
        Logger.warning(f"{len(failed_files)} files failed to process:")
        for f in failed_files:
            Logger.warning(f"  - {f}")
    else:
        Logger.info("All files processed successfully.")
