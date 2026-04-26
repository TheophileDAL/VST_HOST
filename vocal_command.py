import json
import asyncio
import sounddevice as sd
from vosk import Model, KaldiRecognizer

VALID_COMMANDS = {
    "joue",
    "suivant", "suite", "suivre",
    "précédent",
    "stop", "stop tout", "tout", "c'est tout", "top", "top tout"
}

class VocalCommand:
    def __init__(self, commands_queue: asyncio.Queue, device_name: str = "USB PnP Sound Device"):
        self.commands_queue = commands_queue
        self.device_name = device_name
        self.stream = None
        self._audio_queue = asyncio.Queue()
        self._loop = None

        device_info = sd.query_devices(device_name, "input")
        self.sr = int(device_info["default_samplerate"])
        self.model = Model(lang="fr")
        self.rec = KaldiRecognizer(self.model, self.sr)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"[VocalCommand] Audio status: {status}")
        try:
            if self._loop:
                self._loop.call_soon_threadsafe(self._audio_queue.put_nowait, bytes(indata))
        except Exception:
            pass

    def start_stream(self):
        self._loop = asyncio.get_event_loop()
        self.stream = sd.RawInputStream(
            samplerate=self.sr,
            blocksize=32000,
            device=self.device_name,
            dtype="int16",
            channels=1,
            callback=self._audio_callback
        )
        self.stream.start()
        print("[VocalCommand] Stream audio démarré.")

    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            print("[VocalCommand] Stream audio arrété.")

    def _normalize(self, text: str) -> str:
        """Normalise le texte pour gérer les probl�émes d'encodage."""
        replacements = {
            "précédent": "précédent",
            "précédent": "précédent",
            "c'est tout": "c'est tout",
        }
        for broken, fixed in replacements.items():
            text = text.replace(broken, fixed)
        return text.strip().lower()

    def _is_valid(self, text: str) -> bool:
        return text in VALID_COMMANDS

    async def listen(self):
        print("listen")
        self.start_stream()
        try:
            while True:
                try:
                    data = await asyncio.wait_for(self._audio_queue.get(), timeout=1.0)
                    accepted = await asyncio.wait_for(
                        asyncio.to_thread(self.rec.AcceptWaveform, data),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    #print("[VocalCommand] Timeout, bloc ignoré")
                    continue
                except Exception as e:
                    #print(f"[VocalCommand] Erreur AcceptWaveform : {e}, bloc ignoré")
                    continue

                if accepted:
                    raw = await asyncio.to_thread(self.rec.Result)
                    text = json.loads(raw).get("text", "")
                    text = self._normalize(text)

                    if text and self._is_valid(text):
                        print(f"[VocalCommand] Commande reconnue : '{text}'")
                        await self.commands_queue.put({"name": "vocal", "command": text})
                    elif text:
                        print(f"[VocalCommand] Ignoré : '{text}'")

        except asyncio.CancelledError:
            print("[VocalCommand] écoute annulée.")
        finally:
            self.stop_stream()