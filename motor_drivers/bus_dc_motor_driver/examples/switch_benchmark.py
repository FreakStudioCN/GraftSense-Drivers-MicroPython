# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : switch_benchmark.py
# @Description : Timestamped stop/setup/log costs, legacy vs confirmed off-frame.
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
import gc
from machine import I2C, Pin
from board_setup import create_pca, create_controller
from tuning_profile import MOTOR_PRESETS, measure_us
from voltage_monitor import VoltageMonitor
from timing_audit import TimingHistogram
from i2c_strategies import BenchWriter
from direction_switch import switch_reference, emergency_stop

# ======================================== 全局变量 ========================================
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
# ======================================== 自定义类 ========================================
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
