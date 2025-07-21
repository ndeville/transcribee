# Requires: pip install demucs
# Demucs is a more modern and powerful audio separation tool
# Also requires ffmpeg for MP3 conversion

import sys
import os
import shutil
import tempfile
from datetime import datetime

import time
start_time = time.time()


def clean_audio(input_path):
    """
    Separates vocals from an audio file using Demucs and saves as _clean.mp3
    
    Args:
        input_path (str): Path to the input audio file
        
    Returns:
        str: Path to the cleaned audio file if successful, None if failed
    """
    
    # Validate input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file does not exist: {input_path}")
        return None
    
    # Create temporary output directory for demucs processing
    temp_output_dir = tempfile.mkdtemp(prefix="demucs_")
    
    # try:
    # Get input file info
    input_dir = os.path.dirname(input_path)
    input_name = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = f"{input_name}_clean.mp3"
    final_output_path = os.path.join(input_dir, output_filename)

    print(f"Input file: {input_path}")
    print(f"Output will be: {final_output_path}")

    # Run Demucs separation using the command line interface
    # This separates the audio into 4 stems: drums, bass, other, vocals
    cmd = f'python -m demucs.separate "{input_path}" -o "{temp_output_dir}"'
    print(f"Running separation command: {cmd}")

    # Execute the separation command
    exit_code = os.system(cmd)

    if exit_code == 0:
        print(f"Audio separation completed successfully!")
        
        # Find the vocals file in the demucs output structure
        model_dir = os.path.join(temp_output_dir, "htdemucs")
        separated_dir = os.path.join(model_dir, input_name)
        vocals_file = os.path.join(separated_dir, "vocals.wav")
        
        if os.path.exists(vocals_file):
            print(f"Found vocals file: {vocals_file}")
            
            # Convert WAV to MP3 using ffmpeg
            convert_cmd = f'ffmpeg -i "{vocals_file}" -codec:a libmp3lame -b:a 192k "{final_output_path}" -y'
            print(f"Converting to MP3: {convert_cmd}")
            
            convert_exit_code = os.system(convert_cmd)
            
            if convert_exit_code == 0:
                print(f"Successfully created: {final_output_path}")
                return final_output_path
            else:
                print(f"MP3 conversion failed with exit code: {convert_exit_code}")
                print("Make sure ffmpeg is installed: brew install ffmpeg")
                return None
        else:
            print(f"Vocals file not found at: {vocals_file}")
            print(f"Available files in {separated_dir}:")
            if os.path.exists(separated_dir):
                files = os.listdir(separated_dir)
                print(f"  {files}")
            return None
    else:
        print(f"Audio separation failed with exit code: {exit_code}")
        print("Make sure demucs is installed: pip install demucs")
        return None
            
    # finally:
    #     # Clean up temporary files
    #     if os.path.exists(temp_output_dir):
    #         shutil.rmtree(temp_output_dir)
    #         print("Temporary files cleaned up.")







# 250607-1721 TRIED THE BELOW CODE TO OPTIMISE BUT OUTPUT ISN'T BETTER, ALMOST WORSE

# import os
# import torch
# import tempfile
# import subprocess
# import soundfile as sf
# from pydub import AudioSegment
# from demucs.pretrained import get_model
# from demucs.separate import load_track, apply_model

# # max threads on M1 Ultra
# os.environ["OMP_NUM_THREADS"] = str(os.cpu_count())
# os.environ["MKL_NUM_THREADS"] = str(os.cpu_count())

# DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"
# MODEL = get_model(name="htdemucs_6s")
# MODEL.to(DEVICE).eval()

# def clean_audio(input_path: str) -> str:
#     if not os.path.exists(input_path):
#         raise FileNotFoundError(f"Input not found: {input_path}")

#     base, _ = os.path.splitext(input_path)

#     # 1. Denoise with ffmpeg and ensure proper channel count
#     tmp_denoised = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
#     subprocess.run([
#         "ffmpeg", "-y",
#         "-i", input_path,
#         "-af", "afftdn,highpass=f=200,lowpass=f=8000",
#         "-ac", str(MODEL.audio_channels),
#         "-ar", str(MODEL.samplerate),
#         tmp_denoised
#     ], check=True, capture_output=True)

#     # 2. Process in chunks to avoid memory issues
#     import torchaudio
#     info = torchaudio.info(tmp_denoised)
#     sr = info.sample_rate
#     total_frames = info.num_frames
#     chunk_duration_seconds = 300  # 5 minutes
#     chunk_size = chunk_duration_seconds * sr
    
#     processed_chunks = []
#     num_chunks = (total_frames // chunk_size) + 1
    
#     for i, offset in enumerate(range(0, total_frames, chunk_size)):
#         num_frames = min(chunk_size, total_frames - offset)
        
#         print(f"Processing chunk {i + 1}/{num_chunks}...")

#         # Load a chunk
#         wav, current_sr = torchaudio.load(tmp_denoised, frame_offset=offset, num_frames=num_frames)
#         assert sr == current_sr

#         # Ensure stereo
#         if wav.shape[0] == 1:
#             wav = wav.repeat(2, 1)
#         elif wav.shape[0] > 2:
#             wav = wav[:2]
        
#         wav = wav.to(DEVICE)

#         # Apply demucs model
#         with torch.no_grad():
#             estimates = apply_model(
#                 MODEL,
#                 wav.unsqueeze(0),
#                 device=DEVICE,
#                 shifts=4,
#                 split=True,
#                 overlap=0.75,
#                 progress=False,
#             )
        
#         # Extract vocals
#         vocals_idx = MODEL.sources.index('vocals')
#         vocals_chunk = estimates[0, vocals_idx].cpu()
#         processed_chunks.append(vocals_chunk)

#     # Concatenate all processed chunks
#     vocals = torch.cat(processed_chunks, dim=1).T

#     # 3. Write temp WAV and convert to MP3
#     tmp_clean_wav = f"{base}_clean.wav"
#     print("Saving cleaned audio...")
#     sf.write(tmp_clean_wav, vocals, sr, subtype="PCM_24")

#     out_mp3 = f"{base}_clean.mp3"
#     AudioSegment.from_wav(tmp_clean_wav).export(out_mp3, format="mp3", bitrate="320k")

#     # cleanup
#     os.remove(tmp_denoised)
#     os.remove(tmp_clean_wav)

#     return out_mp3









if __name__ == "__main__":

    # clean_audio("/Users/nic/aud/250630-0803-06-intranet-reloaded_TEST.wav")

    # Process all files from Voices in /Users/nic/aud/
    input_dir = "/Users/nic/aud"
    files_to_process = []

    # Collect all files that need processing
    for filename in os.listdir(input_dir):
        if "-intranet-reloaded" in filename and (filename.endswith(".mp3") or filename.endswith(".wav")) and not filename.endswith("_clean.mp3"):
            input_path = os.path.join(input_dir, filename)
            # Always create _clean.mp3 output path regardless of input extension
            clean_path = os.path.join(input_dir, os.path.splitext(filename)[0] + "_clean.mp3")
            
            if not os.path.exists(clean_path):
                files_to_process.append(input_path)
    
    # Sort files alphabetically
    files_to_process.sort()

    total_files = len(files_to_process)

    # Print summary
    print(f"\n\nℹ️  Found {total_files} files to process\n")

    # Process collected files
    for i, input_path in enumerate(files_to_process, 1):
        filename = os.path.basename(input_path)
        print(f"\n\n{datetime.now().strftime('%H:%M:%S')} processing {i}/{total_files}: {filename}\n")
        
        result = clean_audio(input_path)
        if result:
            print(f"✅ Audio cleaning completed: {result}")
        else:
            print(f"❌ Audio cleaning failed for {filename}")


    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')