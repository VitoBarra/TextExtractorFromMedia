import shutil
from pathlib import Path

from moviepy import VideoFileClip

from DataProcessing import VIDEO_EXTENSIONS


def SplitVideo(input_path: Path, output_dir: Path | None = None, interval_minutes: int = 55):
    """
    Splits the input video into chunks of interval_minutes duration using moviepy.

    Args:
        input_path (Path): Path to the input video file.
        output_dir (Path | None): Directory where output chunks will be stored.
                                  Defaults to a folder named after the input file (without extension).
        interval_minutes (int): Duration of each chunk in minutes. Defaults to 55.
    """
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

    chunk_duration = interval_minutes * 60  # in seconds
    basename = input_path.stem

    # Decide output directory
    output_dir = Path(output_dir) / basename

    # Handle existing output directory
    if output_dir.is_dir():
        confirm = input(f"Output directory '{output_dir}' already exists. Delete and recreate it? [y/N]: ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Aborted.")
            return
        shutil.rmtree(output_dir)
        print("Deleted existing directory.")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Load video
    try:
        clip = VideoFileClip(str(input_path))
    except Exception as e:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise e

    duration = clip.duration  # in seconds
    start = 0
    part = 1

    while start < duration:
        end = min(start + chunk_duration, duration)
        subclip = clip.subclipped(start, end)
        output_file = output_dir / f"{basename}_part{part}.mp4"
        print(f"Creating {output_file} (start at {start:.2f} sec, end at {end:.2f} sec)...")
        subclip.write_videofile(str(output_file), codec="libx264", audio_codec="aac", logger='bar')
        start += chunk_duration
        part += 1

    clip.close()
    print(f"Done! Files are in: {output_dir}")


def SplitVideoInFolder(input_directory: Path, out_dir: Path, interval_minutes: int = 55):
    """
    Splits all video files in a folder into chunks.

    Args:
        input_directory (Path): Path to the folder containing input video files.
        out_dir (Path): Path to the base folder where outputs will be stored.
        interval_minutes (int): Duration of each chunk in minutes. Defaults to 55.
    """
    input_directory = Path(input_directory)
    out_dir = Path(out_dir)

    # Gather all files in the directory that match the allowed extensions
    files_to_process = [
        f for ext in VIDEO_EXTENSIONS
        for f in input_directory.glob(f"*{ext}")
    ]

    if not files_to_process:
        print(f"No allowed media files found in directory: '{input_directory}'")
        return

    print(f"Found {len(files_to_process)} media files to process.")

    for file_path in files_to_process:
        basename = file_path.stem
        expected_output_dir = out_dir / basename

        print(f"\n--- Checking file: {file_path.name} ---")

        if expected_output_dir.is_dir():
            print(f"Output directory '{expected_output_dir}' already exists. Skipping processing.")
            continue  # Skip to the next file

        print(f"Starting processing for: {file_path.name}")
        try:
            SplitVideo(file_path, out_dir, interval_minutes)
        except Exception as e:
            print(f"Error while splitting {file_path.name}: {e}")

    print("\n--- Processing complete ---")
