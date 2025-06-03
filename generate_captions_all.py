import whisperx
# from googletrans import Translator
import torch



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
# 250324-1151 Testing with generating SRT instead of TXT

# IMPORTS

import torch
import whisperx
import os
from pathlib import Path
from tqdm import tqdm

import textwrap


# GLOBALS

troubleshoot = False
model_size = "large-v3"  # Using large-v3 for highest quality
batch_size = 32  # Increased batch size for better performance
compute_type = "float32"  # Can try "float16" for faster processing if you have GPU

print(f"\n\n>>> PROCESSING WITH {model_size} MODEL\n\n")

verbose = True
count = 0

# FUNCTIONS

# def generate_srt(mp4_path, source_lang="EN", output_lang="EN", model_name="large-v3"):
#     source_lang = source_lang.lower()
#     output_lang = output_lang.lower()
#     device = "cuda" if torch.cuda.is_available() else "cpu"
    
#     # Specify compute_type based on device
#     compute_type = "float16" if device == "cuda" else "float32"
#     model = whisperx.load_model(model_name, device, compute_type=compute_type)
#     result = model.transcribe(mp4_path, language=source_lang)
    
#     # The alignment might need to be adjusted depending on the WhisperX version
#     model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
#     result = whisperx.align(result["segments"], model_a, metadata, audio=mp4_path, device=device)
#     segments = result["segments"]

#     def format_timestamp(seconds):
#         hours = int(seconds // 3600)
#         minutes = int((seconds % 3600) // 60)
#         secs = int(seconds % 60)
#         millis = int((seconds - int(seconds)) * 1000)
#         return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
    
#     srt_lines = []
#     for i, seg in enumerate(segments, 1):
#         start = format_timestamp(seg["start"])
#         end = format_timestamp(seg["end"])
#         text = seg["text"].strip()

#         srt_lines.append(str(i))
#         srt_lines.append(f"{start} --> {end}")
#         srt_lines.append(text)
#         srt_lines.append("")
    
#     srt_content = "\n".join(srt_lines)
#     srt_path = mp4_path.rsplit(".", 1)[0] + ".srt"
#     with open(srt_path, "w", encoding="utf-8") as f:
#         f.write(srt_content)
#     print(f"\n\n✅ Captions saved to {srt_path}\n\n")
#     return srt_path


# 250325-0913 Testing with word wrapping
def generate_txt(segments, output_path):
    """Generate a continuous text transcript from segments."""
    with open(output_path, "w", encoding="utf-8") as f:
        for segment in segments:
            f.write(f"{segment['text']} ")
    print(f"\n✅ Text transcript saved to {output_path}\n\n")
    return output_path

def generate_srt(mp4_path, source_lang="EN", output_lang="EN", model_name="large-v3", max_line_length=40):
    source_lang = source_lang.lower()
    output_lang = output_lang.lower()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "float32"

    model = whisperx.load_model(model_name, device, compute_type=compute_type)
    result = model.transcribe(mp4_path, language=source_lang)

    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio=mp4_path, device=device)
    segments = result["segments"]

    def format_timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = format_timestamp(seg["start"])
        end = format_timestamp(seg["end"])
        text = seg["text"].strip()
        wrapped_lines = textwrap.wrap(text, width=max_line_length)

        srt_lines.append(str(i))
        srt_lines.append(f"{start} --> {end}")
        srt_lines.extend(wrapped_lines)
        srt_lines.append("")

    # Store segments for txt generation
    all_segments = segments

    srt_content = "\n".join(srt_lines)
    srt_path = mp4_path.rsplit(".", 1)[0] + ".srt"
    txt_path = mp4_path.rsplit(".", 1)[0] + ".txt"
    
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
    print(f"\n✅ Captions saved to {srt_path}")
    
    # Generate txt file
    generate_txt(all_segments, txt_path)
    
    return srt_path, txt_path




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
        count += 1 
        transcript_pattern = f"{video_file.stem}.srt"
        existing_transcripts = list(output_dir.glob(transcript_pattern))
        
        if existing_transcripts:
            if verbose:
                print(f"\n❌ #{count} skipping {video_file.name} - transcript already exists\n")
            continue

        file_start = time.time()
        print(f"\n\n{datetime.now().strftime('%H:%M:%S')} =============== ℹ️  Processing {video_file.name}...\n")
        
        # Transcribe and get both file paths
        srt_path, txt_path = generate_srt(str(video_file))
        
        # # Write output to file
        # output_file = output_dir / f"{video_file.stem}_transcript.txt"
        
        # # Write continuous text
        # with open(output_file, "w", encoding="utf-8") as f:
        #     for segment in segments:
        #         f.write(f"{segment['text']} ")
        
        # print(f"\n\n✅ Transcript saved to {output_file}\n\n")
        
        if verbose:
            print(f"Total processing time for {video_file.name}: {round((time.time() - file_start)/60, 1)}min")


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