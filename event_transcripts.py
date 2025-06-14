from datetime import datetime
import os
ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
print(f"\n---------- {ts_time} starting {os.path.basename(__file__)}")
import time
start_time = time.time()

from dotenv import load_dotenv
load_dotenv()
DB_BTOB = os.getenv("DB_BTOB")
DB_MAILINGEE = os.getenv("DB_MAILINGEE")

import pprint
pp = pprint.PrettyPrinter(indent=4)

####################
# TRANSCRIPTS FROM EVENT RECORDINGS 

"""
Goal: copy recordings to dedicated folder, then run script = outputs clean discussions files with timestamps and language(s) + transcriptions
TODO
- indicate what languages were spoken (list, eg ["EN", "DE"])
- cleanup audio (extract vocals)
- split into discussions files (each discussion is a separate file)
- rename files to include time of the day of the recording (start and end) and language
- run Whisperx transcription with automated language detection on each discussion file
"""

250609-1134
NEW PROCES:
- clean audio files with Python below.
- then use ocenaudio to manually idenfify the key segments
- export using audio_manual_segmenting.py
- run below for transcripts + note


# IMPORTS

# import my_utils
# from DB.tools import select_all_records, update_record, create_record, delete_record
from pydub import AudioSegment, silence
import os
import sys
from datetime import datetime, timedelta

from audio_cleaning import clean_audio
from audio_splitting import split_discussions

# GLOBALS


folder_with_event_recordings = "/Users/nic/aud"
event_tag = "voices"

# languages = ["EN", "DE"]

test = 1
verbose = 1

count_row = 0
count_total = 0
count = 0


# FUNCTIONS






# MAIN


# 1/ RUN CLEANING

# for filename in sorted(os.listdir(folder_with_event_recordings)):
#     if event_tag in filename and filename.endswith(".mp3") and not filename.endswith("_clean.mp3"):
#         input_path = os.path.join(folder_with_event_recordings, filename)
#         clean_path = os.path.join(folder_with_event_recordings, filename.replace(".mp3", "_clean.mp3"))
        
#         # Skip if clean version already exists
#         if not os.path.exists(clean_path):
#             print(f"\n{datetime.now().strftime('%H:%M:%S')} processing: {filename}")
#             result = clean_audio(input_path)
            
#             if result:
#                 print(f"Audio cleaning completed! Output: {result}")
#             else:
#                 print(f"Audio cleaning failed for {filename}")
#         else:
#             print(f"\nSkipping {filename} - clean version already exists")



# # 2/ Split clean files into discussions

# for filename in sorted(os.listdir(folder_with_event_recordings)):
#     if event_tag in filename and filename.endswith("_clean.mp3"):
#         input_path = os.path.join(folder_with_event_recordings, filename)
#         output_dir = os.path.join(folder_with_event_recordings)
        
#         # Get timestamp from filename (first 11 chars)
#         timestamp = filename[:11]
        
#         # Check if any segmented version exists with this timestamp
#         has_segments = False
#         for f in os.listdir(output_dir):
#             if f.startswith(timestamp) and "_seg" in f:
#                 has_segments = True
#                 break
        
#         if not has_segments:
#             print(f"\n{datetime.now().strftime('%H:%M:%S')} splitting: {filename}")
#             split_discussions(input_path)
#         else:
#             print(f"\nSkipping {filename} - segmented version already exists")






# 3/ Run Whisperx transcription with automated language detection on each discussion file



# FOR NOW: Run Transcribe All



# 4/ Run OpenAI Assistant to summarize each discussion



from openaee_nic_event_transcript import generate_event_discussion_note

output_folder = f"/Users/nic/Dropbox/Notes/kaltura/events/{event_tag}"

count_discussion_notes = 0

# Process all discussion transcripts
for filename in sorted(os.listdir("/Users/nic/aud")):

    if filename.endswith("_seg.txt") and event_tag in filename:

        count_discussion_notes += 1

        discussion_raw_transcript = os.path.join("/Users/nic/aud", filename)
        discussion_timestamp = filename[:6] + "_" + filename.split("_")[3]

        print(f"\n{datetime.now().strftime('%H:%M:%S')} # {count_discussion_notes} processing: {filename}")

        event_discussion_note = generate_event_discussion_note(discussion_raw_transcript)

        if event_discussion_note:
            # Write discussion note to markdown file
            output_filename = f"{discussion_timestamp}.md"
            output_path = os.path.join(output_folder, output_filename)

            with open(output_path, 'w') as f:
                f.write(event_discussion_note)

            print(f"✅ Discussion note written to: {output_path}")
        else:
            print(f"❌ Failed to generate discussion note for: {filename}")












########################################################################################################

if __name__ == '__main__':
    print('\n\n-------------------------------')
    # print(f"\ncount_row:\t{count_row:,}")
    # print(f"count_total:\t{count_total:,}")
    # print(f"count:\t\t{count:,}")
    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')

















########################################################################################################

if __name__ == '__main__':
    print('\n\n-------------------------------')
    print(f"\ncount_row:\t{count_row:,}")
    print(f"count_total:\t{count_total:,}")
    print(f"count:\t\t{count:,}")
    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')