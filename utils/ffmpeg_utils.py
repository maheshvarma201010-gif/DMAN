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
    target_lang can be 'tam', 'tel', 'hin', 'eng', etc.
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

    data = json.loads(stdout)
    streams = data.get("streams", [])

    audio_tracks = [s for s in streams if s.get("codec_type") == "audio"]
    if not audio_tracks:
        return None

    # Language mapping (basic)
    lang_map = {
        "tamil": "tam",
        "telugu": "tel",
        "hindi": "hin",
        "english": "eng"
    }
    target_tag = lang_map.get(target_lang.lower(), target_lang.lower()[:3])

    # 1. Match by language tag
    for i, track in enumerate(audio_tracks):
        tags = track.get("tags", {})
        if tags.get("language") == target_tag:
            return track.get("index")

    # 2. Match by title tag
    for i, track in enumerate(audio_tracks):
        tags = track.get("tags", {})
        title = tags.get("title", "").lower()
        if target_lang.lower() in title:
            return track.get("index")

    # 3. Default to first audio track if no match found
    return audio_tracks[0].get("index")

async def process_media(input_path, output_path, audio_index):
    """
    FFmpeg command to extract video and selected audio track.
    Outputs as MP4 only.
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
        output_path
    ]
    stdout, error = await run_command(cmd)
    return error is None
