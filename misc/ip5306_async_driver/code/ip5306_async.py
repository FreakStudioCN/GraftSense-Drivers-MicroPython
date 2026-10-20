from _gs_ip5306_ip5306 import *

class IP5306Async(IP5306):
    async def level_async(self):
        return self.level

    async def deinit_async(self):
        return super().deinit()

    async def aclose(self):
        await self.deinit_async()
