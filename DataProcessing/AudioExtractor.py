import os
from pathlib import Path

from moviepy import VideoFileClip

from DataProcessing import AUDIO_EXTENSIONS
from DataProcessing.ffmpegUtil import AudioFormat, get_audio_settings
from Utility.Logger import info, warning, error


def ExtractAudioFromVideo(input_video_path, output_audio_path=None, audio_format=AudioFormat.WAV):
    """
    Extracts audio from a video file and saves it to an audio file.

    Parameters:
    - input_video_path: str, path to the input video file
    - output_audio_path: str, path to save the extracted audio (optional)
    - audio_format: AudioFormat enum, choose the format (WAV, MP3, FLAC, OGG)
    """
    try:
        video_clip = VideoFileClip(input_video_path)
        audio_clip = video_clip.audio
        if audio_clip is None:
            warning(f"No audio track found in the video '{input_video_path}'.")
            return

        # If no output path, generate one automatically
        if output_audio_path is None:
            base_name = os.path.splitext(os.path.basename(input_video_path))[0]
            output_audio_path = f"{base_name}.{audio_format.value}"

        codec, bitrate = get_audio_settings(audio_format)
        audio_clip.write_audiofile(output_audio_path, codec=codec, bitrate=bitrate)

        audio_clip.close()
        video_clip.close()
        info(f"Audio extracted and saved to '{output_audio_path}' as {audio_format.value.upper()}")

    except Exception as e:
        error(f"An error occurred while extracting audio from '{input_video_path}': {e}")

def VideoFolderToAudio(input_directory: Path,
                       out_dir: Path,
                       audio_format: AudioFormat = AudioFormat.WAV,
                       overwrite: bool = False):
    """
    Extracts audio from all video files in a folder.

    Args:
        input_directory (Path): Folder containing video files.
        out_dir (Path): Base folder where audio outputs will be stored.
        audio_format (AudioFormat): Desired audio format.
        overwrite (bool): If True, overwrite existing audio files.
    """
    input_directory = Path(input_directory)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files_to_process = [f for f in input_directory.iterdir() if f.is_file()]
    if not files_to_process:
        warning(f"No media files found in directory '{input_directory}'.")
        return

    info(f"Found {len(files_to_process)} files to process in '{input_directory}'")

    failed_files = []

    for idx, file_path in enumerate(files_to_process, start=1):
        basename = file_path.stem
        audio_output_path = out_dir / f"{basename}.{audio_format.value}"

        info(f"Processing file [{idx}/{len(files_to_process)}]: {file_path.name}")

        # Skip if any audio file with same basename exists
        existing = list(out_dir.glob(f"{basename}.*"))
        if any(f.suffix.lower() in AUDIO_EXTENSIONS for f in existing) and not overwrite:
            warning(f"An audio file with name '{basename}' already exists. Skipping.")
            continue

        try:
            video_clip = VideoFileClip(str(file_path))
            audio_clip = video_clip.audio

            if audio_clip is None:
                warning(f"No audio track found in '{file_path.name}'. Skipping.")
                video_clip.close()
                failed_files.append(file_path.name)
                continue

            codec, bitrate = get_audio_settings(audio_format)
            audio_clip.write_audiofile(str(audio_output_path), codec=codec, bitrate=bitrate)

            audio_clip.close()
            video_clip.close()
            info(f"Audio extracted to '{audio_output_path.name}'")

        except Exception as e:
            error(f"Error processing '{file_path.name}': {e}")
            failed_files.append(file_path.name)

    info("Audio extraction complete.")
    if failed_files:
        warning(f"{len(failed_files)} files failed to process:")
        for f in failed_files:
            warning(f"  - {f}")
    else:
        info("All files processed successfully.")
