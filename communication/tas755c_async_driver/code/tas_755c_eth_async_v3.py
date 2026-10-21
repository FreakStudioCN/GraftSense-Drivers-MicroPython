from tas_755c_eth_async_v2 import TAS_755C_ETHAsyncV2
class TAS_755C_ETHAsyncV3(TAS_755C_ETHAsyncV2):
    async def enter_command_mode_async(self): return await super().enter_command_mode_async()
    async def enter_data_mode_async(self): return await super().enter_data_mode_async()
    async def set_ip_config_async(self, mode, ip, gateway, subnet, dns): return await super().set_ip_config_async(mode, ip, gateway, subnet, dns)
    async def get_ip_config_async(self): return await super().get_ip_config_async()
    async def set_tcp_config_async(self, local_port, remote_port, mode, remote_address): return await super().set_tcp_config_async(local_port, remote_port, mode, remote_address)
    async def get_tcp_config_async(self): return await super().get_tcp_config_async()
    async def set_http_config_async(self, net_status, method, header_return): return await super().set_http_config_async(net_status, method, header_return)
    async def save_async(self): return await super().save_async()
    async def restart_async(self): return await super().restart_async()
    async def send_data_async(self, data): return await super().send_data_async(data)
    async def read_data_async(self, timeout_ms=3000): return await super().read_data_async(timeout_ms)
    async def has_data_async(self): return await super().has_data_async()
