from tas_755c_eth_async import TAS_755C_ETHAsync

class TAS_755C_ETHAsyncV2(TAS_755C_ETHAsync):
    async def has_data_async(self):
        async with self._lock:
            return self._uart.any()
