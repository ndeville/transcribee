from generate_captions import generate_en_srt
from generate_translation import generate_translated_srt


transcribe_file = input(f"\n> Enter the path to the file: ")


generate_en_srt(transcribe_file, language="en")
# generate_en_srt(transcribe_file)

# srt_path = transcribe_file.replace('.mp4', '.srt')

# target_languages = [
#     "FR",
#     "DE",
#     # "ES",
#     # "PT",
#     # "AR",
#     # "CN",
#     # "IT",
# ]

# for target_lang in target_languages:

#     generate_translated_srt(srt_path, target_lang)

