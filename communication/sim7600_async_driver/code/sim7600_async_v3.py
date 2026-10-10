from sim7600_async_v2 import SIM7600AsyncV2

class SIM7600AsyncV3(SIM7600AsyncV2):
    async def check_sim_card_async(self): return await self.command_async("AT+CPIN?")
    async def get_signal_quality_async(self): return await self.command_async("AT+CSQ")
    async def check_network_registration_async(self): return await self.command_async("AT+CEREG?")
    async def check_network_attach_async(self): return await self.command_async("AT+CGATT?")
