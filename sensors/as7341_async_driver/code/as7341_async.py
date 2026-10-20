
# Preserve the documented exception contract on MicroPython.
try:
    TimeoutError
except NameError:
    try:
        from uasyncio import TimeoutError
    except ImportError:
        from asyncio import TimeoutError

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio
import time
from struct import unpack_from
from _gs_as7341_as7341 import AS7341
_ASYNC_FACADE_P0 = True

class AS7341Async(AS7341):
    """Await initialize_async(); public async operations share one bus lock."""

    def __init__(self, i2c, addr=57):
        """
            初始化AS7341传感器对象
            Initialize AS7341 sensor object

            Args:
                i2c (machine.I2C): 已初始化的I2C总线对象
                                   Initialized I2C bus object
                addr (int): 传感器I2C地址，默认0x39
                            Sensor I2C address, default 0x39

            Notes:
                必须传入有效的I2C总线对象，否则传感器无法通信
                Must pass a valid I2C bus object, otherwise the sensor cannot communicate
            """
        self._bus = i2c
        self._address = addr
        self._buffer1 = bytearray(1)
        self._buffer2 = bytearray(2)
        self._buffer13 = bytearray(13)
        self._measuremode = self.AS7341_MODE_SPM
        self._connected = False
        self._async_lock = asyncio.Lock()

    async def initialize_async(self):
        self._connected = await self.reset_async()
        return self._connected

    async def start_measure_async(self, selection=None, timeout_ms=2000, poll_ms=50):
        async with self._async_lock:
            try:
                return await self._unlocked_start_measure_async(selection, timeout_ms, poll_ms)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_start_measure_async(self, selection=None, timeout_ms=2000, poll_ms=50):
        if not isinstance(timeout_ms, int) or timeout_ms <= 0:
            raise ValueError('timeout_ms must be a positive integer')
        if not isinstance(poll_ms, int) or poll_ms <= 0:
            raise ValueError('poll_ms must be a positive integer')
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        await self._modify_reg_async(self.AS7341_CFG_0, self.AS7341_CFG_0_LOW_POWER, False)
        await self._unlocked_set_spectral_measurement_async(False)
        await self._write_byte_async(self.AS7341_CFG_6, self.AS7341_CFG_6_SMUX_CMD_WRITE)
        if selection is not None:
            await self._unlocked_channel_select_async(selection)
        if self._measuremode == self.AS7341_CONFIG_INT_MODE_SPM:
            await self._unlocked_set_smux_async(True)
        elif self._measuremode == self.AS7341_CONFIG_INT_MODE_SYNS:
            await self._unlocked_set_smux_async(True)
            await self._unlocked_set_gpio_input_async(True)
        await self._unlocked_set_spectral_measurement_async(True)
        if self._measuremode == self.AS7341_CONFIG_INT_MODE_SPM:
            while not await self._unlocked_measurement_completed_async():
                if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                    raise TimeoutError('AS7341 measurement timeout after %d ms' % timeout_ms)
                await asyncio.sleep_ms(poll_ms)

    async def _read_byte_async(self, reg):
        try:
            self._bus.readfrom_mem_into(self._address, reg, self._buffer1)
            return self._buffer1[0]
        except Exception as err:
            print('I2C read_byte at 0x{:02X}, error: {}'.format(reg, err))
            return -1

    async def _read_word_async(self, reg):
        try:
            self._bus.readfrom_mem_into(self._address, reg, self._buffer2)
            return int.from_bytes(self._buffer2, 'little')
        except Exception as err:
            print('I2C read_word at 0x{:02X}, error: {}'.format(reg, err))
            return -1

    async def _read_all_channels_async(self):
        try:
            self._bus.readfrom_mem_into(self._address, self.AS7341_ASTATUS, self._buffer13)
            return unpack_from('<HHHHHH', self._buffer13, 1)
        except Exception as err:
            print('I2C read_all_channels at 0x{:02X}, error: {}'.format(self.AS7341_ASTATUS, err))
            return []

    async def _write_byte_async(self, reg, value):
        self._buffer1[0] = value & 255
        try:
            self._bus.writeto_mem(self._address, reg, self._buffer1)
            await asyncio.sleep_ms(10)
        except Exception as err:
            print('I2C write_byte at 0x{:02X}, error: {}'.format(reg, err))
            return False
        return True

    async def _write_word_async(self, reg, value):
        self._buffer2[0] = value & 255
        self._buffer2[1] = value >> 8 & 255
        try:
            self._bus.writeto_mem(self._address, reg, self._buffer2)
            await asyncio.sleep_ms(20)
        except Exception as err:
            print('I2C write_word at 0x{:02X}, error: {}'.format(reg, err))
            return False
        return True

    async def _write_burst_async(self, reg, value):
        try:
            self._bus.writeto_mem(self._address, reg, value)
            await asyncio.sleep_ms(100)
        except Exception as err:
            print('I2C write_burst at 0x{:02X}, error: {}'.format(reg, err))
            return False
        return True

    async def _modify_reg_async(self, reg, mask, flag=True):
        data = await self._read_byte_async(reg)
        if flag:
            data |= mask
        else:
            data &= ~mask
        await self._write_byte_async(reg, data)

    async def _set_bank_async(self, bank=1):
        await self._modify_reg_async(self.AS7341_CFG_0, self.AS7341_CFG_0_REG_BANK, bank != 0)

    async def enable_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_enable_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_enable_async(self):
        await self._write_byte_async(self.AS7341_ENABLE, self.AS7341_ENABLE_PON)

    async def disable_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_disable_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_disable_async(self):
        await self._set_bank_async(1)
        await self._write_byte_async(self.AS7341_CONFIG, 0)
        await self._set_bank_async(0)
        await self._write_byte_async(self.AS7341_ENABLE, 0)

    async def reset_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_reset_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_reset_async(self):
        await self._unlocked_disable_async()
        await asyncio.sleep_ms(50)
        await self._unlocked_enable_async()
        await asyncio.sleep_ms(50)
        id = await self._read_byte_async(self.AS7341_ID)
        if id < 0:
            print('Failed to contact AS7341 at I2C address 0x{:02X}'.format(self._address))
            return False
        elif not id & ~3 == self.AS7341_ID_VALUE:
            print('No AS7341: found 0x{:02X}, expected 0x{:02X}'.format(id, self.AS7341_ID_VALUE))
            return False
        await self._unlocked_set_measure_mode_async(self._measuremode)
        return True

    async def isconnected_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_isconnected_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_isconnected_async(self):
        return self._connected

    async def measurement_completed_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_measurement_completed_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_measurement_completed_async(self):
        return bool(await self._read_byte_async(self.AS7341_STATUS_2) & self.AS7341_STATUS_2_AVALID)

    async def set_spectral_measurement_async(self, flag=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_spectral_measurement_async(flag)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_spectral_measurement_async(self, flag=True):
        await self._modify_reg_async(self.AS7341_ENABLE, self.AS7341_ENABLE_SP_EN, flag)

    async def set_smux_async(self, flag=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_smux_async(flag)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_smux_async(self, flag=True):
        await self._modify_reg_async(self.AS7341_ENABLE, self.AS7341_ENABLE_SMUXEN, flag)

    async def set_measure_mode_async(self, mode=AS7341.AS7341_CONFIG_INT_MODE_SPM):
        async with self._async_lock:
            try:
                return await self._unlocked_set_measure_mode_async(mode)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_measure_mode_async(self, mode=AS7341.AS7341_CONFIG_INT_MODE_SPM):
        if mode in (self.AS7341_CONFIG_INT_MODE_SPM, self.AS7341_CONFIG_INT_MODE_SYNS, self.AS7341_CONFIG_INT_MODE_SYND):
            self._measuremode = mode
            await self._set_bank_async(1)
            data = await self._read_byte_async(self.AS7341_CONFIG) & ~3
            data |= mode
            await self._write_byte_async(self.AS7341_CONFIG, data)
            await self._set_bank_async(0)

    async def channel_select_async(self, selection):
        async with self._async_lock:
            try:
                return await self._unlocked_channel_select_async(selection)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_channel_select_async(self, selection):
        if selection in self.AS7341_SMUX_SELECT:
            await self._write_burst_async(0, self.AS7341_SMUX_SELECT[selection])
        else:
            print('{} is unknown in self.AS7341_SMUX_SELECT'.format(selection))

    async def get_channel_data_async(self, channel=0):
        async with self._async_lock:
            try:
                return await self._unlocked_get_channel_data_async(channel)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_channel_data_async(self, channel=0):
        data = 0
        if 0 <= channel <= 5:
            data = await self._read_word_async(self.AS7341_CH_DATA + channel * 2)
            print('ch={:d}, addr={:02X}, buf2=0x{:02X}{:02X}'.format(channel, self.AS7341_CH_DATA + channel * 2, self._buffer2[0], self._buffer2[1]))
        return data

    async def get_spectral_data_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_spectral_data_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_spectral_data_async(self):
        return await self._read_all_channels_async()

    async def set_flicker_detection_async(self, flag=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_flicker_detection_async(flag)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_flicker_detection_async(self, flag=True):
        await self._modify_reg_async(self.AS7341_ENABLE, self.AS7341_ENABLE_FDEN, flag)

    async def get_flicker_frequency_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_flicker_frequency_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_flicker_frequency_async(self):
        await self._modify_reg_async(self.AS7341_CFG_0, self.AS7341_CFG_0_LOW_POWER, False)
        await self._unlocked_set_spectral_measurement_async(False)
        await self._write_byte_async(self.AS7341_CFG_6, self.AS7341_CFG_6_SMUX_CMD_WRITE)
        await self._unlocked_channel_select_async('FD')
        await self._unlocked_set_smux_async(True)
        await self._unlocked_set_spectral_measurement_async(True)
        await self._unlocked_set_flicker_detection_async(True)
        for _ in range(10):
            fd_status = await self._read_byte_async(self.AS7341_FD_STATUS)
            if fd_status & self.AS7341_FD_STATUS_FD_MEAS_VALID:
                break
            await asyncio.sleep_ms(50)
        else:
            print('Flicker measurement timed out')
            return 0
        for _ in range(10):
            fd_status = await self._read_byte_async(self.AS7341_FD_STATUS)
            if fd_status & self.AS7341_FD_STATUS_FD_100_VALID or fd_status & self.AS7341_FD_STATUS_FD_120_VALID:
                break
            await asyncio.sleep_ms(50)
        else:
            print('Flicker frequency calculation timed out')
            return 0
        await self._unlocked_set_flicker_detection_async(False)
        await self._write_byte_async(self.AS7341_FD_STATUS, 60)
        if fd_status & self.AS7341_FD_STATUS_FD_100_VALID and fd_status & self.AS7341_FD_STATUS_FD_100HZ:
            return 100
        elif fd_status & self.AS7341_FD_STATUS_FD_120_VALID and fd_status & self.AS7341_FD_STATUS_FD_120HZ:
            return 120
        return 0

    async def set_gpio_input_async(self, enable=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_gpio_input_async(enable)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_gpio_input_async(self, enable=True):
        mask = self.AS7341_GPIO_2_GPIO_OUT
        if enable:
            mask |= self.AS7341_GPIO_2_GPIO_IN_EN
        await self._write_byte_async(self.AS7341_GPIO_2, mask)

    async def get_gpio_value_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_gpio_value_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_gpio_value_async(self):
        return bool(await self._read_byte_async(self.AS7341_GPIO_2) & self.AS7341_GPIO_2_GPIO_IN)

    async def set_gpio_output_async(self, inverted=False):
        async with self._async_lock:
            try:
                return await self._unlocked_set_gpio_output_async(inverted)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_gpio_output_async(self, inverted=False):
        mask = 0
        if inverted:
            mask |= self.AS7341_GPIO_2_GPIO_INV
        await self._write_byte_async(self.AS7341_GPIO_2, mask)

    async def set_gpio_inverted_async(self, flag=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_gpio_inverted_async(flag)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_gpio_inverted_async(self, flag=True):
        await self._modify_reg_async(self.AS7341_GPIO_2, self.AS7341_GPIO_2_GPIO_INV, flag)

    async def set_gpio_mask_async(self, mask=0):
        async with self._async_lock:
            try:
                return await self._unlocked_set_gpio_mask_async(mask)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_gpio_mask_async(self, mask=0):
        await self._write_byte_async(self.AS7341_GPIO_2, mask)
        print('GPIO_2 = 0x{:02X}'.format(await self._read_byte_async(self.AS7341_GPIO_2)))

    async def set_astep_async(self, value=599):
        async with self._async_lock:
            try:
                return await self._unlocked_set_astep_async(value)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_astep_async(self, value=599):
        if 0 <= value <= 65534:
            await self._write_word_async(self.AS7341_ASTEP, value)

    async def get_astep_time_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_astep_time_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_astep_time_async(self):
        return (await self._read_word_async(self.AS7341_ASTEP) + 1) * 2.78 / 1000

    async def set_atime_async(self, value=29):
        async with self._async_lock:
            try:
                return await self._unlocked_set_atime_async(value)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_atime_async(self, value=29):
        if 0 <= value <= 255:
            await self._write_byte_async(self.AS7341_ATIME, value)

    async def get_overflow_count_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_overflow_count_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_overflow_count_async(self):
        return (await self._read_word_async(self.AS7341_ASTEP) + 1) * (await self._read_byte_async(self.AS7341_ATIME) + 1)

    async def get_integration_time_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_integration_time_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_integration_time_async(self):
        return await self._unlocked_get_overflow_count_async() * 2.78 / 1000

    async def set_again_async(self, code):
        async with self._async_lock:
            try:
                return await self._unlocked_set_again_async(code)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_again_async(self, code):
        if 0 <= code <= 10:
            await self._write_byte_async(self.AS7341_CFG_1, code)

    async def get_again_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_again_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_again_async(self):
        return await self._read_byte_async(self.AS7341_CFG_1)

    async def set_again_factor_async(self, factor):
        async with self._async_lock:
            try:
                return await self._unlocked_set_again_factor_async(factor)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_again_factor_async(self, factor):
        for code in range(10, -1, -1):
            if 2 ** (code - 1) <= factor:
                break
        await self._write_byte_async(self.AS7341_CFG_1, code)

    async def get_again_factor_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_again_factor_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_again_factor_async(self):
        return 2 ** (await self._unlocked_get_again_async() - 1)

    async def set_wen_async(self, flag=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_wen_async(flag)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_wen_async(self, flag=True):
        await self._modify_reg_async(self.AS7341_ENABLE, self.AS7341_ENABLE_WEN, flag)

    async def set_wtime_async(self, code):
        async with self._async_lock:
            try:
                return await self._unlocked_set_wtime_async(code)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_wtime_async(self, code):
        await self._write_byte_async(self.AS7341_WTIME, code)

    async def set_led_current_async(self, current):
        async with self._async_lock:
            try:
                return await self._unlocked_set_led_current_async(current)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_led_current_async(self, current):
        await self._set_bank_async(1)
        if 4 <= current <= 20:
            await self._modify_reg_async(self.AS7341_CONFIG, self.AS7341_CONFIG_LED_SEL, True)
            data = self.AS7341_LED_LED_ACT + (current - 4) // 2
        else:
            await self._modify_reg_async(self.AS7341_CONFIG, self.AS7341_CONFIG_LED_SEL, False)
            data = 0
        await self._write_byte_async(self.AS7341_LED, data)
        await self._set_bank_async(0)
        await asyncio.sleep_ms(100)

    async def alert_pending_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_alert_pending_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_alert_pending_async(self):
        data = await self._read_byte_async(self.AS7341_STATUS)
        if data & self.AS7341_STATUS_ASAT:
            print('Spectral interrupt generation!')
            return True
        return False

    async def clear_alert_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_clear_alert_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_clear_alert_async(self):
        await self._write_byte_async(self.AS7341_STATUS, 255)

    async def set_spectral_alert_async(self, flag=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_spectral_alert_async(flag)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_spectral_alert_async(self, flag=True):
        await self._modify_reg_async(self.AS7341_INTENAB, self.AS7341_INTENAB_SP_IEN, flag)

    async def set_alert_persistence_async(self, value):
        async with self._async_lock:
            try:
                return await self._unlocked_set_alert_persistence_async(value)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_alert_persistence_async(self, value):
        if 0 <= value <= 15:
            await self._write_byte_async(self.AS7341_PERS, value)

    async def set_spectral_threshold_channel_async(self, value):
        async with self._async_lock:
            try:
                return await self._unlocked_set_spectral_threshold_channel_async(value)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_spectral_threshold_channel_async(self, value):
        if 0 <= value <= 4:
            await self._write_byte_async(self.AS7341_CFG_12, value)

    async def set_thresholds_async(self, lo, hi):
        async with self._async_lock:
            try:
                return await self._unlocked_set_thresholds_async(lo, hi)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_thresholds_async(self, lo, hi):
        if lo < hi:
            await self._write_word_async(self.AS7341_SP_TH_LOW, lo)
            await self._write_word_async(self.AS7341_SP_TH_HIGH, hi)
            await asyncio.sleep_ms(20)

    async def get_thresholds_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_get_thresholds_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_get_thresholds_async(self):
        lo = await self._read_word_async(self.AS7341_SP_TH_LOW)
        hi = await self._read_word_async(self.AS7341_SP_TH_HIGH)
        return (lo, hi)

    async def set_syns_int_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_set_syns_int_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_syns_int_async(self):
        await self._set_bank_async(1)
        await self._write_byte_async(self.AS7341_CONFIG, self.AS7341_CONFIG_INT_SEL | self.AS7341_CONFIG_INT_MODE_SYNS)
        await self._set_bank_async(0)

    async def check_interrupt_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_check_interrupt_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_check_interrupt_async(self):
        return await self._unlocked_alert_pending_async()

    async def clear_interrupt_async(self):
        async with self._async_lock:
            try:
                return await self._unlocked_clear_interrupt_async()
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_clear_interrupt_async(self):
        return await self._unlocked_clear_alert_async()

    async def set_spectral_interrupt_async(self, flag=True):
        async with self._async_lock:
            try:
                return await self._unlocked_set_spectral_interrupt_async(flag)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_spectral_interrupt_async(self, flag=True):
        return await self._unlocked_set_spectral_alert_async(flag)

    async def set_interrupt_persistence_async(self, value):
        async with self._async_lock:
            try:
                return await self._unlocked_set_interrupt_persistence_async(value)
            except asyncio.CancelledError:
                self._connected = False
                await self._set_bank_async(0)
                raise

    async def _unlocked_set_interrupt_persistence_async(self, value):
        return await self._unlocked_set_alert_persistence_async(value)

    async def aclose(self):
        await self.disable_async()
