import sounddevice as sd
import re

class Audio:

    def __init__(self):
        self.selected_output = None

    def setSelectedOutput(self, name : str):
        self.selected_output = name

    def getOutputDevice(self):
        devices = self.outputDeviceList()

        if len(devices) > 0 and self.selected_output == None:
            self.selected_output = devices[0]["name"]

        return next((device for device in devices if device["name"] == self.selected_output), None)

    def outputDeviceList(self):
        try:
            sd._terminate()
            sd._initialize()
            devices = sd.query_devices(kind="output")

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
