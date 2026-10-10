"""Cooperative E22 TX/RX completion bridge.

SPI commands, reset pulses and bounded BUSY command regions remain contiguous
source operations.  Only the potentially timeout-long DIO1 completion wait is
cooperative.
"""
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from e22_900m22s import E22_900M22S
from sx126x import SX126XError, SX126XStateError, SX126XTimeoutError
from _sx126x import (
    SX1262_PA_DEVICE_SEL, SX1262_PA_DUTY_CYCLE_22_DBM, SX1262_PA_HP_MAX_22_DBM,
    SX1262_PA_LUT, SX126X_CALIBRATE_ALL, SX126X_CMD_CALIBRATE,
    SX126X_CMD_CALIBRATE_IMAGE, SX126X_CMD_CLEAR_DEVICE_ERRORS,
    SX126X_CMD_CLEAR_IRQ_STATUS, SX126X_CMD_GET_DEVICE_ERRORS,
    SX126X_CMD_SET_BUFFER_BASE_ADDRESS, SX126X_CMD_SET_DIO2_AS_RF_SWITCH_CTRL,
    SX126X_CMD_SET_DIO3_AS_TCXO_CTRL, SX126X_CMD_SET_PACKET_PARAMS,
    SX126X_CMD_SET_MODULATION_PARAMS, SX126X_CMD_SET_PACKET_TYPE,
    SX126X_CMD_SET_PA_CONFIG, SX126X_CMD_SET_REGULATOR_MODE,
    SX126X_CMD_SET_RF_FREQUENCY, SX126X_CMD_SET_RX_TX_FALLBACK_MODE,
    SX126X_CMD_SET_STANDBY, SX126X_CMD_SET_TX, SX126X_CMD_SET_RX,
    SX126X_CMD_SET_TX_PARAMS, SX126X_CMD_SET_DIO_IRQ_PARAMS,
    SX126X_CMD_WRITE_BUFFER, SX126X_CMD_READ_BUFFER,
    SX126X_CMD_GET_IRQ_STATUS, SX126X_CMD_GET_RX_BUFFER_STATUS,
    SX126X_CMD_GET_PACKET_STATUS, SX126X_DIO2_AS_RF_SWITCH,
    SX126X_DIO3_OUTPUT_2_2, SX126X_FALLBACK_STANDBY_RC, SX126X_IRQ_ALL,
    SX126X_IRQ_CRC_ERROR, SX126X_IRQ_HEADER_ERROR, SX126X_IRQ_RX_DONE,
    SX126X_IRQ_TIMEOUT, SX126X_IRQ_TX_DONE, SX126X_LORA_BW_125_0,
    SX126X_LORA_CRC_ON, SX126X_LORA_HEADER_EXPLICIT,
    SX126X_LORA_IQ_STANDARD, SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_OFF,
    SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_ON, SX126X_LORA_SYNC_WORD_PRIVATE_LSB,
    SX126X_LORA_SYNC_WORD_PRIVATE_MSB, SX126X_PA_RAMP_200_US,
    SX126X_REG_LORA_SYNC_WORD_MSB, SX126X_REG_OCP_CONFIGURATION,
    SX126X_REG_SENSITIVITY_CONFIG, SX126X_REG_TX_CLAMP_CONFIG,
    SX126X_REGULATOR_DCDC, SX126X_REGULATOR_LDO, SX126X_STANDBY_RC,
    SX126X_STATE_STANDBY,
)


class SyncAdapterMixin:
    async def aclose(self):
        self.deinit()


class E22_900M22SAsync(SyncAdapterMixin, E22_900M22S):
    """Serialize E22 operations and bridge DIO1 completion into uasyncio."""

    def __init__(self, spi: object, cs: object, reset: object, busy: object,
                 dio1: object, busy_timeout_ms: int = 5000,
                 debug: bool = False) -> None:
        super().__init__(spi, cs, reset, busy, dio1,
                         busy_timeout_ms=busy_timeout_ms, debug=debug)
        self._async_lock = asyncio.Lock()
        self._dio1_pending = False
        self._dio1_irq_registered = False
        try:
            pin = self._radio._dio1
            trigger = getattr(pin, "IRQ_RISING", None)
            if trigger is not None:
                pin.irq(handler=self._dio1_irq, trigger=trigger)
                self._dio1_irq_registered = True
        except (AttributeError, TypeError):
            # Polling the injected DIO1 value remains the portable fallback.
            pass

    def _dio1_irq(self, _pin):
        # IRQ-safe: only assign a pre-existing boolean; parsing remains in task context.
        self._dio1_pending = True

    async def _wait_dio1_async(self, timeout_ms, operation):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while not self._dio1_pending and not self._radio._dio1.value():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                irq_status = await self._get_irq_status_async()
                await self._clear_irq_status_async(irq_status or SX126X_IRQ_ALL)
                raise SX126XTimeoutError("host timeout waiting for " + operation)
            await asyncio.sleep_ms(1)
        self._dio1_pending = False

    async def initialized_async(self): return self.initialized
    async def initialization_plan_async(self): return self.initialization_plan
    async def state_async(self): return self.state
    async def build_initialization_plan_async(self, frequency_mhz, bandwidth_khz=125.0,
                                              spreading_factor=9, coding_rate=7,
                                              output_power_dbm=14, preamble_length=8,
                                              use_regulator_ldo=False):
        return self.build_initialization_plan(frequency_mhz, bandwidth_khz,
            spreading_factor, coding_rate, output_power_dbm, preamble_length,
            use_regulator_ldo)

    async def _command_async(self, opcode, data, operation):
        """Execute one source command and preserve its post-command status probe."""
        radio = self._radio
        timeout_ms = radio._busy_timeout_ms
        await radio.write_command_async(opcode, data, timeout_ms)
        status = await radio.get_status_async(timeout_ms)
        radio._check_command_status(status, operation)
        return status

    async def _reset_async(self):
        """Keep the source reset pulse train contiguous, then await BUSY release."""
        radio = self._radio
        radio._cs.value(1)
        radio._reset.value(1)
        time.sleep_us(150)
        radio._reset.value(0)
        time.sleep_us(150)
        radio._reset.value(1)
        time.sleep_us(150)
        await radio.wait_while_busy_async(radio._busy_timeout_ms, "reset")
        return await radio.get_status_async(radio._busy_timeout_ms)

    async def _write_register_async(self, address, data):
        return await self._radio.write_register_async(address, data, self._radio._busy_timeout_ms)

    async def _configure_output_power_async(self, output_power_dbm):
        radio = self._radio
        timeout_ms = radio._busy_timeout_ms
        ocp_value = await radio.read_register_async(SX126X_REG_OCP_CONFIGURATION, 1, timeout_ms)
        try:
            clamp = await radio.read_register_async(SX126X_REG_TX_CLAMP_CONFIG, 1, timeout_ms)
            await self._write_register_async(SX126X_REG_TX_CLAMP_CONFIG, bytes((clamp[0] | 0x1E,)))
            await self._command_async(
                SX126X_CMD_SET_PA_CONFIG,
                bytes((SX1262_PA_DUTY_CYCLE_22_DBM, SX1262_PA_HP_MAX_22_DBM,
                       SX1262_PA_DEVICE_SEL, SX1262_PA_LUT)), "SetPaConfig",
            )
            await self._command_async(
                SX126X_CMD_SET_TX_PARAMS,
                bytes((output_power_dbm & 0xFF, SX126X_PA_RAMP_200_US)), "SetTxParams",
            )
        except SX126XError:
            await self._write_register_async(SX126X_REG_OCP_CONFIGURATION, ocp_value)
            raise
        await self._write_register_async(SX126X_REG_OCP_CONFIGURATION, ocp_value)

    async def initialize_async(self, frequency_mhz, bandwidth_khz=125.0,
                               spreading_factor=9, coding_rate=7,
                               output_power_dbm=14, preamble_length=8,
                               use_regulator_ldo=False):
        """Run the source initialization plan with cooperative BUSY boundaries."""
        plan = self.build_initialization_plan(
            frequency_mhz, bandwidth_khz, spreading_factor, coding_rate,
            output_power_dbm, preamble_length, use_regulator_ldo,
        )
        radio = self._radio
        timeout_ms = radio._busy_timeout_ms
        self._initialized = False
        async with self._async_lock:
            radio._lora_configured = False
            await self._reset_async()
            await self._command_async(SX126X_CMD_SET_STANDBY, bytes((SX126X_STANDBY_RC,)), "SetStandby")
            radio._state = SX126X_STATE_STANDBY
            await self._command_async(SX126X_CMD_SET_DIO3_AS_TCXO_CTRL, b"\x03\x00\x01\x40", "SetDio3AsTcxoCtrl")
            await self._command_async(SX126X_CMD_SET_REGULATOR_MODE, bytes((SX126X_REGULATOR_LDO if use_regulator_ldo else SX126X_REGULATOR_DCDC,)), "SetRegulatorMode")
            await self._command_async(SX126X_CMD_SET_DIO2_AS_RF_SWITCH_CTRL, bytes((SX126X_DIO2_AS_RF_SWITCH,)), "SetDio2AsRfSwitchCtrl")
            await self._command_async(SX126X_CMD_SET_BUFFER_BASE_ADDRESS, b"\x00\x00", "SetBufferBaseAddress")
            await self._command_async(SX126X_CMD_SET_PACKET_TYPE, b"\x01", "SetPacketType")
            await self._command_async(SX126X_CMD_SET_RX_TX_FALLBACK_MODE, bytes((SX126X_FALLBACK_STANDBY_RC,)), "SetRxTxFallbackMode")
            await self._command_async(SX126X_CMD_CLEAR_IRQ_STATUS, b"\x03\xff", "ClearIrqStatus")
            await self._command_async(SX126X_CMD_CLEAR_DEVICE_ERRORS, b"\x00\x00", "ClearDeviceErrors")
            await self._command_async(SX126X_CMD_CALIBRATE, bytes((SX126X_CALIBRATE_ALL,)), "Calibrate")
            image = b"\xe1\xe9" if frequency_mhz > 900.0 else b"\xd7\xdb"
            await self._command_async(SX126X_CMD_CALIBRATE_IMAGE, image, "CalibrateImage")
            raw = int((frequency_mhz * (1 << 25)) / 32.0)
            await self._command_async(SX126X_CMD_SET_RF_FREQUENCY, bytes(((raw >> 24) & 0xFF, (raw >> 16) & 0xFF, (raw >> 8) & 0xFF, raw & 0xFF)), "SetRfFrequency")
            ldro = SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_ON if float(1 << spreading_factor) / 125.0 >= 16.0 else SX126X_LORA_LOW_DATA_RATE_OPTIMIZE_OFF
            await self._command_async(SX126X_CMD_SET_MODULATION_PARAMS, bytes((spreading_factor, SX126X_LORA_BW_125_0, coding_rate - 4, ldro)), "SetModulationParams")
            await self._command_async(SX126X_CMD_SET_PACKET_PARAMS, bytes(((preamble_length >> 8) & 0xFF, preamble_length & 0xFF, SX126X_LORA_HEADER_EXPLICIT, 255, SX126X_LORA_CRC_ON, SX126X_LORA_IQ_STANDARD)), "SetPacketParams")
            await self._write_register_async(SX126X_REG_LORA_SYNC_WORD_MSB, bytes((SX126X_LORA_SYNC_WORD_PRIVATE_MSB, SX126X_LORA_SYNC_WORD_PRIVATE_LSB)))
            sensitivity = await radio.read_register_async(SX126X_REG_SENSITIVITY_CONFIG, 1, timeout_ms)
            await self._write_register_async(SX126X_REG_SENSITIVITY_CONFIG, bytes((sensitivity[0] | 0x04,)))
            await self._configure_output_power_async(output_power_dbm)
            await self._command_async(SX126X_CMD_CLEAR_IRQ_STATUS, b"\x03\xff", "ClearIrqStatus")
            await self._command_async(SX126X_CMD_SET_STANDBY, bytes((SX126X_STANDBY_RC,)), "SetStandby")
            radio._state = SX126X_STATE_STANDBY
            device_errors = await radio.read_command_async(SX126X_CMD_GET_DEVICE_ERRORS, 2, timeout_ms)
            if (device_errors[0] << 8) | device_errors[1]:
                raise SX126XStateError("device errors after initialization: 0x%04X" % ((device_errors[0] << 8) | device_errors[1]))
            radio._tx_preamble_length = preamble_length
            radio._output_power_dbm = output_power_dbm
            radio._last_initialization_plan = plan
            radio._lora_configured = True
            self._initialized = True

    async def _standby_async(self):
        await self._command_async(SX126X_CMD_SET_STANDBY, bytes((SX126X_STANDBY_RC,)), "SetStandby")
        self._radio._state = SX126X_STATE_STANDBY

    async def _set_packet_params_async(self, payload_length):
        preamble_length = self._radio._tx_preamble_length
        await self._command_async(
            SX126X_CMD_SET_PACKET_PARAMS,
            bytes(((preamble_length >> 8) & 0xFF, preamble_length & 0xFF,
                   SX126X_LORA_HEADER_EXPLICIT, payload_length, SX126X_LORA_CRC_ON,
                   SX126X_LORA_IQ_STANDARD)),
            "SetPacketParams",
        )

    async def _configure_irq_async(self, rx):
        if rx:
            irq_mask = SX126X_IRQ_RX_DONE | SX126X_IRQ_HEADER_ERROR | SX126X_IRQ_CRC_ERROR | SX126X_IRQ_TIMEOUT
            dio1_mask = SX126X_IRQ_RX_DONE
        else:
            irq_mask = SX126X_IRQ_TX_DONE | SX126X_IRQ_TIMEOUT
            dio1_mask = SX126X_IRQ_TX_DONE
        await self._command_async(
            SX126X_CMD_SET_DIO_IRQ_PARAMS,
            bytes(((irq_mask >> 8) & 0xFF, irq_mask & 0xFF,
                   (dio1_mask >> 8) & 0xFF, dio1_mask & 0xFF, 0, 0, 0, 0)),
            "SetDioIrqParams",
        )

    async def _clear_irq_status_async(self, irq_mask=SX126X_IRQ_ALL):
        await self._command_async(
            SX126X_CMD_CLEAR_IRQ_STATUS,
            bytes(((irq_mask >> 8) & 0xFF, irq_mask & 0xFF)), "ClearIrqStatus",
        )

    async def _apply_rx_sensitivity_async(self):
        radio = self._radio
        value = await radio.read_register_async(
            SX126X_REG_SENSITIVITY_CONFIG, 1, radio._busy_timeout_ms
        )
        await self._write_register_async(SX126X_REG_SENSITIVITY_CONFIG, bytes((value[0] | 0x04,)))

    async def _get_irq_status_async(self):
        radio = self._radio
        data = await radio.read_command_async(
            SX126X_CMD_GET_IRQ_STATUS, 2, radio._busy_timeout_ms
        )
        return (data[0] << 8) | data[1]

    async def _set_transfer_state_async(self, opcode, timeout_ms, state):
        timeout_raw = timeout_ms * 64
        if timeout_raw > 0xFFFFFF:
            raise ValueError("timeout_ms exceeds the SX126X 24-bit timeout")
        await self._command_async(
            opcode,
            bytes(((timeout_raw >> 16) & 0xFF, (timeout_raw >> 8) & 0xFF, timeout_raw & 0xFF)),
            "SetTx" if opcode == SX126X_CMD_SET_TX else "SetRx",
        )
        self._radio._state = state

    async def _receive_result_async(self, max_length, irq_status):
        radio = self._radio
        buffer_status = await radio.read_command_async(
            SX126X_CMD_GET_RX_BUFFER_STATUS, 2, radio._busy_timeout_ms
        )
        payload_length, pointer = buffer_status[0], buffer_status[1]
        if payload_length > max_length:
            raise SX126XStateError("received payload exceeds max_length")
        payload = await radio.read_command_async(
            SX126X_CMD_READ_BUFFER, payload_length, radio._busy_timeout_ms, bytes((pointer,))
        )
        packet_status = await radio.read_command_async(
            SX126X_CMD_GET_PACKET_STATUS, 3, radio._busy_timeout_ms
        )
        snr_raw = packet_status[1] if packet_status[1] < 128 else packet_status[1] - 256
        await self._clear_irq_status_async(irq_status)
        return payload, -packet_status[0] / 2.0, snr_raw / 4.0

    async def send_async(self, data, timeout_ms):
        if data is None or not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes-like")
        if not 1 <= len(data) <= 255: raise ValueError("data length must be between 1 and 255")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0: raise ValueError("timeout_ms must be greater than zero")
        if not self._initialized: raise RuntimeError("device must be initialized before send")
        radio = self._radio
        async with self._async_lock:
            try:
                await self._standby_async()
                await self._set_packet_params_async(len(data))
                await self._configure_irq_async(False)
                await self._command_async(SX126X_CMD_SET_BUFFER_BASE_ADDRESS, b"\x00\x00", "SetBufferBaseAddress")
                await self._clear_irq_status_async()
                await self._command_async(SX126X_CMD_WRITE_BUFFER, b"\x00" + bytes(data), "WriteBuffer")
                await self._apply_rx_sensitivity_async()
                self._dio1_pending = False
                await self._set_transfer_state_async(SX126X_CMD_SET_TX, timeout_ms, 3)
                await self._wait_dio1_async(timeout_ms, "TX_DONE")
                irq_status = await self._get_irq_status_async()
                await self._clear_irq_status_async(irq_status or SX126X_IRQ_ALL)
                if irq_status & SX126X_IRQ_TIMEOUT: raise SX126XTimeoutError("SX126X reported TX timeout")
                if not irq_status & SX126X_IRQ_TX_DONE: raise SX126XStateError("DIO1 asserted without TX_DONE")
                return len(data)
            finally:
                await self._standby_async()

    async def receive_async(self, max_length=255, timeout_ms=3000):
        if not isinstance(max_length, int) or not 1 <= max_length <= 255: raise ValueError("max_length must be between 1 and 255")
        if not isinstance(timeout_ms, int) or timeout_ms <= 0: raise ValueError("timeout_ms must be greater than zero")
        if not self._initialized: raise RuntimeError("device must be initialized before receive")
        radio = self._radio
        async with self._async_lock:
            try:
                await self._standby_async()
                await self._set_packet_params_async(max_length)
                await self._configure_irq_async(True)
                await self._command_async(SX126X_CMD_SET_BUFFER_BASE_ADDRESS, b"\x00\x00", "SetBufferBaseAddress")
                await self._clear_irq_status_async()
                await self._apply_rx_sensitivity_async()
                self._dio1_pending = False
                await self._set_transfer_state_async(SX126X_CMD_SET_RX, timeout_ms, 2)
                await self._wait_dio1_async(timeout_ms, "RX_DONE")
                irq_status = await self._get_irq_status_async()
                if irq_status & SX126X_IRQ_TIMEOUT:
                    try:
                        await self._clear_irq_status_async(irq_status or SX126X_IRQ_ALL)
                    except Exception:
                        pass
                    raise SX126XTimeoutError("SX126X reported RX timeout")
                if irq_status & (SX126X_IRQ_HEADER_ERROR | SX126X_IRQ_CRC_ERROR):
                    try:
                        await self._clear_irq_status_async(irq_status or SX126X_IRQ_ALL)
                    except Exception:
                        pass
                    raise SX126XStateError("SX126X reported RX packet error")
                if not irq_status & SX126X_IRQ_RX_DONE:
                    try:
                        await self._clear_irq_status_async(irq_status or SX126X_IRQ_ALL)
                    except Exception:
                        pass
                    raise SX126XStateError("DIO1 asserted without RX_DONE")
                return await self._receive_result_async(max_length, irq_status)
            finally:
                await self._standby_async()

    async def aclose(self):
        await self.deinit_async()
    async def deinit_async(self):
        if self._dio1_irq_registered:
            try: self._radio._dio1.irq(handler=None)
            except (AttributeError, TypeError): pass
        self.deinit()
