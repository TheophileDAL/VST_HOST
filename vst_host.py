import asyncio
import importlib.util
import os
import argparse

from vocal_command import VocalCommand
from ble_command import BleCommand

parser = argparse.ArgumentParser()
parser.add_argument("--vc", help="enable vocal commands", action="store_true")
args = parser.parse_args()

if args.vc:
    enable_vc = True
else:
    enable_vc = False

host_list = []
host_list.append(dict(name = "Midi", list = []))
host_list.append(dict(name = "Audio", list = []))

host_classes = []
host_classes.append(dict(name = "Midi", list = []))
host_classes.append(dict(name = "Audio", list = []))

PLUGINS_DIR = "/home/theo-rasp/Projects/VST_Host/Pugins"

for filename in os.listdir(PLUGINS_DIR):
    if not filename.endswith(".py"):
        continue

    filepath = os.path.join(PLUGINS_DIR, filename)
    module_name = filename[:-3]  # Retire le .py

    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "get_info"):
        print(f"[WARN] {filename} n'a pas de get_info(), ignoré.")
        continue
    
    info = module.get_info()
    if (info["gui"] == False or os.environ.get('DISPLAY') is not None):
        host_list[info["stream"]]["list"].append(dict(name=info["name"]))
        host_classes[info["stream"]]["list"].append(info["class"])


async def main():

    server = None
    preset_index = 0
    preset_info = None
    host = None

    commands = asyncio.Queue()
    
    if enable_vc == True:
        vocal = VocalCommand(commands_queue=commands)
        vocal_task = asyncio.create_task(vocal.listen())

    ble_command = BleCommand(commands_queue=commands)
    await ble_command.configure()
    await ble_command.start()
    
    try:
        while True:
            command = await commands.get()
            if command["name"] == "load setup":
                if host is not None:
                    await host.close()
                    host_list[actual_stream]["list"][actual_host]["list"] = []
                    host = None
                
                await asyncio.sleep(3)
                await ble_command.task("set presets list", host_list)

            elif command["name"] == "load host":
                if host is not None:
                    await host.close()
                    host_list[actual_stream]["list"][actual_host]["list"] = []
                    host = None
                
                host_class = host_classes[command["stream"]]["list"][command["host"]]
                
                if host_class.is_installed():
                    host = host_class()
                    await host.start()

                    preset_list = host.get_presets()
                    host_list[command["stream"]]["list"][command["host"]]["list"] = preset_list
                    await ble_command.task("set presets list", host_list)

                    actual_stream = command["stream"]
                    actual_host = command["host"]
                else:
                    print(host_list[command["stream"]]["list"][command["host"]]["name"] + " is not installed")
                    await ble_command.task("set presets list", host_list)
                    
            elif command["name"] == "load preset":
                preset_index = command["preset"]
                print("NEW COMMAND : LOAD PRESET ", preset_index)                        
                await host.load_preset(preset_index)
                presets_info = host.get_preset_info()
                await ble_command.task("set preset info", presets_info)

            elif command["name"] == "set parameter":
                host.set_parameter(command["parameter"])
                
            elif command["name"] == "install host":
                host_class = host_classes[command["stream"]]["list"][command["host"]]
                success = host_class.install(print)
                
                if (success):
                    host = host_class()
                    await host.start()

                    preset_list = host.get_presets()
                    host_list[command["stream"]]["list"][command["host"]]["list"] = preset_list
                    await ble_command.task("set presets list", host_list)

                    actual_stream = command["stream"]
                    actual_host = command["host"]

            elif command["name"] == "vocal":
                text = command["command"]
                if text == "joue":
                    await ble_command.start()

                    await ble_command.task("set presets list", host_list)

                    host = Carla()
                    previous_host = 0
                    await host.start()

                    presets_list = host.get_presets()
                    host_list[0]["list"] = presets_list
                    await ble_command.task("set presets list", host_list)
                    
                    preset_index = 0
                    await host.load_preset(preset_index)

                    await ble_command.task("set selected preset", preset_index)

                    preset_info = host.get_preset_info()
                    await ble_command.task("set preset info", preset_info)
                                        
                elif text == "suivant" or text == "suite" or text == "suivre":
                    if host is not None:
                        if len(presets_list) != 0:
                            preset_index = preset_index + 1
                            if (preset_index > len(presets_list) - 1):
                                preset_index = 0
                            await host.load_preset(preset_index)
                            
                            await ble_command.task("set selected preset", preset_index)
                            
                            preset_info = host.get_preset_info()
                            await ble_command.task("set preset info", preset_info)

                elif text == "précédent":
                    if host is not None:
                        if len(presets_list) != 0:
                            preset_index = preset_index - 1
                            if (preset_index < 0):
                                preset_index = len(host.presets) - 1
                            await host.load_preset(preset_index)

                            await ble_command.task("set selected preset", preset_index)
                            
                            preset_info = host.get_preset_info()
                            await ble_command.task("set preset info", preset_info)

                elif text == "stop" or text == "stop tout" or text == "tout" or text == "c'est tout" or text == "top" or text == "top tout":
                    if (host is not None):
                        await host.close()
                        host_list[actual_stream]["list"][actual_host]["list"] = []
                        host = None

                    await ble_command.stop()
                    
                    if (text != "stop"):
                        break

    finally:
        if enable_vc == True:
            vocal_task.cancel()
            await asyncio.gather(vocal_task, return_exceptions=True)

asyncio.run(main())
