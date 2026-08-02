import os
from pydub import AudioSegment

for i in range(1, 6):
    path = f"D:/code/MyWord/9.AI重构工业/audio/verse-{i}.mp3"
    if os.path.exists(path):
        audio = AudioSegment.from_file(path)
        print(f"verse-{i}: {len(audio)} ms")
    else:
        print(f"verse-{i}: not found")
