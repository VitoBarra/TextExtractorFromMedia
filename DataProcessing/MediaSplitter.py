import ffmpeg
from pathlib import Path
import numpy as np
import shutil
from enum import Enum

from DataProcessing.ffmpegUtil import safe_probe


class MediaMode(Enum):
    AUDIO = "audio"
    VIDEO = "video"


def detect_media_mode(input_path: Path) -> MediaMode:
    """
    Detect whether a file is audio-only or has video.
    """
    probe = safe_probe(str(input_path))
    streams = probe.get("streams", [])

    has_video = any(s["codec_type"] == "video" for s in streams)
    if has_video:
        return MediaMode.VIDEO
    return MediaMode.AUDIO


def split_media(input_path: Path,
                output_dir: Path,
                chunk_duration_s: int,
                mode: MediaMode | None = None,
                audio_sr: int = 44100,
                overwrite: bool = False):
    """
    Split a media file (audio or video) into fixed-duration chunks.

    Args:
        input_path (Path): Input media file.
        output_dir (Path): Output folder where chunks are stored.
        chunk_duration_s (int): Chunk size in seconds.
        mode (MediaMode | None): Explicit mode, or None = auto-detect.
        audio_sr (int): Sample rate for audio mode.
        overwrite (bool): If True, overwrite existing output_dir.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} does not exist.")

    # Auto-detect if not provided
    if mode is None:
        mode = detect_media_mode(input_path)
        print(f"🔍 Auto-detected mode: {mode.value}")

    # Prepare output dir
    basename = input_path.stem
    file_outdir = Path(output_dir) / basename
    if file_outdir.exists() and overwrite:
        shutil.rmtree(file_outdir)
    file_outdir.mkdir(parents=True, exist_ok=True)

    # Probe duration
    probe = ffmpeg.probe(str(input_path))
    duration = float(probe["format"]["duration"])
    num_chunks = int(np.ceil(duration / chunk_duration_s))

    print(f"⏱ {basename}: {duration:.2f}s total, {num_chunks} chunks of {chunk_duration_s}s")

    for i in range(num_chunks):
        start = i * chunk_duration_s
        end = min(start + chunk_duration_s, duration)
        chunk_name = f"{basename}_part{i+1:03d}"

        if mode == MediaMode.VIDEO:
            outfile = file_outdir / f"{chunk_name}.mp4"
            (
                ffmpeg.input(str(input_path), ss=start, t=(end - start))
                      .output(str(outfile), c="copy")
                      .run(overwrite_output=True, quiet=True)
            )
        elif mode == MediaMode.AUDIO:
            outfile = file_outdir / f"{chunk_name}.wav"
            (
                ffmpeg.input(str(input_path), ss=start, t=(end - start))
                      .output(str(outfile), format="wav", ac=1, ar=audio_sr)
                      .run(overwrite_output=True, quiet=True)
            )
        else:
            raise ValueError("Unsupported MediaMode")

        print(f"   ✔ Saved {outfile.name} ({end - start:.2f}s)")

    print(f"✅ Done! Chunks saved in {file_outdir}")



def SplitMediaInFolder(input_directory: Path,
                       out_dir: Path,
                       chunk_duration_s: int,
                       overwrite: bool = False):
    """
    Splits all media files in a folder into chunks (audio or video).

    Args:
        input_directory (Path): Folder containing media files.
        out_dir (Path): Base folder where outputs will be stored.
        chunk_duration_s (int): Duration of each chunk in seconds. Default 30 min.
        overwrite (bool): If True, overwrite existing outputs.
    """
    input_directory = Path(input_directory)
    out_dir = Path(out_dir)

    # Gather all files (basic filter to skip hidden/system files)
    files_to_process = [f for f in input_directory.iterdir() if f.is_file()]

    if not files_to_process:
        print(f"No media files found in directory: '{input_directory}'")
        return

    print(f"📂 Found {len(files_to_process)} files to process in {input_directory}")

    for file_path in files_to_process:
        basename = file_path.stem
        expected_output_dir = out_dir / basename

        print(f"\n--- Checking file: {file_path.name} ---")

        if expected_output_dir.is_dir() and not overwrite:
            print(f"⚠️ Output '{expected_output_dir}' already exists. Skipping.")
            continue

        print(f"▶️ Splitting {file_path.name} ...")
        try:
            split_media(
                input_path=file_path,
                output_dir=out_dir,
                chunk_duration_s=chunk_duration_s,
                mode=None,           # auto-detect (video/audio)
                overwrite=overwrite
            )
        except Exception as e:
            print(f"❌ Error while splitting {file_path.name}: {e}")

    print("\n✅ All processing complete")
