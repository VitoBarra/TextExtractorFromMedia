import os
from pathlib import Path

import noisereduce as nr
import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter

from DataProcessing import AUDIO_EXTENSIONS
from DataProcessing.ffmpegUtil import get_audio_settings, AudioFormat


# === Utility Functions ===
def load_audio_chunk(file_path):
    """
    Load an audio chunk using soundfile.

    Args:
        file_path (str or Path): Path to the audio file.

    Returns:
        tuple: (audio_data as numpy array, sample_rate)
    """
    try:
        audio_data, sr = sf.read(str(file_path), dtype="float32")
        # If stereo, convert to mono
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        return audio_data, sr
    except Exception as e:
        print(f"❌ Error loading audio chunk {file_path}: {e}")
        raise


def save_audio(audio_data, sr, file_path, codec=None, bitrate=None):
    """
    Save a numpy array as an audio file (WAV/MP3/FLAC/OGG).

    Args:
        audio_data (np.ndarray): Audio data to save.
        sr (int): Sample rate.
        file_path (str or Path): Output path.
        codec (str, optional): Codec (from get_audio_settings).
        bitrate (str, optional): Bitrate (only for formats like MP3).
    """
    file_path = str(file_path)

    # WAV/FLAC/OGG can be written directly with soundfile
    if file_path.endswith((".wav", ".flac", ".ogg")):
        sf.write(file_path, audio_data, sr)
    elif file_path.endswith(".mp3"):
        # MP3 requires ffmpeg backend
        import subprocess
        temp_wav = file_path.replace(".mp3", "_temp.wav")
        sf.write(temp_wav, audio_data, sr)
        cmd = ["ffmpeg", "-y", "-i", temp_wav, "-codec:a", codec or "libmp3lame"]
        if bitrate:
            cmd.extend(["-b:a", bitrate])
        cmd.append(file_path)
        subprocess.run(cmd, check=True)
        os.remove(temp_wav)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

# Process function
def butter_bandpass(lowcut, highcut, fs, order=6):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype="band")
    return b, a

def bandpass_filter(data, lowcut, highcut, fs, order=6):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    return lfilter(b, a, data)

def reduce_noise_audio(signal, sr, noise_duration=2):
    noise_clip = signal[: int(noise_duration * sr)]
    reduced = nr.reduce_noise(y=signal, y_noise=noise_clip, sr=sr)
    return reduced

def compress_audio(signal, threshold_db=-30, ratio=4):
    threshold = 10 ** (threshold_db / 20.0)
    compressed = np.copy(signal)
    above_thresh = np.abs(signal) > threshold
    compressed[above_thresh] = np.sign(signal[above_thresh]) * (
        threshold + (np.abs(signal[above_thresh]) - threshold) / ratio
    )
    return compressed

def boost_volume(signal, gain_db=6):
    factor = 10 ** (gain_db / 20)
    return signal * factor

def normalize_audio(signal):
    return signal / np.max(np.abs(signal))


# === Main Chunked Enhancement Function ===
def EnhanceAudioFolder(input_dir: Path,
                       out_dir: Path,
                       audio_format: AudioFormat = AudioFormat.WAV,
                       lowcut=80, highcut=8000,
                       compress_threshold_db=-20, compress_ratio=2,
                       gain_db=6,
                       overwrite: bool = False):
    """
    Enhances all audio projects in a folder structure. Each project has multiple chunks.
    Skips chunks that are already processed unless overwrite=True.
    """
    input_dir = Path(input_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    projects = [p for p in input_dir.iterdir() if p.is_dir()]
    if not projects:
        print(f"⚠️ No projects found in {input_dir}")
        return

    print(f"📂 Found {len(projects)} projects to process in '{input_dir}'")

    failed_projects = []

    for project in projects:
        project_name = project.name
        print(f"\n=== 🎶 Processing project: {project_name} ===")

        project_out_dir = out_dir / project_name
        enhanced_chunk_dir = project_out_dir / "enhanced_chunks"
        enhanced_chunk_dir.mkdir(parents=True, exist_ok=True)

        enhanced_chunks = []
        sr = None

        # 🔑 only process files with extensions defined in AudioFormat
        chunks = sorted([f for f in project.iterdir()
                         if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS])

        if not chunks:
            print(f"⚠️ No audio chunks found in {project_name}. Skipping.")
            failed_projects.append(project_name)
            continue

        print(f"   ➡ Found {len(chunks)} chunks in {project_name}")

        for idx, chunk_file in enumerate(chunks, start=1):
            print(f"   ✂ Chunk {idx}/{len(chunks)}: {chunk_file.name}")

            try:
                # Target enhanced chunk file
                enhanced_chunk_file = enhanced_chunk_dir / f"{chunk_file.stem}_enhanced.wav"

                # Skip if already exists
                if enhanced_chunk_file.exists() and not overwrite:
                    print(f"   ⚠️ Enhanced chunk already exists: {enhanced_chunk_file.name}. Skipping.")
                    chunk, sr = load_audio_chunk(enhanced_chunk_file)  # still load for concatenation
                    enhanced_chunks.append(chunk)
                    continue

                # Load raw chunk
                chunk, sr = load_audio_chunk(chunk_file)

                # Enhance
                enhanced = bandpass_filter(chunk, lowcut, highcut, sr)
                enhanced = reduce_noise_audio(enhanced, sr)
                enhanced = compress_audio(enhanced, threshold_db=compress_threshold_db, ratio=compress_ratio)
                enhanced = boost_volume(enhanced, gain_db)
                enhanced = normalize_audio(enhanced)

                # Save enhanced chunk as WAV (internal processing format)
                save_audio(enhanced, sr, enhanced_chunk_file)

                enhanced_chunks.append(enhanced)

            except Exception as e:
                print(f"   ❌ Error processing {chunk_file.name}: {e}")
                failed_projects.append(project_name)
                break

        # Combine all chunks into final project file
        if enhanced_chunks:
            final_audio = np.concatenate(enhanced_chunks)
            final_file = project_out_dir / f"{project_name}.{audio_format.value}"

            if final_file.exists() and not overwrite:
                print(f"⚠️ Final file already exists for {project_name}. Skipping save.")
            else:
                codec, bitrate = get_audio_settings(audio_format)
                save_audio(final_audio, sr, final_file, codec=codec, bitrate=bitrate)
                print(f"💾 Final enhanced audio saved to: {final_file}")






