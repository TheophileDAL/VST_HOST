import subprocess
import asyncio
import glob
import os

from plugin import Plugin
from jack_server import Jack
 
from pythonosc import udp_client, dispatcher, osc_server
from pythonosc.osc_message_builder import OscMessageBuilder

HOST_NAME = "ZynAddSubFx"
ZYNC_EXE = "/usr/bin/zynaddsubfx"
ZYNC_PRESETS_DIR = "/usr/share/zynaddsubfx/banks"

ZYNC_OSC_PORT = 17961       # port OSC d'entrée de ZynAddSubFX
ZYNC_OSC_HOST = "127.0.0.1"
LOCAL_OSC_PORT = 17962       # port local pour recevoir les réponses

def get_info() -> dict:
    return {
        "name":     HOST_NAME,
        "class":    ZynAddSubFx,
        "stream": 0,   # 0 = MIDI, 1 = AUDIO, 2 = BOTH
        "gui": False # no gui needed to use this plugin
    }

class ZynAddSubFx(Plugin):

    def __init__(self):
        # Répertoires standards de presets (.xiz = instrument, .xmz = master)
        self.presets_dir = ZYNC_PRESETS_DIR
 
        self.process: asyncio.subprocess.Process | None = None
        self.presets = []
        self.preset_index = [0, 0]
        self.jack = Jack()
 
        # Client OSC pour envoyer des messages ZynAddSubFX
        self.osc_client = udp_client.SimpleUDPClient(ZYNC_OSC_HOST, ZYNC_OSC_PORT)
 
        # Etat interne des paramètres (clé = chemin OSC, valeur normalisée 0.0-1.0)
        self._parameters: dict[str, float] = {}
 
        # Serveur OSC pour recevoir les réponses (optionnel)
        self._osc_server = None
        self._osc_thread = None
        
    @classmethod
    def is_installed(cls) -> bool:
        return super().is_installed(ZYNC_EXE)
    
    @classmethod
    def install(cls, callback = None):
        return super().install(HOST_NAME, ZYNC_EXE, progress_callback=callback)

    async def start(self):
        await self.jack.start()

        self.process = await asyncio.create_subprocess_exec(
            ZYNC_EXE,
            "--no-gui",
            "--auto-connect",
            "--preferred-port", str(ZYNC_OSC_PORT),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
 
        await asyncio.sleep(3)
 
        await self.jack.midi_connexion("zynaddsubfx:midi_input")
        print("ZynAddSubFX is ready")
  
    def _send_osc(self, address: str, *args):
        """Envoie un message OSC à ZynAddSubFX."""
        try:
            self.osc_client.send_message(address, list(args) if args else [])
        except Exception as e:
            print(f"OSC send error ({address}): {e}")

    def get_presets(self) -> list[str]:
        self.presets = []
        banks = os.listdir(self.presets_dir)

        for bank in banks:
            directory = self.presets_dir + "/" + bank
            preset_found = glob.glob(os.path.join(directory, "**", "*.xiz"), recursive=True)
    
            if (preset_found.count != 0):
                preset_found.sort(key=os.path.basename)
                bank_preset = dict(name = bank, list = [dict(name = os.path.basename(p).removesuffix(".xiz")) for p in preset_found])
                self.presets.append(bank_preset)
        
        return self.presets
        
        
 
    def get_preset_info(self) -> dict:
        parameters = []
        for osc_path, norm_value in self._parameters.items():
            parameters.append(dict(
                name=osc_path,
                id=osc_path,
                unit="",
                value=norm_value,
                min=0.0,
                max=1.0,
            ))
 
        preset_name = (
            self.presets[self.preset_index[0]]["list"][self.preset_index[1]]["name"]
            if self.presets else "default"
        )
 
        plugins_info = [dict(
            name=preset_name,
            id=0,
            param_count=len(parameters),
            parameters=parameters,
        )]
 
        return dict(
            name=preset_name,
            plugin_count=1,
            plugins=plugins_info,
        )
 
    async def load_preset(self, index: int):
        if not self.presets:
            print("No presets loaded. Call get_presets() first.")
            return
 
        preset_path = os.path.join(self.presets_dir, 
                                   self.presets[index[0]]["name"],
                                   self.presets[index[0]]["list"][index[1]]["name"] + ".xiz"
                                   )
        self.preset_index = index
 
        # /load_xiz <part_number> <path>  ? format ZynAddSubFX ? 2.5
        self._send_osc("/load_xiz", 0, preset_path)
 
        # Laisser le synthé charger l'instrument
        await asyncio.sleep(0.5)
        print(f"Loaded preset: {os.path.basename(preset_path)}")
  
    def set_parameter(self, json_data: dict):
        """
        Modifie un paramètre via OSC.
 
        json_data doit contenir :
          - "parameterId" : chemin OSC complet, ex. "/part0/Pvolume"
          - "value"       : valeur normalisée entre 0.0 et 1.0
 
        ZynAddSubFX attend des valeurs entières pour la plupart de ses
        paramètres (0-127 ou 0-255) ; la conversion est faite ici.
        """
        osc_path: str = json_data["parameterId"]
        norm_value: float = float(json_data["value"])
 
        # Mise en cache de la valeur normalisée
        self._parameters[osc_path] = norm_value
 
        # ZynAddSubFX : la plupart des paramètres utilisent une plage 0-127
        raw_value = int(norm_value * 127)
        self._send_osc(osc_path, raw_value)
 
    # ------------------------------------------------------------------
    # Fermeture
    # ------------------------------------------------------------------
 
    async def close(self):
        if self.process is not None:
            self.process.kill()
            await self.process.wait()

        await self.jack.stop()

        print("ZynAddSubFX is closed")
