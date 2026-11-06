# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : switch_benchmark.py
# @Description : Timestamped stop/setup/log costs, legacy vs confirmed off-frame.
# @License : MIT

# 单文件测试：除 code/ 中的驱动外，不依赖其他测试脚本。

# ======================================== 导入相关模块 ========================================
import time
import gc
from machine import I2C, Pin
from pca9685 import PCA9685
from motor_controller import MotorController
from voltage_monitor import VoltageMonitor
from array import array
import ustruct


# ======================================== 全局变量 ========================================
MOTOR_CONFIGS = ((0, 1, 5, 6), (2, 3, 7, 8), (4, 5, 3, 2), (6, 7, 1, 0))
PID_PARAMS = ((0.15, 0.6, 0.0),) * 4
PPR = 13
GEAR_RATIO = 20
MOTOR_PRESETS = ((0.25, 0.30, 0.0, 160), (0.25, 0.25, 0.0, 160), (0.30, 0.25, 0.0, 200), (0.15, 0.20, 0.0, 200))
BIN_COUNT = 256
BIN_US = 100
STARTUP_I_PERCENT = 8.0
ARM_MOTORS = False
CASES = (
    (400000, "legacy_sync"),
    (400000, "frame_sync"),
    (400000, "frame_deferred"),
    (1000000, "legacy_sync"),
    (1000000, "frame_sync"),
    (1000000, "frame_deferred"),
    (400000, "frame_deferred"),
    (1000000, "frame_deferred"),
)
PARTS = (
    "software_disable",
    "hardware_off",
    "legacy_second_stop",
    "deadtime",
    "configure",
    "step_log",
    "core",
    "readback",
    "adc",
    "telemetry",
    "checks",
)
TARGETS = (30, -40, 50, -60)


# ======================================== 功能函数 ========================================
def create_pca() -> object:
    """扫描设备，将全部电机通道关闭，再设置整片 PWM 为 1000 Hz。"""
    i2c = I2C(0, scl=Pin(9), sda=Pin(10), freq=400000)
    try:
        devices = i2c.scan()
        print("I2C devices:", [hex(x) for x in devices])
        if not devices:
            raise RuntimeError("No I2C device found")
        if 0x4F not in devices:
            raise RuntimeError("Device not found at expected address")
        # 无固定芯片 ID；构造及频率设置通过寄存器读写验证响应。
        pca = PCA9685(i2c, 0x4F)
        # reset() 清除了自动递增位；pwm() 的四字节寄存器写入需要先启用它。
        pca.i2c.writeto_mem(pca.address, 0x00, b"\x20")
        for channel in range(8):
            pca.duty(channel, 0)
        pca.freq(1000)
        return pca
    except BaseException:
        try:
            if hasattr(i2c, "deinit"):
                i2c.deinit()
        except Exception:
            pass
        raise


def create_controller(pca: object = None) -> object:
    """只创建并停止四路，示例限幅为 ±50%，不改变正式入口配置。"""
    owned = pca is None
    if owned:
        pca = create_pca()
    try:
        return MotorController(
            pca,
            MOTOR_CONFIGS,
            PID_PARAMS,
            ppr=PPR,
            gear_ratio=GEAR_RATIO,
            output_limit=(-50, 50),
            integral_limit=(-50, 50),
        )
    except BaseException:
        if owned:
            try:
                if hasattr(pca.i2c, "deinit"):
                    pca.i2c.deinit()
            except Exception:
                pass
        raise


def measure_us(totals: list, slot: int) -> object:
    """Accumulate ticks_us time, including failed calls; never use in an IRQ."""

    def decorate(function: object) -> object:
        def timed(*args: object, **kwargs: object) -> object:
            start = time.ticks_us()
            try:
                return function(*args, **kwargs)
            finally:
                totals[slot] += time.ticks_diff(time.ticks_us(), start)

        return timed

    return decorate


def pack_channel(buffer: bytearray, offset: int, value: int) -> None:
    """Encode PCA full-on/off flags without allocating a new packed object."""
    ustruct.pack_into("<HH", buffer, offset, 4096 if value == 4095 else 0, 4096 if value == 0 else value if value != 4095 else 0)


def switch_reference(controller: object, writer: object, targets: tuple, optimized: bool, parts: list) -> None:
    """Fill timing slots 0..4: software, off, duplicate legacy stop, gap, setup.

    Only a successful off-frame write AND register readback permit re-enabling.
    Hardware errors preserve the original exception after immediate stop attempts.
    """
    try:
        if optimized:
            begin = time.ticks_us()
            disable_software(controller)
            parts[0] = time.ticks_diff(time.ticks_us(), begin)
            begin = time.ticks_us()
            writer.confirmed_off()
            parts[1] = time.ticks_diff(time.ticks_us(), begin)
            begin = time.ticks_us()
            time.sleep_us(200)
            parts[3] = time.ticks_diff(time.ticks_us(), begin)
        else:
            begin = time.ticks_us()
            writer.stop()
            parts[1] = time.ticks_diff(time.ticks_us(), begin)
            begin = time.ticks_us()
            controller.stop_all()
            parts[2] = time.ticks_diff(time.ticks_us(), begin)
        begin = time.ticks_us()
        controller.set_target_rpms(targets)
        controller.start_all()
        prime_integral(controller, targets)
        parts[4] = time.ticks_diff(time.ticks_us(), begin)
    except BaseException:
        try:
            emergency_stop(controller, writer)
        except Exception:
            pass
        raise


def prime_integral(controller: object, targets: tuple, percent: float = STARTUP_I_PERCENT) -> None:
    """Preload a small signed I contribution for this bench; retain each PID's limits."""
    if type(percent) not in (int, float) or not 0 <= percent <= 10:
        raise ValueError("Startup I contribution must be within 0..10 percent")
    if len(targets) != len(controller._pids):
        raise ValueError("One startup target per PID is required")
    for pid, target in zip(controller._pids, targets):
        signed = percent if target > 0 else -percent if target < 0 else 0
        initial = signed / pid.ki if pid.ki else 0
        pid.integral = max(pid.integral_min, min(pid.integral_max, initial))


def disable_software(controller: object) -> None:
    """Disable/reset every PID without writing the PWM device."""
    error = None
    for index, pid in enumerate(controller._pids):
        try:
            pid.set_enabled(False)
            controller._pwms[index] = 0
        except Exception as exc:
            if error is None:
                error = exc
    if error is not None:
        raise error


def emergency_stop(controller: object, writer: object, parts: object = None) -> None:
    """Immediate best effort: always attempt hardware stop even if PID disable fails."""
    error = None
    begin = time.ticks_us()
    try:
        disable_software(controller)
    except Exception as exc:
        error = exc
    if parts is not None:
        parts[0] = time.ticks_diff(time.ticks_us(), begin)
    begin = time.ticks_us()
    try:
        writer.stop()
    except Exception as exc:
        if error is None:
            error = exc
    if parts is not None:
        parts[1] = time.ticks_diff(time.ticks_us(), begin)
    if error is not None:
        raise error


# ======================================== 自定义类 ========================================
class TimingHistogram:
    """100us histogram upper bounds, exact mean/max; last bin is overflow."""

    def __init__(self) -> None:
        self.bins = array("I", [0] * BIN_COUNT)
        self.count = self.total = self.maximum = 0

    def add(self, elapsed_us: int) -> None:
        if elapsed_us < 0:
            raise ValueError("Elapsed time must be nonnegative")
        self.count += 1
        self.total += elapsed_us
        self.maximum = max(self.maximum, elapsed_us)
        self.bins[min(elapsed_us // BIN_US, BIN_COUNT - 1)] += 1

    def percentile(self, percent: int) -> int:
        if not 1 <= percent <= 100:
            raise ValueError("Percentile must be 1..100")
        rank = (self.count * percent + 99) // 100
        cumulative = 0
        for index, count in enumerate(self.bins):
            cumulative += count
            if cumulative >= rank:
                return min(self.maximum, (index + 1) * BIN_US) if index < BIN_COUNT - 1 else self.maximum
        return 0

    def result(self) -> tuple:
        return (self.count, self.total // max(self.count, 1), self.percentile(95), self.percentile(99), self.maximum)


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

    def confirmed_off(self) -> None:
        """One normal-stop burst plus exact readback; failures never permit reverse."""
        self.pending = False
        self.cache.clear()
        self.pca.i2c.writeto_mem(self.pca.address, 6, self.off)
        if self.pca.i2c.readfrom_mem(self.pca.address, 6, 32) != self.off:
            raise RuntimeError("Normal off-frame readback mismatch")
        for channel in range(8):
            self.levels[channel] = self.committed[channel] = 0

    def deinit(self) -> None:
        try:
            self.stop()
        finally:
            self.pca.duty = self.original_duty
            self.pca.pwm = self.original_pwm


class TimedBus:
    """Measure actual bus calls, count writes/bytes; borrowed bus ownership."""

    def __init__(self, raw: object, totals: list) -> None:
        self.raw = raw
        self.totals = totals
        self.write = raw.writeto_mem
        self.readfrom_mem = measure_us(totals, 0)(raw.readfrom_mem)

    def writeto_mem(self, address: int, register: int, data: object) -> None:
        begin = time.ticks_us()
        try:
            self.write(address, register, data)
            self.totals[2] += 1
            self.totals[3] += len(data)
        finally:
            self.totals[0] += time.ticks_diff(time.ticks_us(), begin)


# ======================================== 初始化配置 ========================================


# ======================================== 主程序 ========================================
def run(armed: bool = False, seconds: int = 12) -> None:
    """Eight bounded legacy/new-transition and synchronous/deferred-log comparisons."""
    if not armed:
        print("Motion disabled. Launch explicitly from the PC tool.")
        return
    if not 8 <= seconds <= 20:
        raise ValueError("I2C comparison duration must be 8..20 seconds")
    pca = bus = controller = voltage = writer = None
    mode2 = None
    failed = False
    try:
        pca = create_pca()
        bus = pca.i2c
        # Update all PWM registers on STOP, preserving unrelated MODE2 bits.
        mode2 = bus.readfrom_mem(pca.address, 1, 1)[0]
        bus.writeto_mem(pca.address, 1, bytes((mode2 & ~8,)))
        if not bus.readfrom_mem(pca.address, 0, 1)[0] & 0x20:
            raise RuntimeError("PCA auto-increment must be enabled")
        controller = create_controller(pca)
        voltage = VoltageMonitor(pin=4, interval_ms=200)
        for motor_id, (kp, ki, kd, window) in enumerate(MOTOR_PRESETS, 1):
            controller.set_pid(motor_id, kp, ki, kd)
        for pid in controller._pids:
            pid.integral_min, pid.integral_max = -150, 150
        for encoder, (_, _, _, window) in zip(controller._encoders, MOTOR_PRESETS):
            original = encoder.get_rpm
            history = []

            def windowed(delta: int, dt: float, method: object = original, samples: list = history, size: int = window // 20) -> float:
                samples.append((delta, dt))
                if len(samples) > size:
                    samples.pop(0)
                return method(sum(item[0] for item in samples), sum(item[1] for item in samples))

            encoder.get_rpm = windowed
        totals = [0, 0, 0, 0]
        for pid in controller._pids:
            pid.update = measure_us(totals, 1)(pid.update)
        for phase, (frequency, mode) in enumerate(CASES, 1):
            if writer is not None:
                writer.deinit()
            controller.stop_all()
            bus = I2C(0, scl=Pin(9), sda=Pin(10), freq=frequency)
            pca.i2c = bus
            print("BUS_CONFIG,%d,%d,%s,%s" % (phase, frequency, mode, bus))
            writer = BenchWriter(pca, "batch")
            writer.stop()
            # No motion: repeated all-off burst writes and exact readback first.
            for _ in range(100):
                bus.writeto_mem(pca.address, 6, writer.off)
                if bus.readfrom_mem(pca.address, 6, 32) != writer.off:
                    raise RuntimeError("Stopped preflight readback failed")
            print("PREFLIGHT,%d,100,0" % phase)
            pca.i2c = TimedBus(bus, totals)
            for motor_id, (kp, ki, kd, window) in enumerate(MOTOR_PRESETS, 1):
                print("MOTOR_CONFIG,%d,%d,%.3f,%.3f,%.4f,%d" % (phase, motor_id, kp, ki, kd, window))
            print("CONFIG,%d,0.25,0.30,0,160" % phase)
            controller.set_target_rpms((0, 0, 0, 0))
            time.sleep(3)
            controller.update()
            gc.collect()
            hist = {name: TimingHistogram() for name in ("i2c", "core", "work", "period", "steady", "transition", "emergency")}
            peaks = {name: [0, 0, 0] for name in ("work",) + PARTS}
            maximum_parts = [0] * len(PARTS)
            parts = [0] * len(PARTS)
            events = [[0] * (5 + len(PARTS)) for _ in range(3)]
            event_count = 0
            start = time.ticks_ms()
            deadline = time.ticks_add(start, 20)
            previous = last_print = last_verify = start
            stage = 0
            targets = (0, 0, 0, 0)
            counts = [encoder.get_count() for encoder in controller._encoders]
            moved_at = [start] * 4
            step_at = start
            print_us = writes = payload_bytes = verified = over_budget = 0
            while True:
                if time.ticks_diff(time.ticks_ms(), deadline) < 0:
                    time.sleep_ms(1)
                    continue
                tick = time.ticks_us()
                now = time.ticks_ms()
                deadline = time.ticks_add(deadline, 20)
                while time.ticks_diff(now, deadline) >= 0:
                    deadline = time.ticks_add(deadline, 20)
                elapsed = time.ticks_diff(now, start)
                dt = time.ticks_diff(now, previous)
                previous = now
                for i in range(len(parts)):
                    parts[i] = 0
                event_code = 0
                event_writes = 0
                totals[0] = totals[1] = totals[2] = totals[3] = 0
                if elapsed >= (seconds + 1) * 1000:
                    event_code = 3
                    emergency_stop(controller, writer, parts)
                    work = time.ticks_diff(time.ticks_us(), tick)
                    hist["emergency"].add(work)
                    hist["work"].add(work)
                    events[event_count][:5] = [elapsed, event_code, work, totals[2], totals[3]]
                    for i in range(len(parts)):
                        events[event_count][5 + i] = parts[i]
                    event_count += 1
                    for name, value in (("work", work), ("hardware_off", parts[1]), ("software_disable", parts[0])):
                        if value > peaks[name][0]:
                            peaks[name][:] = [value, elapsed, event_code]
                            if name == "work":
                                maximum_parts[:] = parts
                    over_budget += int(work > 20000)
                    break
                selected = 2 if elapsed >= 1000 + seconds * 500 else 1 if elapsed >= 1000 else 0
                if selected != stage:
                    event_code = selected
                    targets = TARGETS if selected == 1 else tuple(-value for value in TARGETS)
                    switch_reference(controller, writer, targets, mode != "legacy_sync", parts)
                    event_writes = totals[2]
                    stage = selected
                    step_at = now
                    moved_at = [now] * 4
                    if mode != "frame_deferred":
                        begin = time.ticks_us()
                        print("STEP,%d,%d,%d" % (phase, elapsed, stage))
                        parts[5] = time.ticks_diff(time.ticks_us(), begin)
                totals[0] = totals[1] = totals[2] = totals[3] = 0
                begin = time.ticks_us()
                writer.begin()
                try:
                    controller.update()
                    writer.flush()
                except BaseException:
                    try:
                        writer.stop()
                    except Exception:
                        pass
                    raise
                core_us = time.ticks_diff(time.ticks_us(), begin)
                parts[6] = core_us
                hist["i2c"].add(totals[0])
                hist["core"].add(core_us)
                hist["period"].add(dt * 1000)
                writes += totals[2]
                payload_bytes += totals[3]
                if time.ticks_diff(now, last_verify) >= 1000:
                    begin = time.ticks_us()
                    writer.verify()
                    parts[7] = time.ticks_diff(time.ticks_us(), begin)
                    verified += 1
                    last_verify = now
                begin = time.ticks_us()
                voltage.update()
                parts[8] = time.ticks_diff(time.ticks_us(), begin)
                checks_begin = time.ticks_us()
                supply = voltage.get_voltage()
                if not 6 < supply < 9:
                    raise RuntimeError("Supply outside 6..9 V")
                rpms = [controller.get_motor_rpm(i) for i in range(1, 5)]
                if any(abs(rpm) > 180 for rpm in rpms):
                    raise RuntimeError("Unexpected motor speed")
                for i, encoder in enumerate(controller._encoders):
                    count = encoder.get_count()
                    if count != counts[i]:
                        moved_at[i] = now
                    counts[i] = count
                    if stage and time.ticks_diff(now, step_at) > 4000 and time.ticks_diff(now, moved_at[i]) > 2500 and abs(controller._pwms[i]) > 25:
                        raise RuntimeError("No encoder movement under drive")
                parts[10] = time.ticks_diff(time.ticks_us(), checks_begin)
                if time.ticks_diff(now, last_print) >= 100:
                    last_print = now
                    values = (
                        [phase, 20, elapsed] + list(targets) + rpms + list(controller._pwms) + [supply, core_us, totals[0], totals[1], print_us, dt]
                    )
                    begin = time.ticks_us()
                    print("D,%d,%d,%d,%.1f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%d,%d,%d,%d,%d" % tuple(values))
                    print_us = time.ticks_diff(time.ticks_us(), begin)
                    parts[9] = print_us
                work = time.ticks_diff(time.ticks_us(), tick)
                hist["work"].add(work)
                over_budget += int(work > 20000)
                hist["transition" if event_code else "steady"].add(work)
                if event_code:
                    events[event_count][:5] = [elapsed, event_code, work, event_writes, 0]
                    for i in range(len(parts)):
                        events[event_count][5 + i] = parts[i]
                    event_count += 1
                for index, name in enumerate(PARTS):
                    if parts[index] > peaks[name][0]:
                        peaks[name][:] = [parts[index], elapsed, event_code]
                if work > peaks["work"][0]:
                    peaks["work"][:] = [work, elapsed, event_code]
                    maximum_parts[:] = parts
            writer.stop()
            controller.stop_all()
            writer.verify()
            for name, histogram in hist.items():
                print("AUDIT,%d,%s," % (phase, name) + ",".join(str(value) for value in histogram.result()))
            for name, value in peaks.items():
                print("PEAK,%d,%s,%d,%d,%d" % (phase, name, value[0], value[1], value[2]))
            print("MAX_PARTS,%d," % phase + ",".join(str(value) for value in maximum_parts))
            for row in events[:event_count]:
                print("SWITCH_EVENT,%d," % phase + ",".join(str(value) for value in row))
            print("BUS_RESULT,%d,%d,%d,%d,%d,%d,0" % (phase, writes, payload_bytes, verified, writer.reversal_frames, over_budget))
            print("END_PHASE,%d" % phase)
        print("DONE")
    except BaseException:
        failed = True
        raise
    finally:
        error = None
        for resource in (writer, controller, voltage, pca):
            if resource is not None:
                try:
                    resource.deinit()
                except Exception as exc:
                    if error is None:
                        error = exc
        if bus is not None:
            try:
                bus = I2C(0, scl=Pin(9), sda=Pin(10), freq=400000)
                if mode2 is not None:
                    bus.writeto_mem(0x4F, 1, bytes((mode2,)))
                if hasattr(bus, "deinit"):
                    bus.deinit()
            except Exception as exc:
                if error is None:
                    error = exc
        if error is not None and not failed:
            raise error


if __name__ == "__main__":
    run(ARM_MOTORS)
