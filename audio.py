import sounddevice as sd
import re
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTING_LIST_PATH = os.path.join(BASE_DIR,"settings.json")

class Audio:

    @classmethod
    def getDevice(cls, kind:str):
        if kind != "input" and kind != "output":
            return None
                
        devices = cls.deviceList(kind)

        with open(SETTING_LIST_PATH, 'r', encoding='utf-8') as fichier:
            setting_list = json.load(fichier)

        if len(devices) == 0:
            return None

        if kind == "input":
            index = 0
        else:
            index = 1

        selected = setting_list[0]["list"][index]["selected"]
        if selected not in (device["name"] for device in devices):
            selected = devices[0]["name"]

        return next((device for device in devices if device["name"] == selected), None)

    @classmethod
    def deviceList(cls, kind:str):
        try:
            sd._terminate()
            sd._initialize()
            devices = sd.query_devices(kind=kind)

            if isinstance(devices, tuple) == False:
                devices = (devices,)
            else:
                if not devices:
                    return []
            
            device_list = []

            for device in devices:
                match = re.search(r'hw:(\d+)', device["name"])
                if match:
                    hw = match.group(1)
                name = device["name"].split("(")[0].split(':')[0].strip()
                device_list.append(dict(name = name,
                                        index = device["index"],
                                        hw = int(hw),
                                        max_input_channels = device["max_input_channels"],
                                        max_output_channels = device["max_output_channels"],
                                        samplerate = device["default_samplerate"]))
                
            return device_list

        except:
            print("No audio devices found.")
            return []
