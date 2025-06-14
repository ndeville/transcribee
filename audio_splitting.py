import time
start_time = time.time()

from pydub import AudioSegment, silence
import os
import sys
from datetime import datetime, timedelta

def split_discussions(input_path, min_silence_len=5000, silence_thresh=-50, keep_silence=500, min_discussion_len_ms=30000):
    """
    - `min_silence_len=1000`: the minimum length (in milliseconds) of a silent section to be considered a split point (here, 1 second).
    - `silence_thresh=-40`: the audio level threshold (in dBFS) below which sound is considered silence (here, anything quieter than –40 dBFS).
    - `keep_silence=500`: how much silence (in milliseconds) to retain at the start and end of each chunk (here, 0.5 seconds).```
    """
    # Extract start timestamp from filename
    filename = os.path.basename(input_path)
    start_time = datetime.strptime(filename[:11], '%y%m%d_%H%M')

    print(f"\n{datetime.now().strftime('%H:%M:%S')} Starting to split {input_path} into discussions...\n")
    
    audio = AudioSegment.from_mp3(input_path)
    chunks = silence.split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=keep_silence
    )
    
    current_position_ms = 0
    
    for chunk in chunks:
        # Only keep chunks longer than 30 seconds (30000 milliseconds)
        if len(chunk) > min_discussion_len_ms:
            # Calculate timestamp for this chunk
            minutes_from_start = current_position_ms / 1000 / 60  # Convert ms to minutes
            chunk_timestamp = start_time + timedelta(minutes=minutes_from_start)
            
            # Use input filename but replace _clean.mp3 with the chunk timestamp
            base_filename = filename.replace("_clean.mp3", "")
            chunk_filename = f"{base_filename}_{chunk_timestamp.strftime('%H%M')}_seg.mp3"
            
            out_path = os.path.join(os.path.dirname(input_path), chunk_filename)
            chunk.export(out_path, format="mp3")
        
        current_position_ms += len(chunk) + min_silence_len  # Add chunk length plus silence



if __name__ == "__main__":

    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')