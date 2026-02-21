import os, hashlib, base64, asyncio, edge_tts
from groq import Groq

class VoiceEngine:
    def __init__(self, api_key, cache_dir="audio_cache"):
        self.client = Groq(api_key=api_key)
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir): os.makedirs(cache_dir)

    def transcribe(self, audio_bytes):
        """Transcription via Whisper v3 (Vitesse < 200ms)."""
        temp_path = f"t_{hashlib.md5(audio_bytes).hexdigest()}.wav"
        try:
            with open(temp_path, "wb") as f: f.write(audio_bytes)
            with open(temp_path, "rb") as file:
                return self.client.audio.transcriptions.create(
                    file=(temp_path, file.read()),
                    model="whisper-large-v3",
                    language="en"
                ).text
        except: return ""
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)

    async def generate_speech(self, text, voice="en-US-AndrewNeural"):
        """Génération vocale AndrewNeural (le plus réaliste du marché)."""
        hash_name = hashlib.md5(text.encode()).hexdigest()
        filepath = os.path.join(self.cache_dir, f"{hash_name}.mp3")
        
        if not os.path.exists(filepath):
            await edge_tts.Communicate(text, voice).save(filepath)
        
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode()