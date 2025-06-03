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
USER = os.getenv("USER")

import sys
sys.path.append(f"/Users/{USER}/Python/indeXee")
sys.path.append(f"/Users/{USER}/Python/scrapee")

# import my_utils
# import grist_BB
# import grist_PE
# import dbee

from inspect import currentframe
def get_linenumber():
    """
    print line numbers with f"{get_linenumber()}"
    """
    cf = currentframe()
    return cf.f_back.f_lineno

import pprint
pp = pprint.PrettyPrinter(indent=4)
print()
count = 0
count_row = 0

print(f"{os.path.basename(__file__)} boilerplate loaded -----------")
print()
####################
# Generate .srt

import whisper

file_path = '/Users/.....'
output_path = f'/Users/{USER}/Python/transcribee/test/'
language = 'en'

from typing import Iterator, TextIO

def srt_format_timestamp(seconds: float):
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    return (f"{hours}:") + f"{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def write_srt(transcript: Iterator[dict], file: TextIO):
    count = 0
    for segment in transcript:
        count +=1
        print(
            f"{count}\n"
            f"{srt_format_timestamp(segment['start'])} --> {srt_format_timestamp(segment['end'])}\n"
            f"{segment['text'].replace('-->', '->').strip()}\n",
            file=file,
            flush=True,
        )    

model = whisper.load_model("base")
response = model.transcribe(file_path)
    
# save SRT
with open(os.path.join(output_path, os.path.splitext(file_path)[0] + f".{language}.srt"), "w") as srt:
    write_srt(response["segments"], file=srt)



########################################################################################################

if __name__ == '__main__':
    print()
    print()
    print('-------------------------------')
    print(f"{os.path.basename(__file__)}")
    print()
    print(f"{count=}")
    print()
    print('-------------------------------')
    run_time = round((time.time() - start_time), 1)
    if run_time > 60:
        print(f'{os.path.basename(__file__)} finished in {run_time/60} minutes.')
    else:
        print(f'{os.path.basename(__file__)} finished in {run_time}s.')
    print()