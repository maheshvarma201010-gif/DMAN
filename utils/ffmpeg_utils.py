import asyncio
import json
import logging
import os

async def run_command(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        logging.error(f"Command failed: {' '.join(cmd)}")
        logging.error(f"Stderr: {stderr.decode()}")
        return None, stderr.decode()
    return stdout.decode(), None

async def get_audio_track_index(filepath, target_lang):
    """
    Detects the best matching audio track index for the target language.
    target_lang can be 'tamil', 'telugu', 'hindi', 'english', etc.
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
        return None

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return None

    streams = data.get("streams", [])
    audio_tracks = [s for s in streams if s.get("codec_type") == "audio"]

    if not audio_tracks:
        return None

    # Comprehensive language mapping
    lang_map = {
        "tamil": ["tam", "tamil"],
        "telugu": ["tel", "telugu"],
        "hindi": ["hin", "hindi"],
        "english": ["eng", "english", "en"],
        "malayalam": ["mal", "malayalam"],
        "kannada": ["kan", "kannada"]
    }

    target_tags = lang_map.get(target_lang.lower(), [target_lang.lower()[:3]])

    # 1. Match by language tag
    for track in audio_tracks:
        tags = track.get("tags", {})
        lang_tag = tags.get("language", "").lower()
        if lang_tag in target_tags:
            return track.get("index")

    # 2. Match by title tag
    for track in audio_tracks:
        tags = track.get("tags", {})
        title = tags.get("title", "").lower()
        for tag in target_tags:
            if tag in title:
                return track.get("index")

    # 3. Default to first audio track
    return audio_tracks[0].get("index")

async def process_media(input_path, output_path, audio_index):
    """
    FFmpeg command to extract video and selected audio track.
    Optimized for Telegram streaming with faststart.
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-map", "0:v:0",
        "-map", f"0:{audio_index}",
        "-c:v", "copy",
        "-c:a", "aac",
        "-preset", "ultrafast",
        "-movflags", "+faststart",
        output_path
    ]
    stdout, error = await run_command(cmd)
    return error is None
