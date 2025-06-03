
source_video_file = "/Users/nic/Video/test_video.mp4"

from moviepy.editor import VideoFileClip
import os

def extract_audio(video_path, output_dir=None):
    # Get the directory and filename of the source video
    video_dir, video_filename = os.path.split(video_path)
    
    # If no output directory is specified, use the video's directory
    if output_dir is None:
        output_dir = video_dir
    
    # Create the output filename (replace video extension with .mp3)
    audio_filename = os.path.splitext(video_filename)[0] + ".mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    # Load the video file
    video = VideoFileClip(video_path)
    
    # Extract the audio
    audio = video.audio
    
    # Write the audio file
    audio.write_audiofile(audio_path)
    
    # Close the video to release resources
    video.close()
    
    return audio_path

# Extract audio from the source video
extracted_audio_path = extract_audio(source_video_file)
print(f"Audio extracted to: {extracted_audio_path}")
