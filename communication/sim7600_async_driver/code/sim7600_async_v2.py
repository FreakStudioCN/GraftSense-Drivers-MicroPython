from sim7600_async import SIM7600Async, CallingAsync, SMSAsync, GPSAsync, LBSAsync, HTTPAsync


class SIM7600AsyncV2(SIM7600Async):
    async def send_command_async(self, command, timeout_ms=3000):
        return await self.command_async(command, timeout_ms)
