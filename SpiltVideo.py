import os
import shutil
from moviepy import VideoFileClip

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



if __name__ == '__main__':
    split_video_file(os.path.join("data","13-neural Volume.mp4"), 30)