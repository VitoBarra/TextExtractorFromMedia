import os
from pathlib import Path

import whisper
from whisper import transcribe


def transcribe_audio(audio_path: str, model_size: str = "base", save_to: str = None) -> str:
    """
    Transcribes an audio file using OpenAI Whisper.

    Parameters:
        audio_path (str): Path to the audio file (mp3, wav, m4a, etc.)
        model_size (str): Whisper model size ("tiny", "base", "small", "medium", "large")
        save_to (str): Optional path to save transcription as a .txt file

    Returns:
        str: The transcribed text
    """
    # Load Whisper model
    model = whisper.load_model(model_size)

    # Transcribe audio
    result = transcribe(model, str(audio_path))
    transcription = result["text"]

    os.makedirs(Path(save_to).parent, exist_ok=True)
    # Save to file if requested
    if save_to:
        with open(save_to, "w", encoding="utf-8") as f:
            f.write(transcription)
        print(f"✅ Transcription saved to {save_to}")

    return transcription