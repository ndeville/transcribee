import os
import time
from datetime import datetime

print(f"\n---------- {datetime.now().strftime('%H:%M:%S')} starting {os.path.basename(__file__)}")

import cv2
import subprocess
import traceback
from mutagen import File as MutagenFile

import subprocess
import json
from tqdm import tqdm

from generate_captions import generate_en_srt

verbose = False
copy_failed_urls = False

print(f"\n\nStarting {__file__}...\n")

"""
250606-0721
Re-transcribe voice memos with German forced as a language
ONLY for audio files witn "_Voices" in the name
"""

# FUNCTIONS

def has_audio_stream(filepath):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'a',
         '-show_entries', 'stream=index', '-of', 'json', filepath],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    return bool(info.get('streams'))



def get_media_duration(media_path):
    """Get the duration of a media file (video or audio) in seconds."""
    try:
        # Get the file extension
        _, ext = os.path.splitext(media_path)
        ext = ext.lower()

        # Handle audio files
        if ext in ('.mp3', '.wav'):
            audio = MutagenFile(str(media_path))
            if audio is None:
                print(f"Error: Could not read audio file {media_path}")
                return 0
            return audio.info.length

        # Handle video files
        elif ext in ('.mp4', '.mov'):
            cap = cv2.VideoCapture(str(media_path))
            if not cap.isOpened():
                print(f"Error: Could not open video file {media_path}")
                return 0
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count/fps
            cap.release()
            return duration
        
        else:
            print(f"Error: Unsupported file format {ext}")
            return 0

    except Exception as e:
        print(f"Error getting duration for {media_path}: {e}")
        return 0


def get_media_files(directories, extensions=('.mp4', '.wav', '.mov', '.mp3')):
    """Get all media files from the given directories that don't have corresponding SRT files."""
    media_files = []
    
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Warning: Directory not found: {directory}")
            continue

        for ext in extensions:
            for root, _, files in os.walk(directory):
                for file in tqdm(files, desc=f"Scanning {ext} files in {root}"):
                    # Skip files that start with a dot
                    if file.startswith('.'):
                        continue
                    if "_Voices" not in file:
                        continue
                    if file.endswith(ext):
                        media_file = os.path.join(root, file)
                        base_path = os.path.splitext(media_file)[0]
                        srt_file = base_path + '_de.srt'
                        txt_file = base_path + '_de.txt'
                        if not os.path.exists(srt_file) and not os.path.exists(txt_file):
                            if has_audio_stream(media_file):
                                media_files.append(media_file)
    
    return sorted(media_files, key=lambda x: os.path.getmtime(x), reverse=True)


def process_media_files(media_files, verbose=False):
    """Process media files and generate SRT files using generate_en_srt."""
    
    for count_media, media_file in enumerate(media_files):
        duration = get_media_duration(media_file)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        print(f"\n\n🔊 {datetime.now().strftime('%H:%M')} ======= Processing {count_media+1}/{len(media_files)} > {media_file} [{minutes}m{seconds}s]\n")
        
        start_time = time.time()
        
        try:
            # Convert to absolute path if it isn't already
            media_file = os.path.abspath(media_file)
            
            generate_en_srt(media_file, language="de")

            # Check if the file is an audio file (.mp3 or .wav) and delete the JSON and SRT files
            if media_file.lower().endswith(('.mp3', '.wav')):
                base_name = os.path.splitext(media_file)[0]
                json_file = f"{base_name}.json"
                srt_file = f"{base_name}.srt"
                
                # Delete JSON file if it exists
                if os.path.exists(json_file):
                    os.remove(json_file)
                    print(f"ℹ️  Deleted JSON file: {json_file}")
                
                # Delete SRT file if it exists
                if os.path.exists(srt_file):
                    os.remove(srt_file)
                    print(f"ℹ️  Deleted SRT file: {srt_file}")
            
            # Calculate and display processing time
            run_time = round(time.time() - start_time, 3)
            run_time_minutes = int(run_time // 60)
            run_time_seconds = int(run_time % 60)
            print(f'\nℹ️   Completed in {run_time_minutes}m{run_time_seconds}s ({duration/run_time:.2f}x): {media_file} [{minutes}m{seconds}s]')
                
        except Exception as e:
            # print(f"❌ Error processing {media_file}: {str(e)}")
            traceback.print_exc()

            if copy_failed_urls:
                process = subprocess.Popen("pbcopy", universal_newlines=True, stdin=subprocess.PIPE)
                process.communicate(media_file)            

            # input(f"\n\n❌ ERROR with {media_file}\n\nCopied to clipboard: {media_file}\n\nPress Enter to continue...")
            print(f"\n\n❌ ERROR with {media_file}\n\nCopied to clipboard: {media_file}\n\n")
            continue


# MAIN


# Start Chrono Script
start_time = time.time()

# Define your directories here
directories = [
    "/Users/nic/aud",
    # "/Users/nic/vid",
    # "/Users/nic/Dropbox/Kaltura/videos",
]

# Get list of media files that need processing
media_files = get_media_files(directories)

if not media_files:
    print("\n ℹ️  No new media files to process.\n")
else:
    print(f"Found {len(media_files)} files to process:")
    for count_file, file in enumerate(media_files):
        print(f"{count_file+1} > {file}")

    # Process the files
    process_media_files(media_files)

# End Chrono
run_time = round((time.time() - start_time), 3)
minutes = int(run_time // 60)
seconds = int(run_time % 60)
print(f'\nℹ️  {minutes}m{seconds}s to generate ALL SRT & TXT files\n')

