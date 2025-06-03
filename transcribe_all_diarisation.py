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

troubleshoot = False # True adds model_size to output filename
model_size = "large-v3"
"""
ValueError: Invalid model size 'turbo', expected one of: 
tiny.en in 49mns / WRONG
tiny in 49mns
base.en
base
small.en
small
medium.en
medium in 53mns / 13mns
large-v1
large-v2
large-v3 in 58mns
large
distil-large-v2
distil-medium.en
distil-small.en
"""

print(f"\n\n>>> PROCESSING AS SINGLE RECORDING WITH {model_size}\n\n")

# Add after other globals
verbose = True

# FUNCTIONS


def transcribe_with_diarization(video_path, auth_token):
    """
    Transcribe video with speaker diarization using WhisperX
    Args:
        video_path: Path to video file
        auth_token: HuggingFace authentication token
    Returns:
        List of transcribed segments with speaker labels
    """
    step_start = time.time()
    global model_size, verbose
    
    if verbose:
        print(f"\nStarting transcription of {video_path}")
    
    device = "mps" if torch.cuda.is_available() else "cpu"
    
    # Load WhisperX model
    model = whisperx.load_model(model_size, device, compute_type="float32")
    if verbose:
        print(f"ℹ️  Model loaded in {round(time.time() - step_start, 2)}s")
    
    # Load audio
    step_start = time.time()
    audio = whisperx.load_audio(video_path)
    if verbose:
        print(f"ℹ️  Audio loaded in {round(time.time() - step_start, 2)}s")
    
    # Transcribe
    step_start = time.time()
    result = model.transcribe(audio, batch_size=32)
    if verbose:
        print(f"ℹ️  Transcription completed in {round(time.time() - step_start, 2)}s")
    
    # Write raw transcript to file
    step_start = time.time()
    raw_transcript_path = output_dir / f"{Path(video_path).stem}_raw_transcript.txt"
    
    # Extract full text from segments
    full_text = " ".join([segment["text"] for segment in result["segments"]])
    
    # Write to file
    with open(raw_transcript_path, "w", encoding="utf-8") as f:
        f.write(full_text)
    
    if verbose:
        print(f"ℹ️  Raw transcript written to {raw_transcript_path} in {round(time.time() - step_start, 2)}s")

    
    # Diarization
    step_start = time.time()
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=auth_token, device=device)
    diarize_segments = diarize_model(audio)
    if verbose:
        print(f"ℹ️  Diarization completed in {round(time.time() - step_start, 2)}s")
    
    # Align speakers
    step_start = time.time()
    result = whisperx.assign_word_speakers(diarize_segments, result)
    if verbose:
        print(f"ℹ️  Speaker alignment completed in {round(time.time() - step_start, 2)}s")
    
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
    # Check if any transcript exists (any .txt file starting with video filename)
    # transcript_pattern = f"{video_file.stem}*.txt"
    if '-KA' in video_file.stem:
        transcript_pattern = f"{video_file.stem}_transcript.txt"
        existing_transcripts = list(output_dir.glob(transcript_pattern))
        
        if existing_transcripts:
            if verbose:
                print(f"\n❌ Skipping {video_file.name} - transcript already exists\n")
            continue


        file_start = time.time()
        print(f"\n\n{datetime.now().strftime('%H:%M:%S')} =============== ℹ️  Processing {video_file.name}...\n")
        
        # Transcribe with diarization
        segments = transcribe_with_diarization(str(video_file), HF_AUTH_TOKEN)
        # if troubleshoot:
        #     print(f"\n\n🔍 Segments:")
        #     pp.pprint(segments)
        #     print(f"\n\n")
        
        # Track the previous speaker
        previous_speaker = None

        # Write output to file
        if troubleshoot:
            output_file = output_dir / f"{video_file.stem}_transcript_{model_size}_with_diarization.txt"
        else:
            output_file = output_dir / f"{video_file.stem}_transcript_with_diarization.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            for segment in segments:
                current_speaker = segment.get("speaker", "UNKNOWN")
                text = segment["text"]
                # start = segment["start"]
                # end = segment["end"]
                # f.write(f"[{speaker}] ({start:.2f}s - {end:.2f}s): {text}\n")
                if current_speaker != previous_speaker:
                    f.write(f"\n\n[{current_speaker}] {text}")
                    previous_speaker = current_speaker
                else:
                    f.write(f" {text}")
        
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