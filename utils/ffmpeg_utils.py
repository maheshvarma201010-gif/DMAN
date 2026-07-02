import asyncio
import json
import os
from core.logger import ffmpeg_logger as logger

async def run_command(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"Stderr: {stderr.decode()}")
        return None, stderr.decode()
    return stdout.decode(), None

async def get_audio_track_index(filepath, target_lang):
    """
    Detects the best matching audio track index for the target language using ffprobe.
    Returns (index, list_of_available_languages)
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        filepath
    ]
    stdout, error = await run_command(cmd)
    if not stdout:
        return None, []

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return None, []

    streams = data.get("streams", [])
    audio_tracks = [s for s in streams if s.get("codec_type") == "audio"]

    if not audio_tracks:
        return None, []

    available_langs = []
    for track in audio_tracks:
        tags = track.get("tags", {})
        lang = tags.get("language") or tags.get("title") or "unknown"
        available_langs.append(lang.lower())

    # Language mapping for common regional languages
    lang_map = {
        "tamil": ["tam", "tamil"],
        "telugu": ["tel", "telugu"],
        "hindi": ["hin", "hindi"],
        "english": ["eng", "english", "en"],
        "malayalam": ["mal", "malayalam"],
        "kannada": ["kan", "kannada"],
        "japanese": ["jpn", "japanese", "jp"]
    }

    target_tags = lang_map.get(target_lang.lower(), [target_lang.lower()[:3]])

    # 1. Attempt to find track by language tag
    for track in audio_tracks:
        tags = track.get("tags", {})
        lang_tag = tags.get("language", "").lower()
        if any(tag == lang_tag for tag in target_tags):
            return track.get("index"), available_langs

    # 2. Attempt to find track by title tag
    for track in audio_tracks:
        tags = track.get("tags", {})
        title = tags.get("title", "").lower()
        for tag in target_tags:
            if tag in title:
                return track.get("index"), available_langs

    return None, available_langs

async def process_media(input_path, output_path, audio_index):
    """
    FFmpeg command to extract video and the selected audio track only.
    Strictly uses stream copy for video. Preservation of subtitles included if available.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-map", "0:v:0",           # First video stream
        "-map", f"0:{audio_index}",  # Selected audio track
        "-map", "0:s?",             # Map subtitles if they exist
        "-c:v", "copy",            # Keep video stream intact
        "-c:a", "aac",             # Encode audio to AAC for maximum compatibility in MP4
        "-c:s", "mov_text",        # Subtitles must be mov_text for MP4 container
        "-preset", "ultrafast",    # Fast processing
        "-movflags", "+faststart",  # Enable streaming for Telegram
        output_path
    ]
    stdout, error = await run_command(cmd)
    # FFmpeg often returns non-zero even on minor subtitle mapping warnings,
    # but we should check if output file actually exists.
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True
    return False
