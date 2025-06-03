# from datetime import datetime
# import os
# ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
# ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
# print(f"\n---------- {ts_time} starting {os.path.basename(__file__)}")
# import time
# start_time = time.time()

# from dotenv import load_dotenv
# load_dotenv()
# DB_TWITTER = os.getenv("DB_TWITTER")
# DB_BTOB = os.getenv("DB_BTOB")
# DB_MAILINGEE = os.getenv("DB_MAILINGEE")

# import pprint
# pp = pprint.PrettyPrinter(indent=4)

# ####################
# # SCRIPT_TITLE

# # IMPORTS (script-specific)

# import my_utils
# from DB.tools import select_all_records, update_record, create_record, delete_record

# # GLOBALS

# test = 1
# verbose = 1

# count_row = 0
# count_total = 0
# count = 0


# FUNCTIONS



# MAIN


# Examples of new paths:
# /Users/nic/Library/Containers/com.apple.VoiceMemos/Data/tmp/.com.apple.uikit.itemprovider.temporary.aFafNV/Recording 272.m4a
# /Users/nic/Library/Containers/com.apple.VoiceMemos/Data/tmp/.com.apple.uikit.itemprovider.temporary.GMAdVz/Recording 271.m4a
# /Users/nic/Library/Containers/com.apple.VoiceMemos/Data/tmp/.com.apple.uikit.itemprovider.temporary.S0SvM0/Recording 270.m4a


# chmod -R 755 /Users/nic/Library/Containers/com.apple.VoiceMemos/Data/tmp
# chmod -R 755 /Users/nic/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings


# Reddit
# https://www.reddit.com/r/MacOS/comments/16v0j7y/where_do_i_find_my_voice_memos_in_finder_now/

# Correct folder:
# /Users/nic/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings


import os

def list_files_in_folder(folder_path):
    try:
        # Use the os.listdir() method to get a list of files and directories in the specified folder
        files = os.listdir(folder_path)
        
        # Filter out only the files from the list
        file_list = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]
        
        return file_list
    except FileNotFoundError:
        print(f"The folder '{folder_path}' does not exist.")
        return []


directory = "/Users/nic/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
file_list = list_files_in_folder(directory)

for file in file_list:
    print(file)





########################################################################################################

if __name__ == '__main__':
    print('\n\n-------------------------------')
    print(f"\ncount_row:\t{count_row:,}")
    print(f"count_total:\t{count_total:,}")
    print(f"count:\t{count:,}")
    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')