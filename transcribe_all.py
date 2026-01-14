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
from openaee_responses_api import generate_response # Generate responses from OpenAI API

print(f"\n\nStarting {__file__}...\n")


"""CONFIG"""

# model = "o3"
model = "gpt-5.2"

verbose = False
copy_failed_urls = False


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


def get_media_files(directories, extensions=('.mp4', '.wav', '.mov', '.mp3', '.MP3')):
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
                    if file.endswith(ext):
                        media_file = os.path.join(root, file)
                        base_path = os.path.splitext(media_file)[0]
                        srt_file = base_path + '.srt'
                        txt_file = base_path + '.txt'
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
            
            srt_path = generate_en_srt(media_file, language=None)

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

            if "-KA" in media_file:

                print(f"\n📝  Processing {media_file} with NicAI for post-meeting transcription")

                with open("/Users/nic/Dropbox/Notes/ai/prompts/_MeetingFullRecap.md", 'r', encoding='utf-8') as file:
                    system_prompt = file.read()

                # Get the .txt version of the srt_path
                txt_path = srt_path.replace('.srt', '.txt')

                with open(txt_path, 'r', encoding='utf-8') as file:
                    transcript_txt = file.read()
                    user_prompt = f"Meeting raw transcript:\n\n{transcript_txt}"

                answer = generate_response(system_prompt, user_prompt, model=model, filters=None, stream=True)

                # Copy the answer to the clipboard
                process = subprocess.Popen("pbcopy", universal_newlines=True, stdin=subprocess.PIPE)
                process.communicate(answer)

                print(f"\n📝  Copied answer to clipboard: {answer}")

                # Add to Note

                notes_folders = [
                    "/Users/nic/Dropbox/Notes/kaltura/clients",
                    "/Users/nic/Dropbox/Notes/kaltura/partners",
                    "/Users/nic/Dropbox/Notes/kaltura/people",
                ]

                # Create a dictionary of all .md files in the notes folders
                notes_dict = {}
                for folder in notes_folders:
                    if os.path.exists(folder):
                        for file in os.listdir(folder):
                            if file.endswith('.md'):
                                filename_without_ext = os.path.splitext(file)[0].lower()
                                full_path = os.path.join(folder, file)
                                notes_dict[filename_without_ext] = full_path

                # Extract keyword from file path (first word following "-KA")
                keyword = None

                ka_index = media_file.find("-KA")
                if ka_index != -1:
                    # Find the part after "-KA"
                    after_ka = media_file[ka_index + 3:]  # +3 to skip "-KA"
                    # Split by common separators and get the first non-empty part
                    parts = after_ka.replace('_', ' ').replace('-', ' ').replace('.', ' ').split()
                    if parts:
                        keyword = parts[0]
                        print(f"\n📝  Extracted keyword: {keyword}")
                
                if keyword:
                    note_path = notes_dict[keyword.lower()]

                    if os.path.exists(note_path):
                        print(f"📝  Adding to Account note: {keyword}")
                        # Extract date from filename (first 6 characters as YYMMDD)
                        filename = os.path.splitext(os.path.basename(media_file))[0]
                        date_str = filename[:6] if len(filename) >= 6 else "YYMMDD"
                        # Convert YYMMDD to YYYY-MM-DD format
                        try:
                            # Parse the 6-character date string (YYMMDD)
                            year = int("20" + date_str[:2])  # Assume 20xx for YY
                            month = int(date_str[2:4])
                            day = int(date_str[4:6])
                            date_str = f"{year:04d}-{month:02d}-{day:02d}"
                        except (ValueError, IndexError):
                            # If parsing fails, keep original date_str
                            pass
                        # Extract the rest of the filename after the keyword
                        rest_of_filename = ""
                        if len(parts) > 1:
                            rest_of_filename = " ".join(parts[1:-1])
                        
                        output_to_append = f"\n\n### {date_str} Call with {rest_of_filename}\n\n{answer}"
                        with open(note_path, 'a') as file:
                            file.write(output_to_append)
                    else:
                        print(f"❌ Account note not found: {keyword}")
            

            if "-VI" in media_file:  # process as video to be processed with Video Summary

                print(f"\n📝  Processing {media_file} with NicAI for VIDeo Summary\n")

                with open("/Users/nic/Dropbox/Notes/ai/prompts/VideoSummary.md", 'r', encoding='utf-8') as file:
                    system_prompt = file.read()

                # Get the .txt version of the srt_path
                txt_path = srt_path.replace('.srt', '.txt')

                with open(txt_path, 'r', encoding='utf-8') as file:
                    transcript_txt = file.read()
                    user_prompt = f"Video raw transcript:\n\n{transcript_txt}"

                answer = generate_response(system_prompt, user_prompt, model=model, filters=None, stream=True)

                # Copy the answer to the clipboard
                process = subprocess.Popen("pbcopy", universal_newlines=True, stdin=subprocess.PIPE)
                process.communicate(answer)

                print(f"\n📝  Copied answer to clipboard: {answer}")

                # Add to Note

                notes_folders = [
                    "/Users/nic/Dropbox/Notes/kaltura",
                    "/Users/nic/Dropbox/Notes/kaltura/guide/products",
                    "/Users/nic/Dropbox/Notes/kaltura/guide/platform",
                ]

                # Create a dictionary of all .md files in the notes folders
                notes_dict = {}
                for folder in notes_folders:
                    if os.path.exists(folder):
                        for file in os.listdir(folder):
                            if file.endswith('.md'):
                                filename_without_ext = os.path.splitext(file)[0].lower()
                                full_path = os.path.join(folder, file)
                                notes_dict[filename_without_ext] = full_path

                # Extract keyword from file path (first word following "-KA")
                keyword = None

                ka_index = media_file.find("-VI")
                if ka_index != -1:
                    # Find the part after "-VI"
                    after_ka = media_file[ka_index + 3:]  # +3 to skip "-VI"
                    # Split by common separators and get the first non-empty part
                    parts = after_ka.replace('_', ' ').replace('-', ' ').replace('.', ' ').split()
                    if parts:
                        keyword = parts[0]
                        print(f"\n📝  Extracted keyword: {keyword}")
                        rest_of_filename = " ".join(parts[1:-1])
                
                if keyword:
                    note_path = notes_dict[keyword.lower()]

                    if os.path.exists(note_path):
                        print(f"📝  Adding to note: {keyword}")
                        
                        output_to_append = f"\n\n### {rest_of_filename}\n\n{answer}\n\n\n"
                        with open(note_path, 'a') as file:
                            file.write(output_to_append)
                    else:
                        print(f"❌ Note not found: {keyword}")



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
    "/Users/nic/vid",
    # "/Users/nic/aud/251007-abb",
    # "/Users/nic/tmp",
    # "/Users/nic/Dropbox/Kaltura/events/intranet_reloaded",
    # "/Users/nic/Dropbox/Kaltura/videos",
]

# Get list of media files that need processing
media_files = get_media_files(directories)

if not media_files:
    print("\n ℹ️  No new media files to process.\n")
else:
    print(f"\n\nℹ️  Found {len(media_files)} files to process:")
    for count_file, file in enumerate(media_files):
        print(f"{count_file+1} > {file}")

    # Process the files
    process_media_files(media_files)

# End Chrono
run_time = round((time.time() - start_time), 3)
minutes = int(run_time // 60)
seconds = int(run_time % 60)
print(f'\nℹ️  {minutes}m{seconds}s to generate ALL SRT & TXT files\n')

