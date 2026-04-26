import subprocess
import time
import pyautogui
import asyncio
import json
import os

HOST_NAME = "AnalogLab"
ANALOG_EXE = r"C:\Program Files\Arturia\Analog Lab 4\Analog Lab 4.exe"
ANALOG_PRESET_LIST = "/home/theo-rasp/Projects/VST_Host/analog_collection.json"

def get_info() -> dict:
    return {
        "name":     HOST_NAME,
        "class":    AnalogLab,
        "stream": 0   # 0 = MIDI, 1 = AUDIO, 2 = BOTH
    }

class AnalogLab:

    def __init__(self):
        presets = None
        with open(ANALOG_PRESET_LIST, 'r', encoding='utf-8') as fichier:
            presets = json.load(fichier)
        
        self.process = None
        self.presets = presets
        self.preset_index = 0
        
    @classmethod
    def is_plugin_installed(cls) -> bool:
        return os.path.exists(ANALOG_EXE)

    def get_presets(self):
        return [dict(name = p["name"]) for p in self.presets]
    
    def get_preset_info(self):
        return self.presets[self.preset_index]

    async def start(self):
        self.process = subprocess.Popen(["wine", ANALOG_EXE])
        await asyncio.sleep(40)
        print("Analog Lab 4 is ready")

    async def load_preset(self, index):
        preset = self.presets[index[0]]["name"]
        with pyautogui.hold('ctrl'):
            pyautogui.press('f')
        time.sleep(1)
        pyautogui.write(preset)
        time.sleep(1)
        pyautogui.press('enter')
        self.preset_index = index[0]

    def set_parameter(self, parameter):
        print("currently under development")

    async def close(self):
        self.process.terminate()
        self.process.wait()
        time.sleep(10)
        print("Analog Lab 4 is closed")

    def test(self):
        self.start()
        self.loadPreset('American Jazz')
        time.sleep(5)
        self.loadPreset('Fascination')
        time.sleep(5)
        self.loadPreset('Ion Storm')
        time.sleep(5)
        self.close()




