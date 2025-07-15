#!/usr/bin/env python3
"""
Optimize videos for processing to avoid file storage quota issues.
Compresses videos to reduce file size while maintaining quality for analysis.
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_video_info(video_path):
    """Get video file size and duration."""
    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

    # Get duration using ffprobe
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout else 0
    except:
        duration = 0

    return file_size_mb, duration


def compress_video(input_path, output_path, target_size_mb=50):
    """
    Compress video to target size while maintaining quality for AI analysis.

    Args:
        input_path: Path to input video
        output_path: Path for compressed output
        target_size_mb: Target file size in MB (default 50MB)
    """
    file_size_mb, duration = get_video_info(input_path)

    if file_size_mb <= target_size_mb:
        print(f"  ✅ Already under {target_size_mb}MB ({file_size_mb:.1f}MB)")
        return input_path

    print(f"  📦 Compressing {file_size_mb:.1f}MB → ~{target_size_mb}MB")

    # Calculate target bitrate
    if duration > 0:
        # Target bitrate in kbps (leave 10% margin for audio)
        target_bitrate = int((target_size_mb * 8192 * 0.9) / duration)
    else:
        # Fallback bitrate
        target_bitrate = 1000

    # FFmpeg compression command optimized for AI analysis
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-c:v', 'libx264',  # H.264 codec
        '-preset', 'fast',   # Balance speed/compression
        '-crf', '28',        # Quality factor (lower=better, 23 default)
        '-b:v', f'{target_bitrate}k',  # Target video bitrate
        '-maxrate', f'{int(target_bitrate * 1.5)}k',  # Max bitrate
        '-bufsize', f'{int(target_bitrate * 2)}k',    # Buffer size
        '-vf', 'scale=-2:720',  # Scale to 720p max height
        '-c:a', 'aac',      # AAC audio codec
        '-b:a', '128k',     # Audio bitrate
        '-movflags', '+faststart',  # Optimize for streaming
        '-y',  # Overwrite output
        str(output_path)
    ]

    try:
        subprocess.run(cmd, capture_output=True, check=True)
        new_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ✅ Compressed to {new_size_mb:.1f}MB")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Compression failed: {e}")
        return None


def optimize_videos_directory(input_dir, output_dir=None, target_size_mb=50):
    """
    Optimize all videos in a directory.

    Args:
        input_dir: Directory containing videos
        output_dir: Output directory (default: input_dir + '_optimized')
        target_size_mb: Target size per video in MB
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"❌ Directory not found: {input_dir}")
        return

    # Check ffmpeg
    if not check_ffmpeg():
        print("❌ ffmpeg not installed!")
        print("Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)")
        return

    # Set output directory
    if output_dir is None:
        output_path = input_path.parent / f"{input_path.name}_optimized"
    else:
        output_path = Path(output_dir)

    output_path.mkdir(exist_ok=True)

    # Find all video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.MOV', '.MP4']
    video_files = []
    for ext in video_extensions:
        video_files.extend(input_path.glob(f'*{ext}'))

    if not video_files:
        print(f"❌ No video files found in {input_dir}")
        return

    print(f"\n🎥 Found {len(video_files)} videos to optimize")
    print(f"📁 Output directory: {output_path}\n")

    total_original_size = 0
    total_compressed_size = 0

    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] Processing: {video_file.name}")

        output_file = output_path / video_file.name
        original_size = os.path.getsize(video_file) / (1024 * 1024)
        total_original_size += original_size

        # Compress video
        result = compress_video(video_file, output_file, target_size_mb)

        if result:
            compressed_size = os.path.getsize(result) / (1024 * 1024)
            total_compressed_size += compressed_size
        else:
            # Copy original if compression failed
            shutil.copy2(video_file, output_file)
            total_compressed_size += original_size

    # Summary
    print("\n" + "="*50)
    print("📊 OPTIMIZATION SUMMARY")
    print("="*50)
    print(f"Total original size: {total_original_size:.1f}MB")
    print(f"Total compressed size: {total_compressed_size:.1f}MB")
    print(f"Space saved: {total_original_size - total_compressed_size:.1f}MB")
    print(f"Compression ratio: {(1 - total_compressed_size/total_original_size)*100:.1f}%")
    print(f"\n✅ Optimized videos saved to: {output_path}")
    print(f"\nRun processing with: python test_cli.py '{output_path}'")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python optimize_videos.py <video_directory> [target_size_mb]")
        print("Example: python optimize_videos.py test_vids 50")
        sys.exit(1)

    input_dir = sys.argv[1]
    target_size = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    optimize_videos_directory(input_dir, target_size_mb=target_size)


if __name__ == "__main__":
    main()
