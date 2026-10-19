# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/09/22
# @Author  : FreakStudio
# @File    : bma423_async.py
# @Description : Source-faithful asynchronous BMA423 facade
# @License : MIT

# ======================================== 导入相关模块 =========================================
try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

from _gs_bma423_bma423 import *

# ======================================== 全局变量 ============================================
_ASYNC_FACADE_P0 = True

# ======================================== 功能函数 ============================================
# ======================================== 自定义类 =============================================
class SyncAdapterMixin:
    async def aclose(self):
        await self.deinit_async()


class BMA423Async(SyncAdapterMixin, BMA423):
    """Async operations preserve the source register and cleanup order."""

    def __init__(self, i2c, acc_range: int = 2, debug: bool = False) -> None:
        """
        初始化 BMA423 加速度传感器
        Args:
            i2c (I2C): MicroPython I2C 总线实例
            acc_range (int): 加速度量程，可选 2/4/8/16，默认 2g
            debug (bool): 是否启用调试日志输出，默认 False
        Raises:
            ValueError: 参数类型或值无效
            RuntimeError: 设备未找到或芯片 ID 不匹配
        Notes:
            - 自动扫描 I2C 总线查找设备（地址 0x18 或 0x19）
            - 初始化完成后加速度计处于工作状态
        ==========================================
        Initialize BMA423 accelerometer.
        Args:
            i2c (I2C): MicroPython I2C bus instance
            acc_range (int): Acceleration range, options 2/4/8/16, default 2g
            debug (bool): Enable debug log output, default False
        Raises:
            ValueError: Invalid parameter type or value
            RuntimeError: Device not found or chip ID mismatch
        Notes:
            - Auto-scans I2C bus for device (address 0x18 or 0x19)
            - Accelerometer is enabled after initialization
        """
        # 参数校验
        if not hasattr(i2c, "readfrom_mem") or not hasattr(i2c, "writeto_mem"):
            raise ValueError("i2c must be an I2C instance with readfrom_mem/writeto_mem")
        if acc_range not in (2, 4, 8, 16):
            raise ValueError("acc_range must be 2, 4, 8, or 16, got %s" % acc_range)
        if not isinstance(debug, bool):
            raise ValueError("debug must be bool, got %s" % type(debug))

        self._i2c = i2c
        self._addr = None
        self._range = acc_range
        self._debug = debug
        self._callback = None
        self._features_in = bytearray(FEATURES_IN_SIZE)

        # 自动扫描 I2C 总线查找设备地址
        self._initialized = False

    async def initialize_async(self):
        if self._initialized:
            return
        found_devices = self._i2c.scan()
        self._log("I2C bus scan: %s" % [hex(x) for x in found_devices])
        for addr in (self.DEFAULT_ADDR_LOW, self.DEFAULT_ADDR_HIGH):
            if addr in found_devices:
                self._addr = addr
                break
        if self._addr is None:
            raise RuntimeError("BMA423 not found on I2C bus (expected 0x18 or 0x19)")
        self._log("Device found at 0x%02X" % self._addr)

        # 软复位并校验芯片 ID
        await self.reset_async()
        chip_id = self._read_reg(REG_CHIP_ID)[0]
        if chip_id != self.EXPECTED_CHIP_ID:
            raise RuntimeError("BMA423 chip ID mismatch: expected 0x%02X, got 0x%02X" % (self.EXPECTED_CHIP_ID, chip_id))
        self._log("Chip ID verified: 0x%02X" % chip_id)

        # 初始化默认参数，使加速度计进入工作状态
        self.enable_accelerometer(acc=True, aux=False)
        self.set_accelerometer_perf(True)
        self.set_accelerometer_avg(2)
        self.set_accelerometer_freq(100)
        self.set_advanced_power_save(False, False)
        self.set_range(self._range)
        self._initialized = True

    async def reset_async(self):
        self._write_reg(REG_CMD, REG_CMD_SOFTRESET)
        await asyncio.sleep_ms(1000)

    async def _transfer_config_async(self):
        self._log("Uploading features configuration...")
        handle = self._open_config_file()
        buffer = bytearray(8)
        offset = 0
        try:
            while handle.readinto(buffer, 8) == 8:
                self._write_config_mem(offset, buffer)
                offset += 8
                await asyncio.sleep_ms(0)
            self._log("Verifying stored configuration...")
            handle.seek(0)
            offset = 0
            while handle.readinto(buffer, 8) == 8:
                if self._read_config_mem(offset, 8) != buffer:
                    raise RuntimeError("Feature config data mismatch at offset %d" % offset)
                offset += 8
                await asyncio.sleep_ms(0)
        finally:
            handle.close()
        self._log("Config transferred: %d bytes" % offset)

    async def load_features_config_async(self):
        saved_pwr_conf = self._read_reg(REG_PWR_CONF)[0]
        try:
            self._write_reg(REG_PWR_CONF, 0x00)
            await asyncio.sleep_ms(1)
            self._write_reg(REG_INIT_CTRL, 0x00)
            await self._transfer_config_async()
            self._write_reg(REG_INIT_CTRL, 0x01)
            deadline = time.ticks_add(time.ticks_ms(), ASIC_INIT_TIMEOUT_MS)
            status = 0
            while time.ticks_diff(deadline, time.ticks_ms()) >= 0:
                status = self._read_reg(REG_INTERNAL_STATUS)[0] & 0b11111
                if status == 1:
                    self._log("Features engine initialized successfully")
                    return
                await asyncio.sleep_ms(50)
            raise RuntimeError("BMA423 ASIC init timeout after %d ms, internal_status=0x%02X" % (ASIC_INIT_TIMEOUT_MS, status))
        finally:
            self._write_reg(REG_PWR_CONF, saved_pwr_conf)

    async def enable_features_detection_async(self, feature):
        return self.enable_features_detection(feature)

    async def aclose(self):
        await self.deinit_async()
    async def get_xyz_async(self):
        return super().get_xyz()

    async def get_steps_async(self):
        return super().get_steps()

    async def get_temperature_async(self):
        return super().get_temperature()

    async def deinit_async(self):
        super().deinit()

# ======================================== 初始化配置 ==========================================
# ======================================== 主程序 ==============================================