from datetime import datetime
import os
ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
print(f"\n---------- {ts_time} starting {os.path.basename(__file__)}\n")
import time
start_time = time.time()

from dotenv import load_dotenv
load_dotenv()
DB_BTOB = os.getenv("DB_BTOB")
HF_AUTH_TOKEN = os.getenv("HF_AUTH_TOKEN")

import pprint
pp = pprint.PrettyPrinter(indent=4)

####################
# 2024-11-17  testing WhisperX with diaryzation
# 2024-11-17 16:57 doing speed tests, very slow at the moment (49mns for tiny!)

# IMPORTS

import torch
import whisperx
import os
from pathlib import Path
from tqdm import tqdm

# GLOBALS

troubleshoot = False
model_size = "large-v3"  # Using large-v3 for highest quality
batch_size = 32  # Increased batch size for better performance
compute_type = "float32"  # Can try "float16" for faster processing if you have GPU

print(f"\n\n>>> PROCESSING WITH {model_size} MODEL\n\n")

verbose = True

# FUNCTIONS

def transcribe_audio(video_path):
    """
    Transcribe video using WhisperX without diarization
    Args:
        video_path: Path to video file
    Returns:
        Transcribed text and segments
    """
    step_start = time.time()
    global model_size, verbose, batch_size, compute_type
    
    if verbose:
        print(f"\nStarting transcription of {video_path}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Load WhisperX model
    model = whisperx.load_model(model_size, device, compute_type=compute_type)
    if verbose:
        print(f"ℹ️  Model loaded in {round(time.time() - step_start, 2)}s")
    
    # Load audio
    step_start = time.time()
    audio = whisperx.load_audio(video_path)
    if verbose:
        print(f"ℹ️  Audio loaded in {round(time.time() - step_start, 2)}s")
    
    # Transcribe
    step_start = time.time()
    result = model.transcribe(audio, batch_size=batch_size)
    if verbose:
        print(f"ℹ️  Transcription completed in {round(time.time() - step_start, 2)}s")
    
    return result["segments"]

# MAIN

# video_dir = Path("videos")
video_dir = Path("/Users/nic/Movies/Recordings")
# output_dir = Path("videos")
output_dir = Path("/Users/nic/Movies/Recordings")
output_dir.mkdir(exist_ok=True)

# # Process all video files in directory
# for video_file in video_dir.glob("*.mp4"):

# Get all video files
video_files = list(video_dir.glob("*.mp4"))

# Sort video files by last modified time (most recent first)
video_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)


# Process each video file that doesn't have a transcript
for video_file in video_files:
    if '-KA' in video_file.stem:
        transcript_pattern = f"{video_file.stem}_transcript.txt"
        existing_transcripts = list(output_dir.glob(transcript_pattern))
        
        if existing_transcripts:
            if verbose:
                print(f"\n❌ Skipping {video_file.name} - transcript already exists\n")
            continue

        file_start = time.time()
        print(f"\n\n{datetime.now().strftime('%H:%M:%S')} =============== ℹ️  Processing {video_file.name}...\n")
        
        # Transcribe
        segments = transcribe_audio(str(video_file))
        
        # Write output to file
        output_file = output_dir / f"{video_file.stem}_transcript.txt"
        
        # Write continuous text
        with open(output_file, "w", encoding="utf-8") as f:
            for segment in segments:
                f.write(f"{segment['text']} ")
        
        print(f"\n\n✅ Transcript saved to {output_file}\n\n")
        
        if verbose:
            print(f"Total processing time for {video_file.name}: {round(time.time() - file_start, 2)}s")


# TODO 2024-11-17 17:00 find a way to speed up script - now 49mns for a 33mns video



########################################################################################################

if __name__ == '__main__':

    print('\n\n-------------------------------')
    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')