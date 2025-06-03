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

from inspect import currentframe
def get_linenumber():
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
# Transcribee (ex Recordee)
# https://notes.nicolasdeville.com/projects/transcribee

#### DEFAULT PARAMETERS
count_to_do = 100 # can be capped for tests
v = False # verbose flag / can be overridden as a function parameter to be passed
####

import whisper
from whisper.utils import write_srt
import re
import shutil
from collections import namedtuple # to return transcript result as namedtuple
import os, os.path
from pathlib import Path
import sys

line_count_to_do = get_linenumber() - 6 # for referencing count_to_do line number in warning messages

count_recordings = 0
count_processed = 0
count_already_transcribed = 0

def separator(count=50, lines=3, symbol='='):
    separator = f"{symbol * count}" + '\n'
    separator = f"\n{separator * lines}"
    print(separator)


# language = 'english'

def transcribe(file_path, uid):
    global v
    global language

    if v:
        print(f"\n#{get_linenumber()} transcribe {file_path=}")

    # model = whisper.load_model("base")
    # model = whisper.load_model("medium.en") # 220929 testing medium.en and medium
    model = whisper.load_model("medium")
    # response = model.transcribe(file_path) # testing language assignment here instead of .en
    response = model.transcribe(file_path,language='english') 
    text = response["text"]
    language = response["language"]
    srt = response["segments"]
    
    transcript = namedtuple('Transcript', ['text', 'language'])

    final = transcript(text=text, language=language)

    parent_folder = os.path.abspath(os.path.join(file_path, os.pardir))

    # Archive raw
    with open(f"/Users/{USER}/Python/transcribee/raw/{uid}.txt", 'w') as file:
        file.write(f"{final.language}\n{final.text}")

    # write SRT
    with open(f"{parent_folder}/{uid}.srt", 'w', encoding="utf-8") as srt_file:
        write_srt(srt, file=srt_file)
    
    if v:
        print(f'\n#{get_linenumber()} transcript["text"] = {transcript.text}\n')

    return final # namedtuple `transcript``: (transcript.text, transcript.language)




def capitalise_sentence(og_string, v=False):
    if v:
        print(f"\n---start verbose capitalise_sentence (deactivate with v=False)")
        print(f"\n{og_string=}")
    # lowercase everything
    lower_s = og_string.lower()
    if v:
        print(f"\n{lower_s=}")
    # start of string & acronyms
    final = re.sub(r"(\A\w)|"+          # start of string
            "(?<!\.\w)([\.?!] )\w|"+    # after a ?/!/. and a space, 
                                        # but not after an acronym
            "\w(?:\.\w)|"+              # start/middle of acronym
            "(?<=\w\.)\w",              # end of acronym
            lambda x: x.group().upper(), 
            lower_s)
    if v:
        print(f"\nstart_string {final=}")
    # I exception
    if ' i ' in final:
        final = final.replace(' i ', ' I ')
        if v:
            print(f"\n' i ' {final=}")
    if " i'm " in final:
        final = final.replace(" i'm ", " I'm ")
        if v:
            print(f"\n' i'm ' {final=}")
    if v:
        print(f"\nreturned repr(final)={repr(final)}\n\n---end verbose capitalise_sentence\n")
    return final




def clean_beginning_string(string_input, v=False):
    try:
        if string_input not in [None, '', ' ', '-', ' - ', '.']:
            if v:
                print(f"\n---\nclean_beginning_string processing {repr(string_input)}")
            valid = False
            for i in range(1,21): # run enough time
                if valid == False: # run as long as 1st character is not alphabetical
                    first_letter = string_input[0]
                    if not first_letter.isalpha():
                        string_input = string_input[1:]
                        if v:
                            print(f"{string_input}")
                        
                    else:
                        valid = True
                else:
                    break # break loop once 1st character is alphabetical
            # Capitalise
            if not string_input[0].isupper():
                string_output = string_input.replace(string_input[0], string_input[0].upper(), 1) # replace only first occurence of character with capital
            else:
                string_output = string_input
        else:
            string_output = string_input
        if v:
            print(f"{string_output=}")
        return string_output
    except Exception as e:
        print(f"\n\nERROR {e} with {string_input=}")
        return string_input




def clean_transcript(transcript, uid):
    global v

    if v:
        print(f"\n#{get_linenumber()} Transcript to clean:\n{repr(transcript)}\n")

    ### Create dict of replacements
    # if v:
    #     print(f"\n#{get_linenumber()} Creating dict of replacements:\n")
    replacements_file = f"/Users/{USER}/Python/transcribee/replacements.txt"
    replacements = {}
    with open(replacements_file, 'r') as df:
        lines = df.readlines()
        for line in lines:
            if not line.startswith('#'): # remove comments
                # print("line: ", repr(line))
                line_parts = line.split('|')
                if v:
                    print(f"#{get_linenumber()} {line_parts=}")
                replacements[line_parts[0]] = line_parts[1][:-1] # remove trailing \n

    ### Lowercase transcript / helps with replacement logic + clean basis for proper capitalisation
    transcript = transcript.lower()

    ### Remove punctuation
    if ',' in transcript:
        transcript = transcript.replace(',', '')
    if '.' in transcript:
        transcript = transcript.replace('.', '')

    # Replacements
    # if v:
    #     print(f"\n#{get_linenumber()} Processing list of replacements:\n")
    for k,value in replacements.items():
        if v:
            print(f"#{get_linenumber()} replacing {repr(k)} with {repr(value)}")
        if k in transcript:
            if value == '\\n':
                transcript = transcript.replace(k, '\n')
            else:
                transcript = transcript.replace(k, value)
    if v:
        print(f"\n#{get_linenumber()} Processing by lines:\n")
    if '\n' in transcript:
        parts = transcript.split('\n')
        output = []
        for part in parts:
            if v:
                print(f"#{get_linenumber()} {part=}")
            part = clean_beginning_string(part, v=v)
            part = capitalise_sentence(part, v=v)
            part = f"{part}  " # add 2 trailing spaces for Markdown linebreaks
            output.append(part)

        final_output = "\n".join(output)
    else:
        final_output = clean_beginning_string(transcript, v=v)

    # Final cleaning
    if ' / ' in final_output:
        final_output = final_output.replace(' / ', '/')
    if ' .' in final_output:
        final_output = final_output.replace(' .', '.')
    if ' ,' in final_output:
        final_output = final_output.replace(' ,', ',')
    if ' ?' in final_output:
        final_output = final_output.replace(' ?', '?')
    if '??' in final_output:
        final_output = final_output.replace('??', '?')
    if ' :' in final_output:
        final_output = final_output.replace(' :', ':')
    if ' ai ' in final_output:
        final_output = final_output.replace(' ai ', ' AI ')

    if v:
        print(f"\nTranscript cleaned:\n{final_output}\n")

    with open(f"/Users/{USER}/Python/transcribee/processed/{uid}.txt", 'w') as file:
        file.write(final_output)

    return final_output




def add_to_voice_memos_txt(memo_transcript, uid, full_path, transcribe_language):
    global v

    publish_date = f"{uid[:4]}-{uid[4:6]}-{uid[6:8]}"

    # output = f"\n{full_path}\n{publish_date} | {transcribe_language}\n---\n{memo_transcript}\n\n"
    output = f"\n\n> source: {full_path}\n\n\n{memo_transcript}\n"

    # markdown_path = f"/Users/{USER}/Python/homee/internal/voice-memos/{uid}.md"
    # markdown_path = f"/Users/nic/Dropbox/Notes/voice-memos/{uid}.md"
    markdown_path = f"/Users/nic/Dropbox/Notes/voice-memos/{uid[2:8]}.md"

    # If note already exists in voice-memos folder for that day, append to it
    if os.path.exists(markdown_path):
        with open(markdown_path, 'a') as f:
            f.write(output)
    # Else create new note for that day
    else:
        with open(markdown_path, 'w') as f:
            f.write(output)

    # with open(f'/Users/{USER}/Python/homee/voice-memos.txt', 'a') as f:
    #     print(output, file=f)
    





def define_uid(run, full_path, filename):
    if v:
        print(f"\n{get_linenumber()} starting define_uid with:\n{run=}\n{full_path=}\n{filename=}\n")
    if run == "JustPressRecord":
        path_parts = Path(full_path).parts
        parent_folder = path_parts[-2]
        if v:
            print(f"{parent_folder=}")
        if 'icloud' in filename:
            filename_root = filename[1:] # remove leading dot
        else:
            filename_root = filename[:-4]
        uid = f"{parent_folder.replace('-','')}-{filename_root.replace('-','')}"
        if v:
            print(f"{uid=}")

    if run == "Apple":
        filename_root = filename[:-13]
        if v:
            print(f"{filename_root=}")
        uid = filename_root.replace(' ','-')
        if v:
            print(f"{uid=}")
    return uid




def processing(file='', v=v):
    global count_recordings
    global count_processed
    global count_already_transcribed

    if file == 'all':

        """
        FETCH ALL RECORDINGS
        from known Voice Memo folders
        """

        print(f"\n\nPROCESSING ALL RECORDINGS\n\n")

        ### List already transcribed files
        already_transcribed = []
        with open(f'/Users/{USER}/Python/transcribee/log.txt', 'r') as df:
            lines = df.readlines()
            for line in lines:
                if len(line) > 10: # lines with ERRORs
                    already_transcribed.append(line[:15]) # keep only the UID
                else:
                    already_transcribed.append(line[:-1]) # -1 to remove trailing new line
        if v:
            print(f"Already transcribed UIDs:")
            pp.pprint(already_transcribed)
        print()

        folder_paths = [
            # f"/Users/{USER}/Library/Mobile Documents/iCloud~com~openplanetsoftware~just-press-record/Documents", # JustPressRecord / returns partly `.icloud` files
            f"/Users/{USER}/Library/Application Support/com.apple.voicememos/Recordings", # Apple Voice Memos OLD
            f"/Users/{USER}/Library/Containers/com.apple.VoiceMemos/Data", # Apple Voice Memos NEW
            f"/Users/nic/Dropbox/voice-memos", # Apple Voice Memos NEW
        ]

        for folder_path in folder_paths:

            if 'apple.voicememos' in folder_path or 'voice-memos' in folder_path:
                run = 'Apple'
            elif 'just-press-record' in folder_path:
                run = 'JustPressRecord'

            for root, dirs, files in os.walk(folder_path):
                for filename in os.listdir(root):
                    if filename.endswith(".icloud"):
                        count_recordings += 1
                        separator() # prints separator lines for clarity
                        print(f"recording #{count_recordings} iCloud file: {filename} from {run} / SKIPPING\n")

                        uid = define_uid(run, folder_path, filename)

                        ### Log
                        if uid not in already_transcribed:
                            if v:
                                print(f"Adding {uid} as iCloud to log.")
                            with open(f'/Users/{USER}/Python/transcribee/log.txt', 'a') as f:
                                print(f"{uid} ICLOUD FILE", file=f)

                        break

                    if filename.endswith(".m4a"):
                        count_recordings += 1
                        separator() # prints separator lines for clarity
                        print(f"recording #{count_recordings} Processing {filename} from {run}\n")
                        print(f"{filename=}")
                        
                        ### Full Path
                        full_path = os.path.join(root, filename)
                        if v:
                            print(f"{full_path=}")     

                        uid = define_uid(run, full_path, filename)  

                        ### Process if not done already

                        if uid not in already_transcribed:

                            if count_to_do == 0:
                                print(f"\n#{get_linenumber()} NO count_to_do in line {line_count_to_do} / TESTING")

                            elif count_processed < count_to_do:    

                                #### Define copy_to_path for audio file but copy later (only once file processed)
                                copy_to_path = f"/Users/{USER}/Python/transcribee/files/{uid}.m4a"

                                # try:
                                transcribe_object = transcribe(full_path, uid) # returns namedtuple with `text` and `language`
                                if v:
                                    f"#{get_linenumber()} {transcribe_object=}"
                                raw_transcribe = transcribe_object.text
                                if v:
                                    f"#{get_linenumber()} {raw_transcribe=}"
                                transcribe_language = transcribe_object.language
                                if v:
                                    f"#{get_linenumber()} {transcribe_language=}"
                                transcript = clean_transcript(raw_transcribe, uid)
                                if v:
                                    f"#{get_linenumber()} {transcript=}"

                                add_to_voice_memos_txt(transcript, uid, copy_to_path, transcribe_language)

                                    ### Log if successful
                                print(f"Adding {uid} to log.")
                                with open(f'/Users/{USER}/Python/transcribee/log.txt', 'a') as f:
                                    print(uid, file=f)
                                # except Exception as e:
                                #     print(f"\n\nERROR {e} with {run} ID {uid}.")
                                    # with open(f'/Users/{USER}/Python/transcribee/log.txt', 'a') as f:
                                    #     print(f"{uid} ERROR {run}", file=f)

                                ### Copy file to project folder /files now that everything is done
                                
                                if v:
                                    print(f"\nCOPYING FILE:")
                                    print(f"from {full_path}")
                                    print(f"to {copy_to_path}\n")
                                shutil.copy2(full_path, copy_to_path) 

                                count_processed += 1
                                already_transcribed.append(uid)

                        else:
                            print(f"\n{uid} already transcribed.")
                            count_already_transcribed += 1

    elif file.startswith('/Users/') or file.startswith('/Volumes/NicVid/'):

        """
        PROCESS A SINGLE RECORDING
        works in relation with Hazel to process files automatically dropped in specific folders
        """

        print(f"\n\nPROCESSING AS SINGLE RECORDING: {file}\n\n")

        filepath_parts = Path(file).parts
        if v:
            print(f"\n{get_linenumber()} {filepath_parts=} {type(filepath_parts)}")
        uid = filepath_parts[-1]
        if v:
            print(f"\n{get_linenumber()} {uid=}")
        copy_to_path = os.path.abspath(os.path.join(file, os.pardir))
        if v:
            print(f"\n{get_linenumber()} {copy_to_path=}")

        # try:
        transcribe_object = transcribe(file, uid) # returns namedtuple with `text` and `language`
        if v:
            f"\n#{get_linenumber()} {transcribe_object=}"
        raw_transcribe = transcribe_object.text
        if v:
            f"\n#{get_linenumber()} {raw_transcribe=}"
        transcribe_language = transcribe_object.language
        if v:
            f"\n#{get_linenumber()} {transcribe_language=}"
        transcript = clean_transcript(raw_transcribe, uid)
        if v:
            f"\n#{get_linenumber()} {transcript=}"

        output = f"\n{file}\ntranscribed: {ts_db} | {transcribe_language}\n---\n{transcript}\n\n"

        ### txt
        output_file = f"{copy_to_path}/{uid}.txt"
        with open(output_file, 'w') as f:
            print(output, file=f)
        print(f"\n{output_file} created.")


        # # SRT
        # with open(f"{copy_to_path}/{uid}.srt", 'w') as srt:
        #     write_srt(transcribe_object["segments"], file=srt)

    else:
        print(f"{get_linenumber()} WRONG parameter passed. Should be empty or starting with /Users/")

# x = processing('/Users/nic/Downloads/_transcribe/230412-bbc-elon-interview.mp4')
# print(x)




# 2023-12-15 07:05 DOES NOT WORK ANYMORE SINCE 22nd NOV

# New path with no access rights:       
# /Users/nic/Library/Containers/com.apple.VoiceMemos/Data/tmp/.com.apple.uikit.itemprovider.temporary.JcmHtf/Recording 269.m4a
# vs. old path
# /Users/nic/Library/Application Support/com.apple.voicememos/Recordings
# Need to figure out how to get the recordings automatically



########################################################################################################

if __name__ == '__main__':
    print()
    # processing(file=sys.argv[1])
    language = 'english'
    processing('/Users/nic/Movies/Recordings/240724-KA Avolta Meeting.mp4')
    print('-------------------------------')
    print(f"{os.path.basename(__file__)}")
    print()
    print(f"{count_recordings=}")
    print(f"{count_already_transcribed=}")
    print(f"{count_processed=}")
    print()
    print('-------------------------------')
    run_time = round((time.time() - start_time), 1)
    if run_time > 60:
        print(f'{os.path.basename(__file__)} finished in {run_time/60} minutes.')
    else:
        print(f'{os.path.basename(__file__)} finished in {run_time}s.')
    print()