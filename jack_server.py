#JACK SERVER COMMAND FOR I/O
import asyncio
from audio import Audio

JACK_COMMAND = [
    "jackd",
    "-d", "alsa",      # driver ALSA
    "-p", "1024",      # taille du buffer
    "-n", "2",         # nombre de buffers
    "-X", "raw"        # mode MIDI RAW
]

class Jack:

    def __init__(self, audio : Audio):
        self.process: asyncio.subprocess.Process | None = None
        self.audio = audio

    async def start(self):
        device = self.audio.getOutputDevice()

        if device is not None:
            jack_cmd = JACK_COMMAND.copy()
            jack_cmd.extend(["-d", "hw:"+str(device["hw"]), "-r", str(device["samplerate"])])
        else:
            jack_cmd = ["jackd", "-d", "dummy"]

        print(JACK_COMMAND)
        print(jack_cmd)

        self.process = await asyncio.create_subprocess_exec(
            *jack_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.sleep(3)
        print("[JACK SERVER] started")

    async def _get_jack_ports(self):
        proc = await asyncio.create_subprocess_exec(
            "jack_lsp", "-c",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode().splitlines()

        ports = {}
        current_port = None
        for line in lines:
            if line.startswith("   "):
                ports[current_port].append(line.strip())
            else:                        # port
                current_port = line.strip()
                ports[current_port] = []

        return ports

    async def _jack_connect(self, src: str, dst: str):
        proc = await asyncio.create_subprocess_exec(
            "jack_connect", src, dst,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise RuntimeError(f"jack_connect {src} ? {dst} failed: {stderr.decode().strip()}")

    async def midi_connexion(self, host_midi_port: str):
        ports = await self._get_jack_ports()
        
        midi_captures = [port for port in ports if "system:midi_capture" in port]
        
        for src in midi_captures:
            if host_midi_port not in ports[src]:
                await self._jack_connect(src, host_midi_port)

    async def audio_connexion(self, host_audio_port: str):
        ports = await self._get_jack_ports()
        
        midi_captures = [port for port in ports if "system:capture" in port]
        
        for src in midi_captures:
            if host_audio_port not in ports[src]:
                await self._jack_connect(src, host_audio_port)
        
    async def stop(self):
        if self.process is None:
            return
        
        if self.process.returncode is not None:
            # Process déjà terminé ou crash
            self.process = None
            return

        self.process.terminate()

        try:
            await asyncio.wait_for(self.process.wait(), timeout=5.0)

        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()

        finally:
            self.process = None
        
        await asyncio.sleep(2)
