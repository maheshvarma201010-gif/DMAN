import asyncio
import json
import os
from core.logger import ffmpeg_logger as logger

async def run_command(cmd):
    # Ensure we use the local bin if available
    local_bin = os.path.join(os.getcwd(), "bin")

    # Map 'ffmpeg' and 'ffprobe' to their full paths if they are in our bin
    new_cmd = list(cmd)
    if new_cmd[0] in ["ffmpeg", "ffprobe"]:
        full_path = os.path.join(local_bin, new_cmd[0])
        if os.path.exists(full_path):
            new_cmd[0] = full_path

    process = await asyncio.create_subprocess_exec(
        *new_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        logger.error(f"Command failed: {' '.join(new_cmd)}")
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
    If no video stream exists, it creates one with a black frame (for 'video only' requirement).
    """
    # First, check if video stream exists
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name", "-of", "csv=p=0", input_path
    ]
    stdout, error = await run_command(probe_cmd)
    has_video = bool(stdout and stdout.strip())

    if has_video:
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
    else:
        # No video stream found, but 'video only' is required.
        # Create a black video frame from audio.
        cmd = [
            "ffmpeg",
            "-y",
            "-f", "lavfi", "-i", "color=c=black:s=640x360:r=1", # Static black frame
            "-i", input_path,
            "-map", "0:v:0",
            "-map", f"1:{audio_index}",
            "-c:v", "libx264",         # Need to encode since it's a new stream
            "-tune", "stillimage",
            "-c:a", "aac",
            "-shortest",               # Finish when audio ends
            "-preset", "ultrafast",
            "-movflags", "+faststart",
            output_path
        ]
    stdout, error = await run_command(cmd)
    # FFmpeg often returns non-zero even on minor subtitle mapping warnings,
    # but we should check if output file actually exists.
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True
    return False
