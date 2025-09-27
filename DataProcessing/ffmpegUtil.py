from enum import Enum

import ffmpeg


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
    try:
        return ffmpeg.probe(str(path))
    except ffmpeg.Error as e:
        print(f"FFPROBE ERROR for {path}:\n{e.stderr.decode()}")
        raise


def get_video_settings(video_format: VideoFormat):
    """
    Returns the codec and audio codec for the given video format.
    """
    VIDEO_CODEC_MAP = {
        VideoFormat.MP4: ('libx264', 'aac'),
        VideoFormat.AVI: ('png', 'mp3'),  # AVI often uses png video + mp3 audio
        VideoFormat.MOV: ('libx264', 'aac'),
        VideoFormat.MKV: ('libx264', 'aac')
    }
    return VIDEO_CODEC_MAP.get(video_format, ('libx264', 'aac'))


# --- Helper functions ---
def get_audio_settings(audio_format: AudioFormat):
    """
    Returns the codec and optional bitrate for the given audio format.
    """
    AUDIO_CODEC_MAP = {
        AudioFormat.WAV: ('pcm_s16le', None),       # lossless
        AudioFormat.MP3: ('libmp3lame', '320k'),    # high quality
        AudioFormat.FLAC: ('flac', None),           # lossless
        AudioFormat.OGG: ('libvorbis', None)        # good quality
    }
    return AUDIO_CODEC_MAP.get(audio_format, ('pcm_s16le', None))