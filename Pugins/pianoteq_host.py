import subprocess
import asyncio
import requests
import os

from plugin import Modartt
from jack_server import Jack

HOST_NAME = "Pianoteq"
PIANOTEQ_EXE = "pianoteq"

remote_server = '127.0.0.1:8081'

def get_info() -> dict:
    return {
        "name":     HOST_NAME,
        "class":    Pianoteq,
        "stream": 0   # 0 = MIDI, 1 = AUDIO, 2 = BOTH
        "gui": False # no gui needed to use this plugin
    }

class Pianoteq(Modartt):

    def __init__(self):  
        self.process = None
        self.presets = []
        self.preset_index = 0
        self.jack = Jack()
        
    @classmethod
    def is_installed(cls) -> bool:
        return super().is_installed(PIANOTEQ_EXE)
    
    @classmethod
    def install(cls, callback = None):
        return super().install(HOST_NAME, PIANOTEQ_EXE, progress_callback=callback)

    async def start(self):
        await self.jack.start()
        self.process = subprocess.Popen([PIANOTEQ_EXE, "--headless", "--serve", remote_server])
        await asyncio.sleep(5)
        await self.jack.midi_connexion("Pianoteq:midi_in")
        print("Pianoteq 9 is ready")

    def rpc(self, method, params=None, id=0):
        if params is None:
            params=[]
        url = f'http://{remote_server}/jsonrpc'
        payload = {
            "method": method,
            "params": params,
            "jsonrpc": "2.0",
            "id": id}

        try:
            result=requests.post(url, json=payload)
        except requests.exceptions.ConnectionError:
            print('Connection error..')
            return None

        return result.json()

    def get_presets(self):
        presets = self.rpc("getListOfPresets")
        if presets is not None:
            presets = self.rpc("getListOfPresets")["result"]
            self.presets = [p["name"] for p in presets]
        return [dict(name = preset) for preset in self.presets]
        
    def get_preset_info(self):
        gross_parameters = self.rpc("getParameters")
        if gross_parameters is not None:
            gross_parameters = gross_parameters["result"]
        else:
            gross_parameters = []
    
        parameters = []

        for gross_param in gross_parameters:
            parameters.append(dict(name = gross_param['name'],
                                    id = gross_param['index'],
                                    unit = gross_param['unit'],
                                    value = gross_param['normalized_value'],
                                    min = 0.0,
                                    max = 1.0))

        plugins_info = [dict(name = self.presets[self.preset_index], id = 0, param_count = len(parameters), parameters = parameters)]

        preset_info = dict(name = self.presets[self.preset_index], plugin_count = 1, plugins = plugins_info)
        return preset_info

    async def load_preset(self, index):
        preset = self.presets[index[0]]
        self.rpc("loadPreset", params=[preset])
        self.preset_index = index[0]

    def set_parameter(self, json_data):
        self.rpc("setParameters", params = [{ "list" : {"index":json_data["parameterId"],"normalized_value":json_data["value"]} }])

    async def close(self):
        if (self.process is not None):
            self.process.terminate()
            self.process.wait()

        await self.jack.stop()

        print("Pianoteq 9 is closed")



