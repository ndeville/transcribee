from datetime import datetime
import os
print("----------")
ts_file = f"{datetime.now().strftime('%y%m%d-%H%M')}"
ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
print(f"{ts_time} starting {os.path.basename(__file__)}")
import time
start_time = time.time()

from dotenv import load_dotenv
load_dotenv()

import pprint
pp = pprint.PrettyPrinter(indent=4)
print()
count = 0
count_row = 0

print(f"{os.path.basename(__file__)} boilerplate loaded -----------")
print()
####################
# Transcribe One File

import whisper
from whisper.utils import get_writer
import warnings
# from whisper.utils import get_writer
import re
import shutil
from collections import namedtuple # to return transcript result as namedtuple
import os, os.path
from pathlib import Path
import sys
import moviepy.editor # to calculate video duration

from openaee_get import ai_transcript_processing


""" TODO

TEST https://github.com/pyannote to diariaze speakers

"""



warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def transcribe_file(file_path,model_size="medium"):

    print(f"\n\n{datetime.now().strftime('%H:%M:%S')} PROCESSING AS SINGLE RECORDING: {file_path}\n\n")

    filepath_parts = Path(file_path).parts
    uid = filepath_parts[-1]
    copy_to_path = os.path.abspath(os.path.join(file_path, os.pardir))

    # Run model
    model = whisper.load_model(model_size)

    # Transcribe the audio file
    result = model.transcribe(file_path)

    # Extract the transcription from the result
    transcript = result['text']

    # print(f"\n\nTranscript:\n{transcript}\n\n")

    # output = transcript

    # output = f"\n{file}\ntranscribed: {ts_db} | {transcribe_language}\n---\n{transcript}\n\n"

    ### txt
    output_file = f"{copy_to_path}/{uid}.txt"
    with open(output_file, 'w') as f:
        print(transcript, file=f)
    print(f"\n{output_file} created.")

    # # Enriched Markdown

    # enriched_transcript = ai_transcript_processing(transcript)

    # final_transcript = f"## RAW TRANSCRIPT\n{file_path}\n\n{transcript}\n\n{enriched_transcript}"

    # output_file = f"/Users/nic/Dropbox/Notes/kaltura/transcripts/{uid}.md"
    # with open(output_file, 'w') as f:
    #     print(final_transcript, file=f)

    # # Copy file to folder /Users/nic/Dropbox/Notes/kaltura/transcripts as Markdown
    # shutil.copy2(output_file, f"/Users/nic/Dropbox/Notes/kaltura/transcripts/{uid}.md")
    # print(f"\n{uid}.md copied to /Users/nic/Dropbox/Notes/kaltura/transcripts/")

    # SRT
    srt_writer = get_writer("srt", copy_to_path)
    srt_output_file = f"{copy_to_path}/{uid}.srt"
    srt_writer(result, srt_output_file)
    print(f"\n{srt_output_file} created.")


    return transcript


########################################################################################################

if __name__ == '__main__':
    print()
    # processing(file=sys.argv[1])
    # language = 'english'

    file_path = input(f"\nEnter file path to transcribe: ")
    model_size = input(f"\nModel size (base.en, small.en, medium, medium.en, large): ")

    transcribe_file(file_path,model_size)

    # transcribe_file('/Users/nic/Movies/Recordings/240831-173202-test.mp4')
    print('-------------------------------')
    print(f"{os.path.basename(__file__)}")
    print()
    print()
    print('-------------------------------')
    run_time = round((time.time() - start_time), 1)
    if run_time > 60:
        print(f'{os.path.basename(__file__)} finished in {run_time/60} minutes.')
    else:
        print(f'{os.path.basename(__file__)} finished in {run_time}s.')
    print()