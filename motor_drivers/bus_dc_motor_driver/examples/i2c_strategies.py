# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : i2c_strategies.py
# @Description : Exclusive-PCA bench writers; production library defaults are unchanged.
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
import ustruct


# ======================================== 全局变量 ========================================
# ======================================== 功能函数 ========================================
def pack_channel(buffer: bytearray, offset: int, value: int) -> None:
    """Encode PCA full-on/off flags without allocating a new packed object."""
    ustruct.pack_into("<HH", buffer, offset, 4096 if value == 4095 else 0, 4096 if value == 0 else value if value != 4095 else 0)


# ======================================== 自定义类 ========================================
class BenchWriter:
    """Own only CH0..7 during this experiment; all errors invalidate cached state.

    Stock/prealloc retain immediate per-channel writes. Batch buffers until flush.
    Reversal first commits all-off, waits 200us, then commits the requested frame.
    This bench delay is not a universal H-bridge dead-time specification.
    """

    def __init__(self, pca: object, mode: str) -> None:
        if mode not in ("stock", "prealloc", "batch"):
            raise ValueError("Unknown bench writer")
        self.pca = pca
        self.mode = mode
        self.original_duty = pca.duty
        self.original_pwm = pca.pwm
        self.single = bytearray(4)
        self.frame = bytearray(32)
        self.off = bytearray(32)
        self.verify_buffer = bytearray(32)
        self.levels = [0] * 8
        self.committed = [0] * 8
        self.cache = {}
        self.pending = False
        self.reversal_frames = 0
        for channel in range(8):
            pack_channel(self.off, channel * 4, 0)
        if mode != "stock":
            pca.pwm = self.pwm
        pca.duty = self.duty

    def pwm(self, index: int, on: int, off: int) -> None:
        """Same register payload as PCA9685.pwm, with a reusable four-byte buffer."""
        if not 0 <= index <= 15 or not 0 <= on <= 4096 or not 0 <= off <= 4096:
            raise ValueError("PWM parameters outside PCA range")
        ustruct.pack_into("<HH", self.single, 0, on, off)
        self.pca.i2c.writeto_mem(self.pca.address, 6 + 4 * index, self.single)

    def duty(self, index: int, value: int, invert: bool = False) -> int:
        """Cache confirmed writes; only buffer in an explicitly opened batch frame."""
        if type(index) is not int or not 0 <= index < 8 or type(value) is not int or not 0 <= value <= 4095:
            raise ValueError("Bench duty must target CH0..7 with integer duty")
        applied = 4095 - value if invert else value
        self.levels[index] = applied
        if self.mode == "batch" and self.pending:
            return applied
        key = (value, invert)
        if self.cache.get(index) != key:
            try:
                self.original_duty(index, value, invert)
            except BaseException:
                self.cache.clear()
                raise
            self.cache[index] = key
        self.committed[index] = applied
        return applied

    def begin(self) -> None:
        self.pending = self.mode == "batch"

    def flush(self) -> None:
        """Commit a whole 32-byte frame on STOP; no Python per-channel transfers."""
        if not self.pending:
            return
        self.pending = False
        if self.levels == self.committed:
            return
        reversing = any((self.levels[i] and self.committed[i + 1]) or (self.levels[i + 1] and self.committed[i]) for i in range(0, 8, 2))
        for channel in range(8):
            pack_channel(self.frame, channel * 4, self.levels[channel])
        try:
            if reversing:
                self.pca.i2c.writeto_mem(self.pca.address, 6, self.off)
                for channel in range(8):
                    self.committed[channel] = 0
                self.reversal_frames += 1
                time.sleep_us(200)
            self.pca.i2c.writeto_mem(self.pca.address, 6, self.frame)
            for channel in range(8):
                self.committed[channel] = self.levels[channel]
            self.cache.clear()
        except BaseException:
            self.cache.clear()
            raise

    def verify(self) -> None:
        for channel in range(8):
            pack_channel(self.verify_buffer, channel * 4, self.committed[channel])
        actual = self.pca.i2c.readfrom_mem(self.pca.address, 6, 32)
        if actual != self.verify_buffer:
            raise RuntimeError("PCA PWM register readback mismatch")

    def stop(self) -> None:
        """Always attempt eight immediate writes; never defer emergency stopping."""
        self.pending = False
        self.cache.clear()
        error = None
        for channel in range(8):
            try:
                self.original_duty(channel, 0)
                self.levels[channel] = self.committed[channel] = 0
            except Exception as exc:
                if error is None:
                    error = exc
        if error is not None:
            raise error

    def deinit(self) -> None:
        try:
            self.stop()
        finally:
            self.pca.duty = self.original_duty
            self.pca.pwm = self.original_pwm


# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
