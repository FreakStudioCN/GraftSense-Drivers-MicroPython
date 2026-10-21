try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
import ubinascii
from _gs_atecc608a_packet import ATCAPacket
import _gs_atecc608a_constant as ATCA
import _gs_atecc608a_exceptions as ATCA_EXCEPTIONS

class ATECC608AAsync:
    def __init__(self, bus, address=0x60, retries=20, debug=False):
        if not hasattr(bus, "readfrom_into") or not hasattr(bus, "writeto"):
            raise ValueError("bus must provide I2C readfrom_into and writeto")
        self._bus, self._address, self._retries = bus, address, retries
        self._lock, self._device = asyncio.Lock(), None

    async def _execute_async(self, packet, timeout_ms):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        retries = self._retries
        while retries:
            try:
                # Source wake -> tWHI/tWLO -> command order.  One millisecond
                # is a cooperative, safe over-approximation of the 150 us minimum.
                self._bus.writeto(self._address, b"\x00\x00")
                await asyncio.sleep_ms(1)
                if isinstance(self._device, str):
                    packet.device = self._device
                self._bus.writeto(self._address, b"\x03" + packet.to_buffer())

                response = packet.response_data_mv
                poll_deadline = time.ticks_add(time.ticks_ms(), min(packet.delay, 250))
                while time.ticks_diff(poll_deadline, time.ticks_ms()) >= 0:
                    try:
                        self._bus.readfrom_into(self._address, response[0:1])
                        self._bus.readfrom_into(self._address, response[1:response[0]])
                    except OSError:
                        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                            raise ATCA_EXCEPTIONS.GenericError("command timeout")
                        await asyncio.sleep_ms(2)
                    else:
                        break

                status, exception_type = self._decode_response_status(response)
                if status == 0x00:
                    packet._response_data = response[:response[0]]
                    return packet
                if status == 0x11:
                    return packet
                if status == 0xEE:
                    self._bus.writeto(self._address, b"\x01")
                elif exception_type is not None:
                    packet._response_data = response[:response[0]]
                    raise exception_type(ubinascii.hexlify(packet._response_data))
            except OSError:
                retries -= 1
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                break
        raise ATCA_EXCEPTIONS.GenericError("max retry")

    @staticmethod
    def _decode_response_status(response):
        if response[ATCA.ATCA_COUNT_IDX] != 4:
            return 0x00, None
        return {
            0x00: (0x00, None),
            0x01: (0xD1, ATCA_EXCEPTIONS.CheckmacVerifyFailedError),
            0x03: (0xD2, ATCA_EXCEPTIONS.ParseError),
            0x05: (0xD6, ATCA_EXCEPTIONS.EccFaultError),
            0x07: (0xD7, ATCA_EXCEPTIONS.SelfTestError),
            0x08: (0xFA, ATCA_EXCEPTIONS.HealthTestError),
            0x0F: (0xF4, ATCA_EXCEPTIONS.ExecutionError),
            0x11: (0x11, None),
            0xEE: (0xEE, ATCA_EXCEPTIONS.WatchDogAboutToExpireError),
            0xFF: (0xD4, ATCA_EXCEPTIONS.CrcError),
        }.get(response[ATCA.ATCA_RSP_DATA_IDX], (0xE1, ATCA_EXCEPTIONS.GenericError))

    async def atcab_info_async(self, timeout_ms=1000):
        async with self._lock:
            return await self._execute_async(ATCAPacket(opcode=ATCA.ATCA_INFO, param1=ATCA.INFO_MODE_REVISION), timeout_ms)

    async def start_async(self, timeout_ms=1000):
        if hasattr(self._bus, "scan") and self._address not in self._bus.scan():
            raise RuntimeError("ATECC608A address not found")
        packet = await self.atcab_info_async(timeout_ms)
        self._device = "ATECC608A" if packet.response_data[3] == 0x60 else "ATECC508A"
        return self._device

    async def atcab_read_serial_number_async(self, timeout_ms=1000):
        async with self._lock:
            packet = ATCAPacket(opcode=ATCA.ATCA_READ, param1=ATCA.ATCA_ZONE_CONFIG | ATCA.ATCA_ZONE_READWRITE_32, param2=0)
            return await self._execute_async(packet, timeout_ms)

    async def atcab_is_locked_async(self, zone, timeout_ms=1000):
        async with self._lock:
            packet = ATCAPacket(opcode=ATCA.ATCA_READ, param1=ATCA.ATCA_ZONE_CONFIG, param2=(2 << 3) | 5)
            packet = await self._execute_async(packet, timeout_ms)
            return packet[4] != 0x55 if zone == "config" else packet[3] != 0x55

    async def atcab_random_async(self, timeout_ms=1000):
        async with self._lock:
            return await self._execute_async(ATCAPacket(opcode=ATCA.ATCA_RANDOM, param1=ATCA.RANDOM_SEED_UPDATE), timeout_ms)

    async def atcab_sha_async(self, data, timeout_ms=1000):
        async with self._lock:
            packet = ATCAPacket(opcode=ATCA.ATCA_SHA, param1=ATCA.SHA_MODE_SHA256_START)
            await self._execute_async(packet, timeout_ms)
            packet = ATCAPacket(opcode=ATCA.ATCA_SHA, param1=ATCA.SHA_MODE_SHA256_END, param2=len(data), request_data=data)
            return await self._execute_async(packet, timeout_ms)

    async def atcab_read_config_zone_async(self, timeout_ms=1000):
        # Match basic.atcab_read_config_zone(): four ordered block packets.
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        packets = []
        async with self._lock:
            for block in range(ATCA.ATCA_ECC_CONFIG_SIZE // ATCA.ATCA_BLOCK_SIZE):
                remaining = time.ticks_diff(deadline, time.ticks_ms())
                if remaining <= 0:
                    raise ATCA_EXCEPTIONS.GenericError("command timeout")
                packet = ATCAPacket(
                    opcode=ATCA.ATCA_READ,
                    param1=ATCA.ATCA_ZONE_CONFIG | ATCA.ATCA_ZONE_READWRITE_32,
                    param2=block << 3)
                packets.append(await self._execute_async(packet, remaining))
        return packets

    def atcab_version(self):
        return "1.1.1"

    async def aclose(self):
        try:
            self._bus.writeto(self._address, b"\x01")
        except OSError:
            pass
        self._bus = None
