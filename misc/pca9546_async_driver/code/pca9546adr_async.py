from pca9546adr import *

class PCA9546ADRAsync(PCA9546ADR):
    async def write_ctl_async(self, ctl_byte):
        return super().write_ctl(ctl_byte)

    async def select_channel_async(self, ch):
        return super().select_channel(ch)

    async def disable_all_async(self):
        return super().disable_all()

    async def read_status_async(self):
        return super().read_status()

    async def current_mask_async(self):
        return super().current_mask()

    async def aclose(self):
        await self.disable_all_async()
