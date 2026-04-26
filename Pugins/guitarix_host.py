import subprocess
import asyncio
import requests
import os

from plugin import Plugin
from jack_server import Jack

HOST_NAME = "Guitarix"
GUITARIX_EXE = "/usr/bin/guitarix"

GUITARIX_HOST = "127.0.0.1"
GUITARIX_PORT = 7000  # port JSON-RPC par défaut de Guitarix


def get_info() -> dict:
    return {
        "name":     HOST_NAME,
        "class":    Guitarix,
        "stream": 1   # 0 = MIDI, 1 = AUDIO, 2 = BOTH
        "gui": False # no gui needed to use this plugin
    }
 
class Guitarix(Plugin):
    def __init__(self):
        self.process = None
        self.presets = []
        self.preset_index = 0
        self.jack = Jack()
 
    # ------------------------------------------------------------------
    # Démarrage
    # ------------------------------------------------------------------
    
    @classmethod
    def is_installed(cls) -> bool:
        return super().is_installed(GUITARIX_EXE)
 
    async def start(self):
        await self.jack.start()
 
        self.process = subprocess.Popen([
            GUITARIX_EXE,
            "--nogui",
            "--rpcport", str(GUITARIX_PORT),
        ])
 
        await asyncio.sleep(3)
        print("Guitarix is ready")

    @classmethod
    def install(cls, callback = None):
        return super().install(HOST_NAME, GUITARIX_EXE, progress_callback=callback)
 
    # ------------------------------------------------------------------
    # JSON-RPC
    # ------------------------------------------------------------------
 
    def rpc(self, method: str, params=None, id=0):
        if params is None:
            params = []
        url = f"http://{GUITARIX_HOST}:{GUITARIX_PORT}/jsonrpc"
        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": id,
        }
        try:
            result = requests.post(url, json=payload)
        except requests.exceptions.ConnectionError:
            print("Connection error..")
            return None
        return result.json()
 
    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------
 
    def get_presets(self) -> list[str]:
        response = self.rpc("banks")
        if response is None:
            return self.presets
 
        presets = []
        for bank in response.get("result", []):
            bank_name = bank.get("name", "")
            for preset in bank.get("presets", []):
                presets.append(f"{bank_name}/{preset}")
 
        self.presets = presets
        return [dict(name = preset) for preset in self.presets]
 
    def get_preset_info(self) -> dict:
        response = self.rpc("get_parameters", params=[[]])  # liste vide = tous les paramètres
        if response is not None:
            raw_params = response.get("result", {})
        else:
            raw_params = {}
 
        parameters = []
        for osc_id, param in raw_params.items():
            parameters.append(dict(
                name=param.get("name", osc_id),
                id=osc_id,
                unit=param.get("unit", ""),
                value=param.get("value", 0.0),
                min=param.get("lower", 0.0),
                max=param.get("upper", 1.0),
            ))
 
        preset_name = self.presets[self.preset_index] if self.presets else "default"
 
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
 
        preset = self.presets[index[0]]
        bank, name = preset.split("/", 1)
        self.rpc("setpreset", params=[bank, name])
        self.preset_index = index[0]
        print(f"Loaded preset: {preset}")
 
    # ------------------------------------------------------------------
    # Paramètres
    # ------------------------------------------------------------------
 
    def set_parameter(self, json_data: dict):
        param_id = json_data["parameterId"]
        value = float(json_data["value"])
        self.rpc("set_parameter", params=[{param_id: value}])
 
    # ------------------------------------------------------------------
    # Fermeture
    # ------------------------------------------------------------------
 
    async def close(self):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()

        await self.jack.stop()

        print("Guitarix is closed")
