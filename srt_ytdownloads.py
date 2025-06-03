# 250329-1849 RETIRING / RUNNING NOW IN KALTUREE
# 
# # import whisperx
# # from googletrans import Translator
# import torch
# import cv2  # Add this to the imports at the top

# from datetime import datetime
# import os
# ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
# ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
# print(f"\n---------- {ts_time} starting {os.path.basename(__file__)}\n")
# import time
# start_time = time.time()

# from dotenv import load_dotenv
# load_dotenv()
# DB_BTOB = os.getenv("DB_BTOB")
# HF_AUTH_TOKEN = os.getenv("HF_AUTH_TOKEN")

# import pprint
# pp = pprint.PrettyPrinter(indent=4)

# ####################
# # 250326-2233 Create SRT files from MP4 files downloaded from YouTube in dedicated folder /Users/nic/dl/yt

# # IMPORTS

# import torch
# import whisperx
# import os
# from pathlib import Path
# from tqdm import tqdm

# import textwrap


# # GLOBALS

# troubleshoot = False
# # model_size = "large-v3"  # Using large-v3 for highest quality
# # model_size = "turbo"  # Using "turbo" for faster processing in theory. 39mns for a 31mns video.
# model_size = "medium.en"  # 
# """
# Turbo:
# - 32mn for 28mn video
# - 37mn for 28mn video
# - 35mn for 30mns video
# Medium.en:
# - 34mns for 24mns video
# """
# batch_size = 32  # Increased batch size for better performance
# compute_type = "float32"  # Can try "float16" for faster processing if you have GPU

# print(f"\n\n>>> PROCESSING WITH {model_size} MODEL\n\n")

# verbose = True
# count = 0
# count_total = 0

# # FUNCTIONS


# # 250325-0913 Testing with word wrapping
# def generate_txt(segments, output_path):
#     """Generate a continuous text transcript from segments."""
#     with open(output_path, "w", encoding="utf-8") as f:
#         for segment in segments:
#             f.write(f"{segment['text']} ")
#     print(f"\n✅ Text transcript saved to {output_path}\n\n")
#     return output_path

# def generate_srt(mp4_path, source_lang="EN", output_lang="EN", model_name="large-v3", max_line_length=40):
#     source_lang = source_lang.lower()
#     output_lang = output_lang.lower()
#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     compute_type = "float16" if device == "cuda" else "float32"

#     model = whisperx.load_model(model_name, device, compute_type=compute_type)
#     result = model.transcribe(mp4_path, language=source_lang)

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
#         wrapped_lines = textwrap.wrap(text, width=max_line_length)

#         srt_lines.append(str(i))
#         srt_lines.append(f"{start} --> {end}")
#         srt_lines.extend(wrapped_lines)
#         srt_lines.append("")

#     # Store segments for txt generation
#     all_segments = segments

#     srt_content = "\n".join(srt_lines)
#     srt_path = mp4_path.rsplit(".", 1)[0] + ".srt"
#     txt_path = mp4_path.rsplit(".", 1)[0] + ".txt"
    
#     with open(srt_path, "w", encoding="utf-8") as f:
#         f.write(srt_content)
#     print(f"\n✅ Captions saved to {srt_path}")
    
#     # Generate txt file
#     generate_txt(all_segments, txt_path)
    
#     return srt_path, txt_path

# def get_video_duration(video_path):
#     """Get the duration of a video file in seconds."""
#     try:
#         cap = cv2.VideoCapture(str(video_path))
#         if not cap.isOpened():
#             return 0
#         fps = cap.get(cv2.CAP_PROP_FPS)
#         frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         duration = frame_count/fps
#         cap.release()
#         return duration
#     except Exception as e:
#         print(f"Error getting duration for {video_path}: {e}")
#         return 0

# # MAIN

# video_dir = Path("/Users/nic/dl/yt")
# output_dir = Path("/Users/nic/dl/yt")
# output_dir.mkdir(exist_ok=True)

# print("\nScanning for MP4 files...")
# # Get all video files recursively from all subfolders
# video_files = []
# for file in video_dir.rglob("*.mp4"):
#     # Check if an equivalent .srt file already exists
#     srt_file = file.with_suffix('.srt')
#     if not srt_file.exists():
#         video_files.append(file)
#         print(f"Found: {file.relative_to(video_dir)}")

# count_total = len(video_files)

# print(f"\nTotal MP4 files found: {count_total}")

# # Sort video files by duration (longest first)
# video_files.sort(key=lambda x: get_video_duration(x), reverse=True) # reverse=True for longest first

# # # Print duration for each video
# # print("\nVideo durations:")
# # for video_file in video_files:
# #     duration = get_video_duration(video_file)
# #     minutes = int(duration // 60)
# #     seconds = int(duration % 60)
# #     print(f"{video_file.name}: {minutes}m {seconds}s")

# # Process each video file that doesn't have a transcript
# for video_file in video_files:
#     count += 1
#     # Create output paths maintaining the subfolder structure
#     relative_path = video_file.relative_to(video_dir)
#     srt_pattern = output_dir / relative_path.parent / f"{video_file.stem}.srt"
    
#     if srt_pattern.exists():
#         if verbose:
#             print(f"\n❌ #{count} skipping {relative_path} - transcript already exists\n")
#         continue

#     # Create the output directory if it doesn't exist
#     srt_pattern.parent.mkdir(parents=True, exist_ok=True)

#     file_start = time.time()
#     duration = get_video_duration(video_file)
#     minutes = int(duration // 60)
#     seconds = int(duration % 60)
#     print(f"\n\n{datetime.now().strftime('%H:%M:%S')} =============== ℹ️  #{count}/{count_total} processing ({minutes}m {seconds}s) with model size '{model_size}' >>>    /Users/nic/dl/yt/{relative_path}\n")
    
#     # Transcribe and get both file paths
#     try:
#         srt_path, txt_path = generate_srt(str(video_file))
#     except Exception as e:
#         print(f"\n\n\n❌ Error transcribing {video_file}: {e}\n\n\n")
#         continue
    
#     if verbose:
#         print(f"Total processing time for {relative_path}: {round((time.time() - file_start)/60, 1)}min")


# # TODO 2024-11-17 17:00 find a way to speed up script - now 49mns for a 33mns video



# ########################################################################################################

# if __name__ == '__main__':

#     print('\n\n-------------------------------')
#     run_time = round((time.time() - start_time), 3)
#     if run_time < 1:
#         print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
#     elif run_time < 60:
#         print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
#     elif run_time < 3600:
#         print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
#     else:
#         print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')