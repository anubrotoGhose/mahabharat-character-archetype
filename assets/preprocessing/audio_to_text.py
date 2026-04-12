import whisper


def audio_to_text(source_audio_file_path, destination_text_file_path="transcript.txt"):
    model = whisper.load_model("base")
    print(model)
    result = model.transcribe(source_audio_file_path)
    print(result["text"])
    file = open(destination_text_file_path, 'w')
    file.write(result["text"])
    file.close()
    

audio_to_text("/mnt/c/Users/anubr/anu_projects/WebTech/Mahabharat-Character-Analysis/WhatsApp Audio 2025-10-05 at 5.36.34 PM.mp3")