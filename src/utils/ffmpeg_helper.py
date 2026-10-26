"""FFmpeg execution helper supporting cross-platform binaries and filter graphs."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import imageio_ffmpeg


def get_ffmpeg_binary() -> str:
    """Return path to ffmpeg binary (bundled imageio_ffmpeg or system PATH)."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def run_ffmpeg(cmd_args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run an FFmpeg command with the discovered binary."""
    ffmpeg_bin = get_ffmpeg_binary()
    full_cmd = [ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error"] + cmd_args
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg command failed with returncode {result.returncode}:\n{result.stderr}"
        )
    return result


def get_media_duration(file_path: Path) -> float:
    """Return media file duration in seconds using ffmpeg probe."""
    ffmpeg_bin = get_ffmpeg_binary()
    cmd = [ffmpeg_bin, "-i", str(file_path), "-f", "null", "-"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", res.stderr) or re.search(r"time=(\d+):(\d+):(\d+\.?\d*)", res.stderr)
    if match:
        h, m, s = match.groups()
        return int(h) * 3600 + int(m) * 60 + float(s)
    return 8.0


def create_ambient_music(output_path: Path, duration_seconds: int = 120) -> Path:
    """Generate a soft ambient royalty-free background drone track if no music is provided."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "-f", "lavfi",
        "-i", f"anoisesrc=d={duration_seconds}:c=pink:r=44100:a=0.015,lowpass=f=250",
        "-f", "lavfi",
        "-i", f"sine=frequency=110:duration={duration_seconds}",
        "-f", "lavfi",
        "-i", f"sine=frequency=165:duration={duration_seconds}",
        "-filter_complex",
        "[1:a]volume=0.08[a1];[2:a]volume=0.05[a2];[0:a][a1][a2]amix=inputs=3:duration=first:dropout_transition=2[out]",
        "-map", "[out]",
        "-c:a", "libmp3lame",
        "-b:a", "128k",
        str(output_path),
    ]
    run_ffmpeg(cmd)
    return output_path


def create_ken_burns_clip(
    image_path: Path,
    output_path: Path,
    duration_seconds: float,
    zoom_in: bool = True,
    fps: int = 30,
) -> Path:
    """Create a smooth 1080p Ken Burns zoom/pan video clip from a still image."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames = max(30, int(duration_seconds * fps))
    
    if zoom_in:
        zoom_expr = "zoom+0.0012"
    else:
        zoom_expr = "if(eq(on,1),1.12,zoom-0.0012)"

    filter_str = (
        f"scale=1920:1080:force_original_aspect_ratio=increase,"
        f"crop=1920:1080,"
        f"zoompan=z='min({zoom_expr},1.15)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"
    )

    cmd = [
        "-loop", "1",
        "-i", str(image_path),
        "-vf", filter_str,
        "-t", f"{duration_seconds:.3f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        str(output_path),
    ]
    run_ffmpeg(cmd)
    return output_path
