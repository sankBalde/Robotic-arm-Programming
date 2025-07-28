import os
import speech_recognition as sr
from pydub import AudioSegment


def convert_m4a_to_wav(input_path: str, output_path: str) -> str:
    """
    Convertit un fichier .m4a (ou tout format supporté par ffmpeg) en fichier .wav.
    Nécessite ffmpeg installé sur la machine.
    """
    # Charge l'audio d'entrée via pydub (ffmpeg)
    audio = AudioSegment.from_file(input_path, format="mp4")
    # Exporte en WAV PCM
    audio.export(output_path, format="wav")
    print(f"Converti : {input_path} → {output_path}")
    return output_path


def transcribe_in_chunks(
    wav_path: str,
    language: str = "fr-FR",
    chunk_duration: int = 10
) -> str:
    """
    Découpe le fichier WAV en segments de 'chunk_duration' secondes
    et renvoie la transcription complète.
    """
    recognizer = sr.Recognizer()
    transcript_parts = []

    with sr.AudioFile(wav_path) as source:
        total_duration = int(source.DURATION)
        print(f"Durée totale : {total_duration}s, découpage en chunks de {chunk_duration}s...")
        for offset in range(0, total_duration, chunk_duration):
            # Enregistrement partiel
            audio_chunk = recognizer.record(source,
                                            duration=chunk_duration,
                                            offset=offset)
            try:
                text = recognizer.recognize_google(audio_chunk, language=language)
                print(f"[Chunk {offset}s - {offset+chunk_duration}s] : {text}")
                transcript_parts.append(text)
            except sr.UnknownValueError:
                print(f"[Chunk {offset}s] : audio incompréhensible.")
            except sr.RequestError as e:
                print(f"[Chunk {offset}s] : erreur API : {e}")

    # Concaténation des parties
    full_transcript = " \n".join(transcript_parts)
    return full_transcript


def save_text_to_file(text: str, output_path: str) -> None:
    """
    Sauvegarde la chaîne 'text' dans 'output_path' (UTF-8). Crée les dossiers si besoin.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Transcription sauvegardée dans : {output_path}")


if __name__ == "__main__":
    # Chemins des fichiers
    input_m4a = "eva_project_son.m4a"
    temp_wav = "temp_audio.wav"
    output_txt = "resultats/transcription.txt"

    # 1. Conversion de .m4a vers .wav
    wav_file = convert_m4a_to_wav(input_m4a, temp_wav)

    # 2. Transcription par segments
    full_text = transcribe_in_chunks(wav_file, language="fr-FR", chunk_duration=10)

    # 3. Enregistrement de la transcription
    save_text_to_file(full_text, output_txt)

    """"# 4. Suppression du fichier temporaire
    try:
        os.remove(temp_wav)
    except OSError:
        pass
    print("Traitement terminé.")"""
