#JACK SERVER COMMAND FOR I/O
import asyncio
import subprocess

jack_cmd = [
    "jackd",
    "-d", "alsa",      # driver ALSA
    "-d", "hw:USB",    # carte son USB
    "-r", "48000",     # échantillonnage 48 kHz
    "-p", "1024",      # taille du buffer
    "-n", "2",         # nombre de buffers
    "-X", "raw"        # mode MIDI RAW
]

class Jack:

    def __init__(self):
        self.process: asyncio.subprocess.Process | None = None

    async def start(self):
        self.process = await asyncio.create_subprocess_exec(
            *jack_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

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

        self.process.terminate()

        try:
            await asyncio.wait_for(self.process.wait(), timeout=5.0)

        except asyncio.TimeoutError:
            self.process.kill()
            await self.process.wait()

        finally:
            self.process = None
        
        await asyncio.sleep(2)