import os
import time
import json
import subprocess
import traceback
import tempfile
from datetime import datetime

os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

print(f"\n---------- {datetime.now().strftime('%H:%M:%S')} starting {os.path.basename(__file__)}")

import torch
from transformers import AutoProcessor, VibeVoiceAsrForConditionalGeneration
from tqdm import tqdm

from dotenv import load_dotenv
load_dotenv()
ANTHROPIC_API_KEY_TRANSCRIBEE = os.getenv("ANTHROPIC_API_KEY_TRANSCRIBEE")

print(f"\n\nStarting {__file__}...\n")


"""CONFIG"""

llm_model = "claude-opus-4-6"
verbose = False
copy_failed_urls = False

MAX_AUDIO_DURATION = 10 * 60  # 10 min chunks to stay within MPS memory limits
OVERLAP_SECONDS = 5  # overlap between chunks for continuity


# VIBEVOICE MODEL LOADING

def load_vibevoice_model():
    """Load VibeVoice ASR model and processor."""
    model_id = "microsoft/VibeVoice-ASR-HF"
    print(f"⏳ Loading VibeVoice model: {model_id}")
    start = time.time()

    processor = AutoProcessor.from_pretrained(model_id)

    if torch.backends.mps.is_available():
        device = "mps"
        model = VibeVoiceAsrForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=torch.float16
        ).to(device)
    elif torch.cuda.is_available():
        device = "cuda"
        model = VibeVoiceAsrForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=torch.bfloat16, device_map="auto"
        )
    else:
        device = "cpu"
        model = VibeVoiceAsrForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=torch.float32
        ).to(device)

    elapsed = time.time() - start
    print(f"✅ Model loaded on {device} in {elapsed:.1f}s")
    return model, processor, device


# AUDIO UTILITIES

def extract_audio_wav(media_path: str, output_path: str, start_sec: float = None, duration_sec: float = None) -> str:
    """Extract audio from media file to 24kHz mono WAV (VibeVoice native sample rate)."""
    cmd = ["ffmpeg", "-y", "-i", media_path]
    if start_sec is not None:
        cmd += ["-ss", str(start_sec)]
    if duration_sec is not None:
        cmd += ["-t", str(duration_sec)]
    cmd += ["-vn", "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1", output_path]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def get_audio_duration_ffprobe(media_path: str) -> float:
    """Get duration in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", media_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def has_audio_stream(filepath: str) -> bool:
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'a',
         '-show_entries', 'stream=index', '-of', 'json', filepath],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    return bool(info.get('streams'))


# TRANSCRIPTION

def transcribe_chunk(model, processor, device, wav_path: str, hotwords: str = None) -> list[dict]:
    """Transcribe a single WAV file, returns list of {Start, End, Speaker, Content}."""
    kwargs = {"audio": wav_path}
    if hotwords:
        kwargs["prompt"] = hotwords

    inputs = processor.apply_transcription_request(**kwargs).to(device, model.dtype)

    with torch.no_grad():
        output_ids = model.generate(**inputs)

    generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]
    transcription = processor.decode(generated_ids, return_format="parsed")[0]
    return transcription


def transcribe_media(model, processor, device, media_path: str, hotwords: str = None) -> list[dict]:
    """Transcribe a media file, handling chunking for files > 55 min."""
    duration = get_audio_duration_ffprobe(media_path)
    segments = []

    with tempfile.TemporaryDirectory() as tmpdir:
        if duration <= MAX_AUDIO_DURATION + 60:
            # Single pass - file fits within limits (with small margin)
            wav_path = os.path.join(tmpdir, "audio.wav")
            extract_audio_wav(media_path, wav_path)
            print(f"  📡 Transcribing single chunk ({duration:.0f}s)", flush=True)
            segments = transcribe_chunk(model, processor, device, wav_path, hotwords)
        else:
            # Multi-chunk processing
            chunk_starts = []
            pos = 0
            while pos < duration:
                chunk_starts.append(pos)
                pos += MAX_AUDIO_DURATION - OVERLAP_SECONDS
            print(f"  📡 Transcribing {len(chunk_starts)} chunks ({duration:.0f}s total)", flush=True)

            for i, start in enumerate(chunk_starts):
                chunk_duration = min(MAX_AUDIO_DURATION, duration - start)
                wav_path = os.path.join(tmpdir, f"chunk_{i}.wav")
                extract_audio_wav(media_path, wav_path, start_sec=start, duration_sec=chunk_duration)
                print(f"  📡 Chunk {i+1}/{len(chunk_starts)}: {start:.0f}s - {start + chunk_duration:.0f}s", flush=True)

                chunk_segments = transcribe_chunk(model, processor, device, wav_path, hotwords)

                # Offset timestamps and merge
                for seg in chunk_segments:
                    seg["Start"] = round(seg["Start"] + start, 2)
                    seg["End"] = round(seg["End"] + start, 2)

                if i == 0:
                    segments.extend(chunk_segments)
                else:
                    # Skip segments in the overlap zone that duplicate previous chunk
                    overlap_boundary = start + OVERLAP_SECONDS
                    for seg in chunk_segments:
                        if seg["Start"] >= overlap_boundary - 1:
                            segments.append(seg)

    segments.sort(key=lambda s: s["Start"])
    return segments


# OUTPUT FORMATTING

def format_srt_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def segments_to_srt(segments: list[dict], output_path: str) -> str:
    """Write segments to SRT file with speaker labels."""
    with open(output_path, "w", encoding="utf-8") as f:
        idx = 0
        for seg in segments:
            content = seg["Content"].strip()
            if "Speaker" not in seg:
                continue
            idx += 1
            start_ts = format_srt_timestamp(seg["Start"])
            end_ts = format_srt_timestamp(seg["End"])
            speaker = f"Speaker {seg['Speaker']}"
            f.write(f"{idx}\n{start_ts} --> {end_ts}\n[{speaker}] {content}\n\n")
    return output_path


def segments_to_txt(segments: list[dict], output_path: str) -> str:
    """Write segments to plain text file with speaker labels and timestamps."""
    with open(output_path, "w", encoding="utf-8") as f:
        current_speaker = None
        for seg in segments:
            if "Speaker" not in seg:
                continue
            speaker = f"Speaker {seg['Speaker']}"
            content = seg["Content"].strip()
            if not content:
                continue
            mins = int(seg["Start"] // 60)
            secs = int(seg["Start"] % 60)
            if speaker != current_speaker:
                f.write(f"\n[{speaker}] ({mins:02d}:{secs:02d})\n")
                current_speaker = speaker
            f.write(f"{content} ")
        f.write("\n")
    return output_path


# FILE SCANNING

def get_media_files(directories: list[str], extensions: tuple = ('.mp4', '.wav', '.mov', '.mp3', '.MP3', '.m4a')) -> list[str]:
    """Get media files without existing SRT/TXT transcripts."""
    media_files = []
    for directory in directories:
        if not os.path.exists(directory):
            print(f"⚠️  Directory not found: {directory}")
            continue
        for ext in extensions:
            for root, _, files in os.walk(directory):
                for file in tqdm(files, desc=f"Scanning {ext} in {root}"):
                    if file.startswith('.'):
                        continue
                    if file.endswith(ext):
                        media_file = os.path.join(root, file)
                        base_path = os.path.splitext(media_file)[0]
                        if not os.path.exists(base_path + '.srt') and not os.path.exists(base_path + '.txt'):
                            if has_audio_stream(media_file):
                                media_files.append(media_file)
    return sorted(media_files, key=lambda x: os.path.getmtime(x), reverse=True)


# POST-PROCESSING (meeting recaps via LLM)

def _get_claude_response(system_prompt: str, user_prompt: str, llm_model: str) -> str:
    from claude_query import generate_response as generate_response_claude
    return generate_response_claude(system_prompt, user_prompt, model=llm_model, api_key=ANTHROPIC_API_KEY_TRANSCRIBEE)


def post_process_ka(media_file: str, txt_path: str, llm_model: str):
    """Process -KA files: generate meeting recap and append to notes."""
    print(f"\n📝 Processing {media_file} for post-meeting transcription")

    if "internal" in media_file.lower():
        with open("/Users/nic/Dropbox/Notes/ai/prompts/_MeetingRecapInternal.md", 'r', encoding='utf-8') as file:
            system_prompt = file.read()
    else:
        with open("/Users/nic/Dropbox/Notes/ai/prompts/_MeetingFullRecap.md", 'r', encoding='utf-8') as file:
            system_prompt = file.read()

    with open(txt_path, 'r', encoding='utf-8') as file:
        transcript_txt = file.read()
        user_prompt = f"Meeting raw transcript:\n\n{transcript_txt}"

    answer = _get_claude_response(system_prompt, user_prompt, llm_model)

    process = subprocess.Popen("pbcopy", universal_newlines=True, stdin=subprocess.PIPE)
    process.communicate(answer)
    print(f"\n📝 Copied answer to clipboard: {answer}")

    notes_folders = [
        "/Users/nic/Dropbox/Notes/kaltura/clients",
        "/Users/nic/Dropbox/Notes/kaltura/people",
        "/Users/nic/Dropbox/Notes/kaltura/webinars",
    ]

    notes_dict = {}
    for folder in notes_folders:
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith('.md'):
                        notes_dict[os.path.splitext(file)[0].lower()] = os.path.join(root, file)

    keyword = None
    ka_index = media_file.find("-KA")
    if ka_index != -1:
        after_ka = media_file[ka_index + 3:]
        after_ka = os.path.splitext(after_ka.lstrip(' -_'))[0]
        parts = after_ka.replace('_', ' ').split()
        if parts:
            keyword = parts[0]
            print(f"\n📝 Extracted keyword: {keyword}")

    if keyword and keyword.lower() in notes_dict:
        note_path = notes_dict[keyword.lower()]
        if os.path.exists(note_path):
            print(f"📝 Adding to Account note: {keyword}")
            filename = os.path.splitext(os.path.basename(media_file))[0]
            date_str = filename[:6] if len(filename) >= 6 else "YYMMDD"
            try:
                year = int("20" + date_str[:2])
                month = int(date_str[2:4])
                day = int(date_str[4:6])
                date_str = f"{year:04d}-{month:02d}-{day:02d}"
            except (ValueError, IndexError):
                pass
            rest_of_filename = " ".join(parts[1:]) if len(parts) > 1 else ""
            output_to_append = f"\n\n### {date_str} Call with {rest_of_filename}\n\n{answer}"
            with open(note_path, 'a', encoding='utf-8') as file:
                file.write(output_to_append)
        else:
            print(f"❌ Account note not found: {keyword}")


def post_process_vi(media_file: str, txt_path: str, llm_model: str):
    """Process -VI files: generate video summary and append to notes."""
    print(f"\n📝 Processing {media_file} for video summary\n")

    with open("/Users/nic/Dropbox/Notes/ai/prompts/VideoSummary.md", 'r', encoding='utf-8') as file:
        system_prompt = file.read()

    with open(txt_path, 'r', encoding='utf-8') as file:
        transcript_txt = file.read()
        user_prompt = f"Video raw transcript:\n\n{transcript_txt}"

    answer = _get_claude_response(system_prompt, user_prompt, llm_model)

    process = subprocess.Popen("pbcopy", universal_newlines=True, stdin=subprocess.PIPE)
    process.communicate(answer)
    print(f"\n📝 Copied answer to clipboard: {answer}")

    notes_folders = [
        "/Users/nic/Dropbox/Notes/kaltura",
        "/Users/nic/Dropbox/Notes/kaltura/guide/products",
        "/Users/nic/Dropbox/Notes/kaltura/guide/platform",
        "/Users/nic/Dropbox/Notes/kaltura/sko",
    ]

    notes_dict = {}
    for folder in notes_folders:
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith('.md'):
                        notes_dict[os.path.splitext(file)[0].lower()] = os.path.join(root, file)

    keyword = None
    vi_index = media_file.find("-VI")
    if vi_index != -1:
        after_vi = media_file[vi_index + 3:]
        after_vi = os.path.splitext(after_vi.lstrip(' -_'))[0]
        parts = after_vi.replace('_', ' ').split()
        if parts:
            keyword = parts[0]
            print(f"\n📝 Extracted keyword: {keyword}")
            rest_of_filename = " ".join(parts[1:])

    if keyword and keyword.lower() in notes_dict:
        note_path = notes_dict[keyword.lower()]
        if os.path.exists(note_path):
            print(f"📝 Adding to note: {keyword}")
            output_to_append = f"\n\n### {rest_of_filename}\n\n{answer}\n\n\n"
            with open(note_path, 'a', encoding='utf-8') as file:
                file.write(output_to_append)
        else:
            print(f"❌ Note not found: {keyword}")


# MAIN PROCESSING

def process_media_files(media_files: list[str], model, processor, device):
    """Process all media files: transcribe and post-process."""
    for count, media_file in enumerate(media_files):
        duration = get_audio_duration_ffprobe(media_file)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        print(f"\n\n🔊 {datetime.now().strftime('%H:%M')} ======= Processing {count+1}/{len(media_files)} > {media_file} [{minutes}m{seconds}s]\n")

        start_time = time.time()
        try:
            media_file = os.path.abspath(media_file)
            base_path = os.path.splitext(media_file)[0]
            srt_path = base_path + ".srt"
            txt_path = base_path + ".txt"

            # Build hotwords from filename
            hotwords = os.path.splitext(os.path.basename(media_file))[0]
            hotwords = hotwords.replace("-", " ").replace("_", " ")

            # Transcribe
            segments = transcribe_media(model, processor, device, media_file, hotwords=hotwords)

            if not segments:
                print(f"⚠️  No transcription segments returned for {media_file}")
                continue

            # Write outputs
            segments_to_srt(segments, srt_path)
            segments_to_txt(segments, txt_path)
            print(f"✅ SRT: {srt_path}")
            print(f"✅ TXT: {txt_path}")

            # For audio-only files, remove SRT and JSON (keep TXT only)
            if media_file.lower().endswith(('.mp3', '.wav')):
                if os.path.exists(srt_path):
                    os.remove(srt_path)
                    print(f"ℹ️  Deleted SRT file (audio-only): {srt_path}")

            # Post-processing
            if "-KA" in media_file:
                post_process_ka(media_file, txt_path, llm_model)

            if "-VI" in media_file:
                post_process_vi(media_file, txt_path, llm_model)

            run_time = round(time.time() - start_time, 3)
            run_minutes = int(run_time // 60)
            run_seconds = int(run_time % 60)
            ratio = duration / run_time if run_time > 0 else 0
            print(f'\nℹ️  Completed in {run_minutes}m{run_seconds}s ({ratio:.2f}x): {media_file} [{minutes}m{seconds}s]')

        except Exception:
            traceback.print_exc()
            if copy_failed_urls:
                process = subprocess.Popen("pbcopy", universal_newlines=True, stdin=subprocess.PIPE)
                process.communicate(media_file)
            print(f"\n\n❌ ERROR with {media_file}\n\n")
            continue


if __name__ == "__main__":
    script_start = time.time()

    # Load model once
    model, processor, device = load_vibevoice_model()

    directories = [
        "/Users/nic/aud",
        "/Users/nic/vid",
        "/Users/nic/ai/videos",
        "/Users/nic/Dropbox/Kaltura/videos",
    ]

    media_files = get_media_files(directories)

    if not media_files:
        print("\nℹ️  No new media files to process.\n")
    else:
        print(f"\n\nℹ️  Found {len(media_files)} files to process:")
        for i, file in enumerate(media_files):
            print(f"{i+1} > {file}")
        process_media_files(media_files, model, processor, device)

    run_time = round(time.time() - script_start, 3)
    minutes = int(run_time // 60)
    seconds = int(run_time % 60)
    print(f'\nℹ️  {minutes}m{seconds}s total for ALL SRT & TXT files\n')
