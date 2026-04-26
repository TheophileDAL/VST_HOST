import asyncio
import json
from bless import BlessServer, GATTCharacteristicProperties, GATTAttributePermissions

#BLE SERVER
service_uuid = "d98c8810-876b-4516-988c-28c7384a33cc"
presets_uuid = "d98c8811-876b-4516-988c-28c7384a33cc"
selected_preset_uuid = "d98c8812-876b-4516-988c-28c7384a33cc"
preset_info_uuid = "d98c8813-876b-4516-988c-28c7384a33cc"
change_param_uuid = "d98c8814-876b-4516-988c-28c7384a33cc"

class BleCommand:
    def __init__(self, commands_queue: asyncio.Queue):
        self.commands_queue = commands_queue
        self.server = BlessServer(name="VST HOST")
    
    async def configure(self):
        await self.server.add_new_service(service_uuid)

        await self.server.add_new_characteristic(
            service_uuid,
            presets_uuid,
            GATTCharacteristicProperties.read | 
            GATTCharacteristicProperties.notify,
            b"",
            GATTAttributePermissions.readable
        )

        await self.server.add_new_characteristic(
            service_uuid,
            selected_preset_uuid,
            GATTCharacteristicProperties.read | 
            GATTCharacteristicProperties.write |
            GATTCharacteristicProperties.notify,
            b"",
            GATTAttributePermissions.readable | GATTAttributePermissions.writeable
        )

        await self.server.add_new_characteristic(
            service_uuid,
            preset_info_uuid,
            GATTCharacteristicProperties.read | 
            GATTCharacteristicProperties.notify,
            b"",
            GATTAttributePermissions.readable
        )

        await self.server.add_new_characteristic(
            service_uuid,
            change_param_uuid,
            GATTCharacteristicProperties.read | 
            GATTCharacteristicProperties.write |
            GATTCharacteristicProperties.notify,
            b"",
            GATTAttributePermissions.readable | GATTAttributePermissions.writeable
        )

        self.server.write_request_func = self.write_request
        self.server_started = False

    async def start(self):
        if self.server_started == False:
            await self.server.start()
            self.server_started = True
            print("[BleCommand] Server started")

    async def stop(self):
        if self.server_started == True:
            await self.server.stop()
            self.server_started = False

        print("[BleCommand] Server stopped")

    async def task(self, name: str, data):
        if name == "set presets list":
            message = json.dumps(data).encode('utf-8')
            await self.send_big_ble(message, presets_uuid)
        elif name == "set preset info":
            message = json.dumps(data).encode('utf-8')
            await self.send_big_ble(message, preset_info_uuid)
        elif name == "set selected preset":
            message = str(data).encode('utf-8')
            self.server.get_characteristic(selected_preset_uuid).value = message
            self.server.update_value(service_uuid, selected_preset_uuid)

    def write_request(self, characteristic, value, **kwargs):
        message = value.decode('utf-8')
        print("[BleCommand] Received message : ",  message)
        if self.server.get_characteristic(selected_preset_uuid) == characteristic:
            self.commands_queue.put_nowait(json.loads(message))
        elif self.server.get_characteristic(change_param_uuid) == characteristic:
            self.commands_queue.put_nowait(dict(name = "set parameter", parameter = json.loads(message)))

    async def send_big_ble(self, data, uuid):
        CHUNK_SIZE = 200

        for i in range(0, len(data), CHUNK_SIZE):
            chunk = data[i:i+CHUNK_SIZE]
            self.server.get_characteristic(uuid).value = chunk
            self.server.update_value(service_uuid, uuid)
            await asyncio.sleep(0.05)

        self.server.get_characteristic(uuid).value = "end of transmission".encode("utf-8")
        self.server.update_value(service_uuid, uuid)