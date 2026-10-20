"""Cooperative async adapters for SX1276 task-context operations."""

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import time
try:
    import random
except ImportError:
    import urandom as random

import struct

# ======================================== 全局变量 ============================================
IRQ_POLL_MS = 10


async def _pulse_low_async(pin, delay_ms):
    pin.value(0)
    started = time.ticks_ms()
    try:
        await asyncio.sleep_ms(delay_ms)
    finally:
        try:
            remaining = delay_ms - time.ticks_diff(time.ticks_ms(), started)
            while remaining > 0:
                try:
                    await asyncio.sleep_ms(remaining)
                except asyncio.CancelledError:
                    pass
                remaining = delay_ms - time.ticks_diff(time.ticks_ms(), started)
        finally:
            pin.value(1)

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================
class SX1276Async:
    """Cooperative SX1276 implementation with deferred IRQ processing.

    Constructor validation/storage has no I/O.  ``await initialize_async()``
    performs the source initialization sequence, and callers service a pending
    DIO edge with ``await process_irq_async()`` (or ``service_async``).
    """

    MODE = {"SLEEP": 0, "STANDBY": 1, "TX": 3, "RXCONTINUOUS": 5,
            "RXSINGLE": 6, "CAD": 7}
    PKT_TYPE_REQ, PKT_TYPE_ACK, PKT_TYPE_BRD = 0, 1, 2
    PKT_TYPE = {"REQ": PKT_TYPE_REQ, "ACK": PKT_TYPE_ACK, "BRD": PKT_TYPE_BRD}
    _REG_TABLE = {"RegFifo": 0x00, "RegOpMode": 0x01, "RegFrfMsb": 0x06,
                  "RegFrfMid": 0x07, "RegFrfLsb": 0x08, "RegPaConfig": 0x09,
                  "RegFifoAddrPtr": 0x0D, "RegFifoTxBaseAddr": 0x0E,
                  "RegFifoRxBaseAddr": 0x0F, "RegFifoRxCurrentAddr": 0x10,
                  "RegIrqFlags": 0x12, "RegRxNbBytes": 0x13,
                  "RegPktSnrValue": 0x19, "RegPktRssiValue": 0x1A,
                  "RegHopChannel": 0x1C, "RegModemConfig1": 0x1D,
                  "RegModemConfig2": 0x1E, "RegPreambleMsb": 0x20,
                  "RegPreambleLsb": 0x21, "RegPayloadLength": 0x22,
                  "RegHopPeriod": 0x24, "RegModemConfig3": 0x26,
                  "RegDioMapping1": 0x40, "RegPaDac": 0x4D}
    _IRQ_FLAGS = {"RxTimeout": 0x80, "RxDone": 0x40,
                  "PayloadCrcError": 0x20, "ValidHeader": 0x10,
                  "TxDone": 0x08, "CadDone": 0x04,
                  "FhssChangeChannel": 0x02, "CadDetected": 0x01}
    _HEADER_FMT, _HEADER_SIZE = "HHHH", 8
    _FIFO_BOTTOM, _FSTEP = 0, 32000000.0 / 524288

    def __init__(self, spi, cs_pin, rst_pin, dio0_pin, dio1_pin, src_id,
                 fhss_list, plus20dBm=False, debug=False):
        if not hasattr(spi, "write") or not hasattr(spi, "read"):
            raise ValueError("spi must provide write() and read()")
        if not isinstance(src_id, int) or not isinstance(fhss_list, list) or not fhss_list:
            raise ValueError("src_id must be int and fhss_list must be non-empty list")
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool")
        self._spi, self._cs_pin, self._rst_pin = spi, cs_pin, rst_pin
        self._dio0_pin, self._dio1_pin = dio0_pin, dio1_pin
        self.src_id, self._fhss_list, self._debug = src_id, fhss_list, debug
        self._plus20dBm = plus20dBm
        self._pkt_id = self._pkt_type = 0
        self._mode = None
        self.is_available = False
        self._irq_pending = False
        self._initialized = False
        self._send_lock = asyncio.Lock()
        self._bus_lock = asyncio.Lock()
        self._DIO_MAPPING = {"Tx": 0b01 << 6 | 0b01 << 4, "Rx": 0b00 << 6 | 0b01 << 4}

    async def spi_write_async(self, reg, data, fifo=False):
        async with self._bus_lock:
            payload = bytes([self._REG_TABLE[reg] | 0x80]) + (data if fifo else bytes([data]))
            self._cs_pin.value(0)
            try:
                self._spi.write(payload)
            except OSError as exc:
                raise RuntimeError("SPI write failed at register %s" % reg) from exc
            finally:
                self._cs_pin.value(1)

    async def spi_read_async(self, reg=None, length=None):
        async with self._bus_lock:
            self._cs_pin.value(0)
            try:
                data = self._spi.read(2, self._REG_TABLE[reg])[1] if length is None else self._spi.read(length + 1, self._REG_TABLE[reg])[1:]
            except OSError as exc:
                raise RuntimeError("SPI read failed at register %s" % reg) from exc
            finally:
                self._cs_pin.value(1)
        return data

    async def initialize_async(self):
        if self._initialized:
            return
        await _pulse_low_async(self._rst_pin, 10)
        await asyncio.sleep_ms(10)
        self._cs_pin.on()
        await self.spi_write_async("RegOpMode", self.MODE["SLEEP"] | 0x80)
        if await self.spi_read_async("RegOpMode") != (self.MODE["SLEEP"] | 0x80):
            raise RuntimeError("LoRa initialization failed")
        await self.spi_write_async("RegModemConfig1", 0b0111 << 4 | 0b001 << 1)
        await self.spi_write_async("RegModemConfig2", 0xA << 4 | 0b1 << 2)
        await self.spi_write_async("RegModemConfig3", 0b1 << 3 | 0b1 << 2)
        await self.spi_write_async("RegPreambleMsb", 0)
        await self.spi_write_async("RegPreambleLsb", 8)
        await self.spi_write_async("RegHopPeriod", 0 if len(self._fhss_list) == 1 else 20)
        await self.spi_write_async("RegPaConfig", 0b1 << 7 | 0x7 << 4)
        if self._plus20dBm:
            await self.spi_write_async("RegPaDac", 0x07)
        await self.spi_write_async("RegFifoTxBaseAddr", self._FIFO_BOTTOM)
        await self.spi_write_async("RegFifoRxBaseAddr", self._FIFO_BOTTOM)
        self._dio0_pin.irq(handler=self._irq_handler, trigger=self._dio0_pin.IRQ_RISING)
        self._dio1_pin.irq(handler=self._irq_handler, trigger=self._dio1_pin.IRQ_RISING)
        await self.set_mode_async("STANDBY")
        self._initialized = True

    async def set_freq_async(self):
        channel = (await self.spi_read_async("RegHopChannel")) & 0x3F
        freq = int(self._fhss_list[channel] / self._FSTEP)
        await self.spi_write_async("RegFrfMsb", (freq >> 16) & 0xFF)
        await self.spi_write_async("RegFrfMid", (freq >> 8) & 0xFF)
        await self.spi_write_async("RegFrfLsb", freq & 0xFF)

    async def read_fifo_async(self):
        await self.spi_write_async("RegFifoAddrPtr", await self.spi_read_async("RegFifoRxCurrentAddr"))
        packet = await self.spi_read_async("RegFifo", await self.spi_read_async("RegRxNbBytes"))
        snr = struct.unpack_from("b", bytes([await self.spi_read_async("RegPktSnrValue")]))[0] / 4
        rssi_raw = await self.spi_read_async("RegPktRssiValue")
        return packet, snr, round(-157 + rssi_raw + snr if snr < 0 else -157 + 16 / 15 * rssi_raw, 2)

    async def write_fifo_async(self, data):
        await self.spi_write_async("RegFifoAddrPtr", self._FIFO_BOTTOM)
        await self.spi_write_async("RegFifo", data, True)
        await self.spi_write_async("RegPayloadLength", len(data))

    async def set_mode_async(self, value):
        if value in ("TX", "RXCONTINUOUS"):
            await self.set_freq_async()
            await self.spi_write_async("RegDioMapping1", self._DIO_MAPPING["Tx" if value == "TX" else "Rx"])
            self.is_available = False
        elif value in ("STANDBY", "SLEEP"):
            await self.spi_write_async("RegDioMapping1", 0)
        else:
            self._log("Unknown working mode: %s" % value)
            return
        if self._mode != value:
            await self.spi_write_async("RegOpMode", self.MODE[value])
            self._mode = value

    async def _start_transmit_async(self, data):
        await self.set_mode_async("STANDBY")
        await self.write_fifo_async(data)
        await self.set_mode_async("TX")

    async def _send_packet_unlocked(self, dst_id, pkt_id, pkt_type, msg):
        """Transmit one packet while the caller owns the radio transaction."""
        self._pkt_type = pkt_type
        header = struct.pack(self._HEADER_FMT, self.src_id, dst_id, pkt_id, pkt_type)
        await self._start_transmit_async(header + msg.encode())

    async def send_async(self, dst_id=0, pkt_id=0, pkt_type=0, msg="", retry=1, timeout=9, debug=False):
        """Send without blocking the event loop while a REQ waits for its ACK.

        REQ retries are driven by monotonic deadlines and cooperative polling.  Each
        SPI/FIFO action remains a short synchronous transaction, but no REQ/ACK
        wait uses ``time.sleep`` or a busy loop. One instance-level lock serializes all
        caller transactions that touch _pkt_id, radio mode, or FIFO.
        """
        async with self._send_lock:
            if len(msg) > 240:
                raise ValueError("Message too long: %d bytes, max 240 bytes" % len(msg))
            if retry < 1:
                raise ValueError("retry must be at least 1")
            if timeout < 0:
                raise ValueError("timeout must not be negative")
    
            if pkt_type == self.PKT_TYPE["REQ"]:
                pkt_id = random.randint(1, 65535)
                self._pkt_id = pkt_id
    
            if pkt_type in (self.PKT_TYPE["ACK"], self.PKT_TYPE["BRD"]):
                await self._send_packet_unlocked(dst_id, pkt_id, pkt_type, msg)
                return
            if pkt_type != self.PKT_TYPE["REQ"]:
                self._log("Unsupported packet type")
                return
    
            timeout_ms = int(timeout * 1000)
            for _ in range(retry):
                self._pkt_id = pkt_id
                await self._send_packet_unlocked(dst_id, pkt_id, pkt_type, msg)
                deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
                while self._pkt_id != 0 and time.ticks_diff(deadline, time.ticks_ms()) > 0:
                    await self._process_irq_unlocked()
                    await asyncio.sleep_ms(IRQ_POLL_MS)
                await self._process_irq_unlocked()
                if self._pkt_id == 0:
                    return
                if debug:
                    self._log("REQ is not ACKed before timeout is triggered")
    
            if debug:
                self._log("Resend the REQ packet %d times but it is still not ACKed" % retry)

    def _irq_handler(self, pin):
        """ISR-safe edge capture: all SPI and callbacks run in task context."""
        self._irq_pending = True

    async def _process_irq_unlocked(self):
        if not self._irq_pending:
            return
        self._irq_pending = False
        flags = await self.spi_read_async("RegIrqFlags")
        await self.spi_write_async("RegIrqFlags", 0xFF)
        if flags & self._IRQ_FLAGS["TxDone"]:
            if self._pkt_type == self.PKT_TYPE["REQ"]:
                await self.set_mode_async("RXCONTINUOUS")
            else:
                self.is_available = True
            await self.after_TxDone_async(None)
        elif flags & self._IRQ_FLAGS["RxDone"]:
            packet, snr, rssi = await self.read_fifo_async()
            if flags & self._IRQ_FLAGS["PayloadCrcError"] or len(packet) < self._HEADER_SIZE:
                return
            src_id, dst_id, pkt_id, pkt_type = struct.unpack(self._HEADER_FMT, packet[:self._HEADER_SIZE])
            data = packet[self._HEADER_SIZE:]
            if pkt_type == self.PKT_TYPE["REQ"]:
                if dst_id == self.src_id:
                    await self.set_mode_async("STANDBY")
                    await self._send_packet_unlocked(src_id, pkt_id, self.PKT_TYPE["ACK"], "")
                    await self.req_packet_handler_async(data, snr, rssi)
                else:
                    await self.set_mode_async("RXCONTINUOUS")
            elif pkt_type == self.PKT_TYPE["ACK"]:
                if pkt_id == self._pkt_id:
                    self._pkt_id = 0
                    self.is_available = True
                    await self.set_mode_async("STANDBY")
                else:
                    await self.set_mode_async("RXCONTINUOUS")
            elif pkt_type == self.PKT_TYPE["BRD"]:
                await self.brd_packet_handler_async(data, snr, rssi)
                await self.set_mode_async("RXCONTINUOUS")
        elif flags & self._IRQ_FLAGS["FhssChangeChannel"]:
            await self.set_freq_async()

    async def service_async(self):
        await self.process_irq_async()

    async def process_irq_async(self):
        """Serialize FIFO/mode/ACK processing with every public transmit."""
        async with self._send_lock:
            await self._process_irq_unlocked()

    async def req_packet_handler_async(self, data, snr, rssi):
        pass

    async def brd_packet_handler_async(self, data, snr, rssi):
        pass

    async def after_TxDone_async(self, pin):
        pass

    def _log(self, msg):
        if self._debug:
            print("[SX1276] %s" % msg)

    async def deinit_async(self):
        if self._spi is None:
            return
        if self._dio0_pin is not None:
            self._dio0_pin.irq(handler=None)
        if self._dio1_pin is not None:
            self._dio1_pin.irq(handler=None)
        await self.set_mode_async("SLEEP")
        self._initialized = False
        self._spi = self._cs_pin = self._rst_pin = None

    async def aclose(self):
        await self.deinit_async()

# ======================================== 初始化配置 ==========================================

# ======================================== 主程序 ==============================================
