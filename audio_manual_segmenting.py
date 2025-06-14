from datetime import datetime, timedelta
import os
from pydub import AudioSegment

def extract_segment(input_path, discussion_name, start_min=23, start_sec=0, end_min=48, end_sec=0):
    """
    Extract a segment from an audio file between specified start and end times.
    Times are specified in minutes and seconds.
    """
    print(f"\n{datetime.now().strftime('%H:%M:%S')} Extracting segment from {input_path}...")
    
    # Convert minutes and seconds to milliseconds
    start_ms = (start_min * 60 + start_sec) * 1000
    end_ms = (end_min * 60 + end_sec) * 1000
    
    # Load the audio file
    audio = AudioSegment.from_mp3(input_path)
    
    # Extract the segment
    segment = audio[start_ms:end_ms]
    
    # Generate output filename
    dirname = os.path.dirname(input_path)
    basename = os.path.basename(input_path)
    
    timestamp_str = "_".join(basename.split("_")[:2])
    original_time = datetime.strptime(timestamp_str, "%y%m%d_%H%M")
    new_time = original_time + timedelta(minutes=start_min)
    new_timestamp_str = new_time.strftime("%y%m%d_%H%M")

    output_path = os.path.join(dirname, f"{new_timestamp_str}_{discussion_name}.mp3")
    
    # Export the segment
    segment.export(output_path, format="mp3")
    print(f"\n\n✅ Segment exported to: {output_path}\n\n")
    return output_path
 
if __name__ == "__main__":
    
    input_path = "/Users/nic/aud/250605_0945_voices_clean.mp3"
    discussion_name = "basf"
    start_min = 53
    start_sec = 20
    end_min = 84
    end_sec = 00

    extract_segment(input_path, discussion_name, start_min, start_sec, end_min, end_sec)
