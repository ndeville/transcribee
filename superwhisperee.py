# SuperWhisperee
# trying to replicate SuperWhisper

# 241001-0607 WORKING

import subprocess
import sounddevice as sd
import whisper
import scipy.io.wavfile as wavfile
import numpy as np
import threading
from pynput import keyboard
from pynput.keyboard import Key, Controller
import time
import warnings

# For pasting
keyb = Controller()

# Set sample rate
sample_rate = 16000  # Sample rate

# Define key for stopping the recording
# STOP_KEY = keyboard.KeyCode.f1
STOP_KEY = Key.f4

# Configuration
ENABLE_AUDIO_SELECTION = False  # Set to False to disable audio device selection
DEFAULT_DEVICE = 6  # Set the default device to 6

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# FUNCTIONS

def write_to_clipboard(output):ho
    process = subprocess.Popen(
        'pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=subprocess.PIPE)
    process.communicate(output.encode('utf-8'))
    print(f"\nOUTPUT COPIED TO CLIPBOARD\n")

def paste():
    with keyb.pressed(Key.cmd):
        keyb.press('f')
        keyb.release('f')

def list_audio_devices():
    print("\nAvailable audio input devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"{i}: {device['name']}")

def get_device_name(device_id):
    devices = sd.query_devices()
    return devices[device_id]['name'] if device_id is not None else "Default"

def record_audio(sample_rate, stop_event, frames, device=None):
    device_name = get_device_name(device)
    print(f"\nRecording started using device: {device_name}")
    print("Press F4 to stop.")
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16', device=device) as stream:
        while not stop_event.is_set():
            data, overflowed = stream.read(1024)
            if overflowed:
                print("Overflow occurred")
            frames.append(data.copy())
    print("\nRecording stopped.")

def save_audio(filename, recording, sample_rate):
    wavfile.write(filename, sample_rate, recording)
    print(f"\nAudio saved to {filename}")

def transcribe_audio(filename):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = whisper.load_model("tiny.en")
        result = model.transcribe(filename)
    return result['text']

# Copy text to clipboard and paste at current mouse position
def copy_and_paste(text):
    write_to_clipboard(text)
    paste()

def main():
    filename = "recording.wav"
    frames = []
    stop_recording_event = threading.Event()
    
    if ENABLE_AUDIO_SELECTION:
        list_audio_devices()
        device_id = input(f"\nEnter the number of the audio device you want to use (or press Enter for default {DEFAULT_DEVICE}): ")
        device = int(device_id) if device_id.strip() else DEFAULT_DEVICE
    else:
        device = DEFAULT_DEVICE

    print(f"Selected audio device: {get_device_name(device)}")

    # Start the recording in a separate thread
    recording_thread = threading.Thread(target=record_audio, args=(sample_rate, stop_recording_event, frames, device))
    recording_thread.start()
    
    # Define the key listener
    def on_press(key):
        if key == STOP_KEY:
            print("\nStop key pressed")
            stop_recording_event.set()
            return False  # Stop the listener

    # Start the key listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # Wait for recording to finish
    recording_thread.join()
    listener.join()
    
    # Record the time when recording stops
    recording_end_time = time.time()
    
    # Process the recorded audio
    if frames:
        recording = np.concatenate(frames, axis=0)
        save_audio(filename, recording, sample_rate)
        # Transcribe the saved audio
        transcription = transcribe_audio(filename)
        print("\nTranscription:")
        print(transcription)
        # Copy transcription to clipboard and paste at current mouse position
        copy_and_paste(transcription)
        print("\n✅ Transcription has been copied to clipboard and pasted at the current mouse position.")
        
        # Calculate and print the processing time
        processing_time = time.time() - recording_end_time
        print(f"\nProcessing time: {processing_time:.2f} seconds")
    else:
        print("No audio recorded.")

if __name__ == "__main__":
    main()



