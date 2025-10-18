import os
from pathlib import Path

import noisereduce as nr
import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter

from DataProcessing import AUDIO_EXTENSIONS
from DataProcessing.ffmpegUtil import get_audio_settings, AudioFormat
from Utility.Logger import Logger


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
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1)
        return audio_data, sr
    except Exception as e:
        Logger.error(f"Error loading audio chunk '{file_path}': {e}")
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
    try:
        if file_path.endswith((".wav", ".flac", ".ogg")):
            sf.write(file_path, audio_data, sr)
        elif file_path.endswith(".mp3"):
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
    except Exception as e:
        Logger.error(f"Error saving audio to '{file_path}': {e}")
        raise


# === Audio Processing Functions ===
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
    return nr.reduce_noise(y=signal, y_noise=noise_clip, sr=sr)


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


# === Main Enhancement Function ===
def EnhanceAudioFolder(input_dir: Path,
                       out_dir: Path,
                       audio_format: AudioFormat = AudioFormat.WAV,
                       lowcut=80, highcut=8000,
                       compress_threshold_db=-20, compress_ratio=2,
                       gain_db=6,
                       overwrite: bool = False):
    """
    Enhances all audio projects in a folder structure.
    Each project has multiple chunks.
    Skips chunks already processed unless overwrite=True.
    """
    input_dir = Path(input_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    projects = [p for p in input_dir.iterdir() if p.is_dir()]
    if not projects:
        Logger.warning(f"No projects found in '{input_dir}'")
        return

    Logger.info(f"Found {len(projects)} projects to process in '{input_dir}'")
    failed_projects = []

    for project in projects:
        project_name = project.name
        Logger.info(f"Processing project: '{project_name}'")

        project_out_dir = out_dir / project_name
        enhanced_chunk_dir = project_out_dir / "enhanced_chunks"
        enhanced_chunk_dir.mkdir(parents=True, exist_ok=True)

        enhanced_chunks = []
        sr = None

        chunks = sorted([f for f in project.iterdir()
                         if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS])
        if not chunks:
            Logger.warning(f"No audio chunks found in '{project_name}'. Skipping.")
            failed_projects.append(project_name)
            continue

        Logger.info(f"Found {len(chunks)} chunks in '{project_name}'")

        for idx, chunk_file in enumerate(chunks, start=1):
            Logger.info(f"Processing chunk {idx}/{len(chunks)}: '{chunk_file.name}'")

            try:
                enhanced_chunk_file = enhanced_chunk_dir / f"{chunk_file.stem}_enhanced.wav"

                if enhanced_chunk_file.exists() and not overwrite:
                    Logger.info(f"Enhanced chunk exists: '{enhanced_chunk_file.name}'. Skipping.")
                    chunk, sr = load_audio_chunk(enhanced_chunk_file)
                    enhanced_chunks.append(chunk)
                    continue

                chunk, sr = load_audio_chunk(chunk_file)
                enhanced = bandpass_filter(chunk, lowcut, highcut, sr)
                enhanced = reduce_noise_audio(enhanced, sr)
                enhanced = compress_audio(enhanced, threshold_db=compress_threshold_db, ratio=compress_ratio)
                enhanced = boost_volume(enhanced, gain_db)
                enhanced = normalize_audio(enhanced)

                save_audio(enhanced, sr, enhanced_chunk_file)
                enhanced_chunks.append(enhanced)

            except Exception as e:
                Logger.error(f"Error processing chunk '{chunk_file.name}': {e}")
                failed_projects.append(project_name)
                break

        # Save concatenated final audio
        if enhanced_chunks:
            final_audio = np.concatenate(enhanced_chunks)
            final_file = project_out_dir / f"{project_name}.{audio_format.value}"

            if final_file.exists() and not overwrite:
                Logger.info(f"Final file exists for '{project_name}'. Skipping save.")
            else:
                codec, bitrate = get_audio_settings(audio_format)
                save_audio(final_audio, sr, final_file, codec=codec, bitrate=bitrate)
                Logger.info(f"Final enhanced audio saved to: '{final_file}'")

    if failed_projects:
        Logger.warning(f"{len(failed_projects)} projects failed during enhancement:")
        for p in failed_projects:
            Logger.warning(f"  - {p}")
    else:
        Logger.info("All projects enhanced successfully.")
