from enum import Enum
import ffmpeg
from Utility.Logger import Logger


class VideoFormat(Enum):
    MP4 = "mp4"
    AVI = "avi"
    MOV = "mov"
    MKV = "mkv"


class AudioFormat(Enum):
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"


def safe_probe(path: str):
    """
    Safely probe a media file and return metadata.
    Logs detailed error info instead of crashing silently.
    """
    try:
        return ffmpeg.probe(str(path))
    except ffmpeg.Error as e:
        Logger.error(f"FFPROBE ERROR for '{path}':\n{e.stderr.decode(errors='ignore')}")
        raise
    except Exception as e:
        Logger.error(f"Unexpected error while probing '{path}': {e}")
        raise


def get_video_settings(video_format: VideoFormat):
    """
    Returns (video_codec, audio_codec) tuple for the given video format.
    """
    VIDEO_CODEC_MAP = {
        VideoFormat.MP4: ("libx264", "aac"),
        VideoFormat.AVI: ("png", "mp3"),
        VideoFormat.MOV: ("libx264", "aac"),
        VideoFormat.MKV: ("libx264", "aac"),
    }
    return VIDEO_CODEC_MAP.get(video_format, ("libx264", "aac"))


def get_audio_settings(audio_format: AudioFormat):
    """
    Returns (audio_codec, bitrate) tuple for the given audio format.
    """
    AUDIO_CODEC_MAP = {
        AudioFormat.WAV: ("pcm_s16le", None),       # Lossless
        AudioFormat.MP3: ("libmp3lame", "320k"),    # High quality
        AudioFormat.FLAC: ("flac", None),           # Lossless
        AudioFormat.OGG: ("libvorbis", None),       # Good quality
    }
    return AUDIO_CODEC_MAP.get(audio_format, ("pcm_s16le", None))
