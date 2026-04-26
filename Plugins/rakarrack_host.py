import subprocess
import asyncio
import struct
import json
import rtmidi
import sys
import shutil

from plugin import Plugin
from jack_server import Jack

HOST_NAME = "Rakarrack"
RAKARRACK_EXE = "rakarrack-plus"

# Constantes
C_MAX_EFFECTS = 70
C_MAX_PARAMETERS = 20  # C_NUMBER_PARAMETERS (19) + 1
NUM_PRESETS = 62

PRESET_FORMAT = (
    "64s"   # Preset_Name
    "64s"   # Author
    "36s"   # Classe
    "4s"    # Type
    "128s"  # ConvoFiname
    "64s"   # cInput_Gain
    "64s"   # cMaster_Volume
    "64s"   # cBalance
    "f"     # Input_Gain
    "f"     # Master_Volume
    "f"     # Fraction_Bypass
    "i"     # FX_Master_Active
    "128s"  # RevFiname
    "128s"  # EchoFiname
    f"{C_MAX_EFFECTS * C_MAX_PARAMETERS}i"  # Effect_Params[70][20]
    f"{128 * 20}i"                          # XUserMIDI[128][20]
    "128i"  # XMIDIrangeMin
    "128i"  # XMIDIrangeMax
)

PRESET_SIZE = struct.calcsize(PRESET_FORMAT)
BANK_SIZE = PRESET_SIZE * NUM_PRESETS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANKS_PATH = "/usr/local/share/rakarrack-plus/"
BANKS_LIST = ["Default", "Extra", "Extra1"]
MIDI_PRESETS_TABLE = "Rakarrack/Settings/Preferences/User/midi_table.rmt"
MIDI_PORT_NAME = "rakarrack-plus:rakarrack-plus IN 130:0"


def get_info() -> dict:
    return {
        "name":     HOST_NAME,
        "class":    Rakarrack,
        "stream": 1,   # 0 = MIDI, 1 = AUDIO, 2 = BOTH
        "gui": False # no gui needed to use this plugin
    }

class Rakarrack(Plugin):

    def __init__(self):
        self.process = None
        self.banks = []
        self.presets = []
        self.preset_index = [0, 0]
        self.jack = Jack()
        self.midi_out = rtmidi.MidiOut()
    
    @classmethod
    def is_installed(cls) -> bool:
        return super().is_installed(RAKARRACK_EXE)
    
    @classmethod
    def install(cls, callback = None):
        return super().install(HOST_NAME, RAKARRACK_EXE, progress_callback=callback)

    async def start(self):
        await self.jack.start()
        self.process = subprocess.Popen([RAKARRACK_EXE, "--no-gui"])
        await asyncio.sleep(5)
        await self.jack.audio_connexion("rakarrack-plus:in_1")
        await self.jack.audio_connexion("rakarrack-plus:in_2")
        self.midi_port_connexion()
        print("Rakarrack is ready")

    def midi_port_connexion(self):
        available_ports = self.midi_out.get_ports()
        print("Ports MIDI disponibles :", available_ports)

        target_port = None
        for i, name in enumerate(available_ports):
            if "rakarrack" in name.lower():
                target_port = i
                break

        if target_port is not None:
            self.midi_out.open_port(target_port)
            print(f"Connecté au port : {available_ports[target_port]}")
        else:
            # Crée un port virtuel si rakarrack n'est pas trouvé
            self.midi_out.open_virtual_port(MIDI_PORT_NAME)
            print(f"Port virtuel crée : {MIDI_PORT_NAME}")

    def parse_string(self, raw: bytes) -> str:
        """Décode un tableau de chars C (null-terminated) en string Python."""
        return raw.split(b'\x00', 1)[0].decode('utf-8', errors='replace')

    def load_bank(self, filename: str):
        with open(filename, "rb") as f:
            data = f.read()

        if len(data) < BANK_SIZE:
            raise ValueError(
                f"Fichier trop petit : {len(data)} octets lus, "
                f"{BANK_SIZE} attendus."
            )

        presets = []
        seen_names = set()  # Pour détecter les doublons

        for i in range(NUM_PRESETS):
            offset = i * PRESET_SIZE
            chunk = data[offset:offset + PRESET_SIZE]
            fields = struct.unpack_from(PRESET_FORMAT, chunk)

            name = self.parse_string(fields[0])

            # Ignore les presets vides ou déjà vus
            if not name or name in seen_names:
                continue

            seen_names.add(name)

            preset = {
                "Preset_Name":     name,
                "Author":          self.parse_string(fields[1]),
                "Classe":          self.parse_string(fields[2]),
                "Type":            self.parse_string(fields[3]),
                "ConvoFiname":     self.parse_string(fields[4]),
                "cInput_Gain":     self.parse_string(fields[5]),
                "cMaster_Volume":  self.parse_string(fields[6]),
                "cBalance":        self.parse_string(fields[7]),
                "Input_Gain":      fields[8],
                "Master_Volume":   fields[9],
                "Fraction_Bypass": fields[10],
                "FX_Master_Active":fields[11],
                "RevFiname":       self.parse_string(fields[12]),
                "EchoFiname":      self.parse_string(fields[13]),
            }
            presets.append(preset)

        return sorted(presets, key=lambda p: p["Preset_Name"].lower())

    def get_midi_table_for_preset_order(self):
        bank_preset_list = []
        with open(MIDI_PRESETS_TABLE, "r") as f:
            lines = f.readlines()

        bank_preset_list = []
        for line in lines:
            bank_preset = line.strip().split(",")

            if len(bank_preset) < 2:
                bank_preset = [0, 0]
            else :
                bank_preset = [int(bank_preset[0]), int(bank_preset[1])]
            bank_preset_list.append(bank_preset)
            
        return bank_preset_list

    def get_presets(self):
        for bank in BANKS_LIST:
            self.banks.append(self.load_bank(BANKS_PATH + bank + ".rkrb"))
            self.presets.append(dict(name = bank, list = []))

        for order in self.get_midi_table_for_preset_order():
            if order[0] <= len(self.banks):
                if order[1] <= len(self.banks[order[0]]):
                    self.presets[order[0]]["list"].append(dict(name = self.banks[order[0]][order[1]]["Preset_Name"]))

        return self.presets
        
    def get_preset_info(self):
        parameters = []
        
        preset_name = self.presets[self.preset_index[0]]["list"][self.preset_index[1]]["name"]
    
        plugins_info = [dict(
            name=preset_name,
            id=0,
            param_count=len(parameters),
            parameters=parameters,
        )]
 
        return dict(
            name=preset_name,
            plugin_count=1,
            plugins=plugins_info,)

    async def load_preset(self, index):
        channel = 0
        preset_midi_num = (index[0] * len(self.presets[index[0]]["list"])) + index[1]
        program_change = [0xC0 | (channel & 0x0F), preset_midi_num & 0x7F]
        self.midi_out.send_message(program_change)
        
        self.preset_index = index

    def set_parameter(self, json_data):
        print("under development")
        #self.rpc("setParameters", params = [{ "list" : {"index":json_data["parameterId"],"normalized_value":json_data["value"]} }])

    async def close(self):
        if (self.process is not None):
            self.process.terminate()
            self.process.wait()
            del self.midi_out

        await self.jack.stop()

        print("Rakarrack is closed")
