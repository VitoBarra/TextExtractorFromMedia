import glob
import os
import shutil
from moviepy import VideoFileClip



# Allowed video/audio extensions
ALLOWED_EXTENSIONS = (".mp4", ".mov", ".3gp", ".avi", ".mp3", ".wav", ".m4a", ".mkv")

def split_video_file(input_path: str, interval_minutes: int = 55):
    """
    Splits the input video into chunks of interval_minutes duration using moviepy.

    Args:
        input_path (str): Path to the input video file.
        interval_minutes (int): Duration of each chunk in minutes. Defaults to 55.
    """

    chunk_duration = interval_minutes * 60  # in seconds

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

    filename = os.path.basename(input_path)
    basename, _ = os.path.splitext(filename)
    dirname = os.path.dirname(input_path)
    output_dir = os.path.join(dirname, basename)

    # Handle existing output directory
    if os.path.isdir(output_dir):
        confirm = input(f"Output directory '{output_dir}' already exists. Delete and recreate it? [y/N]: ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Aborted.")
            return
        shutil.rmtree(output_dir)
        print("Deleted existing directory.")

    os.makedirs(output_dir, exist_ok=True)

    # Load video
    clip = VideoFileClip(input_path)
    duration = clip.duration  # in seconds
    start = 0
    part = 1

    while start < duration:
        end = min(start + chunk_duration, duration)
        subclip = clip.subclipped(start, end)
        output_file = os.path.join(output_dir, f"{basename}_part{part}.mp4")
        print(f"Creating {output_file} (start at {start:.2f} sec, end at {end:.2f} sec)...")
        subclip.write_videofile(output_file, codec="libx264", audio_codec="aac", logger='bar')
        start += chunk_duration
        part += 1

    clip.close()
    print(f"Done! Files are in: {output_dir}")



def SplitVideoInFolder(data_directory="data", interval_minutes=55):


    # Gather all files in the directory that match the allowed extensions
    files_to_process = []
    for ext in ALLOWED_EXTENSIONS:
        files_to_process.extend(glob.glob(os.path.join(data_directory, f'*{ext}')))

    if not files_to_process:
        print(f"No allowed media files found in directory: '{data_directory}'")
    else:
        print(f"Found {len(files_to_process)} media files to process.")
        for file_path in files_to_process:
            basename, _ = os.path.splitext(os.path.basename(file_path))
            expected_output_dir = os.path.join(data_directory, basename)

            print(f"\n--- Checking file: {os.path.basename(file_path)} ---")

            if os.path.isdir(expected_output_dir):
                print(f"Output directory '{expected_output_dir}' already exists. Skipping processing.")
                continue  # Skip to the next file in the loop

            print(f"Starting processing for: {os.path.basename(file_path)}")
            try:
                split_video_file(file_path, interval_minutes)
            except Exception as e:
                print(f"Error while splitting {os.path.basename(file_path)}: {e}")

        print("\n--- Processing complete ---")