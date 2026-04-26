import subprocess
import time
import sys
import os
import asyncio

from jack_server import Jack
from plugin import Plugin

HOST_NAME = "Carla"
CARLA_RESSOURCES = "/usr/share/carla/resources"

def get_info() -> dict:
    return {
        "name":     HOST_NAME,
        "class":    Carla,
        "stream": 0   # 0 = MIDI, 1 = AUDIO, 2 = BOTH
    }

class Carla(Plugin):

    def __init__(self):
        sys.path.append(CARLA_RESSOURCES)
        import carla_backend
        self.backend = carla_backend
        self.presets_path = "/home/theo-rasp/Music/PRESETS/"
        presets = os.listdir(self.presets_path)
        self.presets = [preset.removesuffix(".carxp") for preset in presets]
        self.process = None
        self.preset_index = 0
        self.jack = Jack()
        
    @classmethod
    def is_installed(cls) -> bool:
        return super().is_installed(CARLA_RESSOURCES + "/carla_backend.py")
    
    @classmethod
    def install(cls, callback = None):
        return super().install(HOST_NAME, CARLA_RESSOURCES + "/carla_backend.py", progress_callback=callback)

    async def start(self):
        await self.jack.start()
        self.process = self.backend.CarlaHostDLL("/lib/carla/libcarla_standalone2.so", True)
        await asyncio.sleep(2)
        self.process.engine_init("JACK", "carla-python")

    def get_presets(self):
        return [dict(name = preset) for preset in self.presets]
    
    def get_preset_info(self):
        plugins_info = []
        plugin_count = 0
        
        if self.process is not None:

            plugin_count = self.process.get_current_plugin_count()

            for plugin_id in range(plugin_count):
                name = self.process.get_plugin_info(plugin_id)['name']
                param_count = self.process.get_parameter_count(plugin_id)

                plugin_param = []

                for param_id in range(param_count):
                    info = self.process.get_parameter_info(plugin_id, param_id)
                    data = self.process.get_parameter_ranges(plugin_id, param_id)
                    value = self.process.get_current_parameter_value(plugin_id, param_id)

                    plugin_param.append(dict(name = info['name'],
                                            id = param_id,
                                            unit =  info['unit'],
                                            value = value,
                                            min = data['min'],
                                            max = data['max']))

                plugins_info.append(dict(name = name, id = plugin_id, param_count = param_count, parameters = plugin_param))

        preset_info = dict(name = self.presets[self.preset_index], plugin_count = plugin_count, plugins = plugins_info)
        return preset_info

    async def load_preset(self, index):
        if self.process.get_current_plugin_count() != 0:
            self.process.remove_all_plugins()
            self.process.engine_close()
            await asyncio.sleep(1)
            self.process.engine_init("JACK", "carla-python")
            await asyncio.sleep(1)
            
        self.process.load_project(self.presets_path + self.presets[index[0]] + ".carxp")
        await asyncio.sleep(1)
        self.preset_index = index[0]

    def set_parameter(self, json_data):
        self.process.set_parameter_value(json_data["pluginId"], json_data["parameterId"], json_data["value"])

    async def close(self):
        if self.process is not None:
            if self.process.is_engine_running():
                self.process.engine_close()
                time.sleep(2)

        await self.jack.stop()

        print("Carla process terminated")
