import json
import soundfile as sf
from vosk import Model, KaldiRecognizer


def offline_transcribe(wav_path, model_path="model-fr-large"):
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)
    data, samplerate = sf.read(wav_path, dtype="int16")

    rec.AcceptWaveform(data.tobytes())
    result = rec.FinalResult()
    return json.loads(result)["text"]


text = offline_transcribe("temp_audio.wav")
with open("resultats/transcription2.txt", "w", encoding="utf-8") as f:
    f.write(text)
