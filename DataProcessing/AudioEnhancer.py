from pathlib import Path

import ffmpeg
import numpy as np
import soundfile as sf
import os
import tempfile
from scipy.signal import butter, lfilter
import noisereduce as nr

# === Utility Functions ===

def load_audio_chunk(input_file, sr, start_time, duration):
    """Load a small chunk directly from file using ffmpeg to temp WAV."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_wav:
        (
            ffmpeg.input(input_file, ss=start_time, t=duration)
            .output(tmp_wav.name, format='wav', ac=1, ar=sr)
            .run(overwrite_output=True, quiet=True)
        )
        data, sr = sf.read(tmp_wav.name)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, sr

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

def save_audio(signal, sr, filename):
    sf.write(filename, signal, sr)

# === Main Chunked Enhancement Function ===

def enhance_audio_in_chunks(input_file, output_file,
                            chunk_duration=30,
                            lowcut=80, highcut=8000,
                            compress_threshold_db=-20, compress_ratio=2,
                            gain_db=6,
                            raw_chunk_dir="raw_chunks",
                            enhanced_chunk_dir="enhanced_chunks",
                            start_chunk=None,
                            end_chunk=None):
    """
    Enhance Audio/video file in chunks with optional start/end chunk selection.
    """
    os.makedirs(raw_chunk_dir, exist_ok=True)
    os.makedirs(enhanced_chunk_dir, exist_ok=True)

    # Get total duration of the file
    probe = ffmpeg.probe(input_file)
    total_duration = float(probe['format']['duration'])
    sr = 44100
    num_chunks = int(np.ceil(total_duration / chunk_duration))

    # Determine the range of chunks to process
    start_chunk = start_chunk or 0
    end_chunk = end_chunk if end_chunk is not None else num_chunks - 1
    print(f"⏱ Total duration: {total_duration:.2f}s, processing chunks {start_chunk} to {end_chunk}")

    enhanced_chunks = []

    for i in range(start_chunk, end_chunk + 1):
        start_time = i * chunk_duration
        duration = min(chunk_duration, total_duration - start_time)

        print(f"\n✂ Chunk {i+1}/{num_chunks}: {start_time:.2f}s to {start_time+duration:.2f}s")
        chunk, sr = load_audio_chunk(input_file, sr, start_time, duration)

        # Save raw chunk
        raw_chunk_file = Path(raw_chunk_dir)/ f"chunk_{i+1:03d}_raw.wav"
        save_audio(chunk, sr, raw_chunk_file)

        # Enhance chunk
        enhanced = bandpass_filter(chunk, lowcut, highcut, sr)
        enhanced = reduce_noise_audio(enhanced, sr)
        # enhanced = compress_audio(enhanced, threshold_db=compress_threshold_db, ratio=compress_ratio)
        # enhanced = boost_volume(enhanced, gain_db)
        enhanced = normalize_audio(enhanced)

        # Save enhanced chunk
        enhanced_chunk_file = Path(enhanced_chunk_dir) / f"chunk_{i+1:03d}_enhanced.wav"
        save_audio(enhanced, sr, enhanced_chunk_file)

        enhanced_chunks.append(enhanced)

    # Combine enhanced chunks into final Audio
    if enhanced_chunks:
        final_audio = np.concatenate(enhanced_chunks)
        save_audio(final_audio, sr, output_file)
        print(f"\n💾 Final enhanced Audio saved to: {output_file}")
    else:
        print("⚠️ No chunks processed. Check start_chunk/end_chunk parameters.")



