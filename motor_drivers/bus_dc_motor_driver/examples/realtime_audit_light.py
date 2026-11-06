# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : realtime_audit_light.py
# @Description : Bounded four-motor timing experiment, launched explicitly by PC.
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
import gc
from timing_audit import TimingHistogram
from board_setup import create_pca, create_controller
from voltage_monitor import VoltageMonitor

# ======================================== 全局变量 ========================================
ARM_MOTORS = False
STARTUP_I_PERCENT = 8.0
PROFILES = ((0.25, 0.30, 0.0, 160),) * 2
MOTOR_PRESETS = ((0.25, 0.30, 0.0, 160), (0.25, 0.25, 0.0, 160), (0.30, 0.25, 0.0, 200), (0.15, 0.20, 0.0, 200))
TARGETS = (30, -40, 50, -60)
VALIDATION_TARGETS = ((30, -40, 50, -60), (-30, 40, -50, 60), (30, 30, 30, 30), (-30, -30, -30, -30), (30, -40, 50, -60))


# ======================================== 功能函数 ========================================
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


# ======================================== 自定义类 ========================================
class TimedI2C:
    """Borrowed bus: measure the actual I2C calls, not the whole PWM calculation."""

    def __init__(self, bus: object, totals: list) -> None:
        self.writeto_mem = measure_us(totals, 0)(bus.writeto_mem)
        self.readfrom_mem = measure_us(totals, 0)(bus.readfrom_mem)


# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
def run(armed: bool = False, seconds: int = 10, profiles: object = None, target_profiles: object = None, per_motor: object = MOTOR_PRESETS) -> None:
    """Compare PI candidates at 20ms with an explicit speed window; stop on exit."""
    if not armed:
        print("Motion disabled. Launch explicitly with the PC recorder.")
        return
    if not 5 <= seconds <= 20:
        raise ValueError("Duration must be 5..20 seconds")
    if profiles is None and target_profiles is None:
        target_profiles = VALIDATION_TARGETS[:2]
    profiles = PROFILES if profiles is None else profiles
    if target_profiles is not None and len(target_profiles) != len(profiles):
        raise ValueError("One target tuple per tuning phase is required")
    if any(len(config) != 4 or not 20 <= config[3] <= 300 or config[3] % 20 for config in profiles):
        raise ValueError("Expected gains and a 20..300 ms window divisible by 20")
    if target_profiles is not None and any(len(targets) != 4 or any(not -60 <= rpm <= 60 for rpm in targets) for targets in target_profiles):
        raise ValueError("Expected four targets within -60..60 RPM")
    if per_motor is not None and (
        len(per_motor) != 4 or any(len(config) != 4 or not 20 <= config[3] <= 300 or config[3] % 20 for config in per_motor)
    ):
        raise ValueError("Expected four valid per-motor presets")
    pca = controller = voltage = raw_bus = None
    failed = False
    totals = [0, 0]
    try:
        pca = create_pca()
        raw_bus = pca.i2c
        controller = create_controller(pca)
        voltage = VoltageMonitor(pin=4, interval_ms=200)
        voltage.update()
        if not 6 < voltage.get_voltage() < 9:
            raise RuntimeError("Check motor supply (6..9 V)")
        pca.i2c = TimedI2C(pca.i2c, totals)
        for pid in controller._pids:
            pid.update = measure_us(totals, 1)(pid.update)
        original_rpms = [encoder.get_rpm for encoder in controller._encoders]
        original_duty = pca.duty
        cache = {}

        def cached_duty(index: int, value: int, invert: bool = False) -> int:
            key = (value, invert)
            if cache.get(index) == key:
                return 4095 - value if invert else value
            result = original_duty(index, value, invert)
            cache[index] = key
            return result

        print("META,TUNING,period_ms=20,output_limit=50,integral_limit=150")
        for phase, (kp, ki, kd, window_ms) in enumerate(profiles, 1):
            targets = TARGETS if target_profiles is None else target_profiles[phase - 1]
            period = 20
            cached = True
            print("CONFIG,%d,%.3f,%.3f,%.4f,%d" % (phase, kp, ki, kd, window_ms))
            for i, encoder in enumerate(controller._encoders):
                encoder.get_rpm = original_rpms[i]
            for pid in controller._pids:
                pid.integral_min = -150
                pid.integral_max = 150
            for motor_id in range(1, 5):
                motor_kp, motor_ki, motor_kd, motor_window = per_motor[motor_id - 1] if per_motor is not None else (kp, ki, kd, window_ms)
                controller.set_pid(motor_id, motor_kp, motor_ki, motor_kd)
                print("MOTOR_CONFIG,%d,%d,%.3f,%.3f,%.4f,%d" % (phase, motor_id, motor_kp, motor_ki, motor_kd, motor_window))
            controller.stop_all()
            controller.set_target_rpms((0, 0, 0, 0))
            time.sleep(3)
            cache.clear()
            pca.duty = cached_duty if cached else original_duty
            for motor_index, encoder in enumerate(controller._encoders):
                motor_window = per_motor[motor_index][3] if per_motor is not None else window_ms
                if motor_window <= period:
                    continue
                original_rpm = encoder.get_rpm
                history = []

                def windowed(
                    delta: int, dt: float, original: object = original_rpm, samples: list = history, size: int = motor_window // period
                ) -> float:
                    samples.append((delta, dt))
                    if len(samples) > size:
                        samples.pop(0)
                    return original(sum(item[0] for item in samples), sum(item[1] for item in samples))

                encoder.get_rpm = windowed
            controller.update()
            start = time.ticks_ms()
            deadline = time.ticks_add(start, period)
            previous_tick = start
            stats = [0] * 13
            names = ("tick_work", "gc")
            audit = {name: TimingHistogram() for name in names}
            deadline_misses = skipped_slots = 0
            last_gc = start
            heap_min = gc.mem_free()
            stepped = False
            previous_print_us = 0
            last_print = start
            last_counts = [encoder.get_count() for encoder in controller._encoders]
            last_motion = [start] * 4
            has_moved = [False] * 4
            step_at = start
            while time.ticks_diff(time.ticks_ms(), start) < (seconds + 1) * 1000:
                if time.ticks_diff(time.ticks_ms(), deadline) < 0:
                    time.sleep_ms(1)
                    continue
                tick_start = time.ticks_us()
                now = time.ticks_ms()
                deadline = time.ticks_add(deadline, period)
                while time.ticks_diff(now, deadline) >= 0:
                    skipped_slots += 1
                    deadline = time.ticks_add(deadline, period)
                control_dt = time.ticks_diff(now, previous_tick)
                previous_tick = now
                elapsed = time.ticks_diff(now, start)
                if elapsed >= 1000 and not stepped:
                    controller.set_target_rpms(targets)
                    controller.start_all()
                    prime_integral(controller, targets)
                    print("STARTUP_I,%d,%.1f" % (phase, STARTUP_I_PERCENT))
                    step_at = now
                    has_moved = [False] * 4
                    stepped = True
                    last_motion = [now] * 4
                    print("STEP,%d,%d" % (phase, elapsed))
                totals[0] = totals[1] = 0
                begin = time.ticks_us()
                controller.update()
                loop_us = time.ticks_diff(time.ticks_us(), begin)
                stats[0] += 1
                stats[1] += loop_us
                stats[2] += totals[0]
                stats[3] += totals[1]
                stats[4] = max(stats[4], loop_us)
                stats[5] = max(stats[5], totals[0])
                stats[6] = max(stats[6], totals[1])
                stats[7] += control_dt
                stats[8] = max(stats[8], control_dt)
                stats[9] += int(control_dt > period + 2)
                voltage.update()
                if phase == 2 and time.ticks_diff(now, last_gc) >= 2000:
                    gc_start = time.ticks_us()
                    gc.collect()
                    audit["gc"].add(time.ticks_diff(time.ticks_us(), gc_start))
                    last_gc = now
                heap_min = min(heap_min, gc.mem_free())
                supply = voltage.get_voltage()
                if not 6 < supply < 9:
                    raise RuntimeError("Supply outside range")
                rpms = tuple(controller.get_motor_rpm(i) for i in range(1, 5))
                if any(abs(rpm) > 180 for rpm in rpms):
                    raise RuntimeError("Unexpected speed")
                for i, encoder in enumerate(controller._encoders):
                    count = encoder.get_count()
                    if count != last_counts[i]:
                        last_motion[i] = now
                        if stepped:
                            has_moved[i] = True
                    last_counts[i] = count
                    if (
                        stepped
                        and (has_moved[i] or time.ticks_diff(now, step_at) > 4000)
                        and time.ticks_diff(now, last_motion[i]) > 2500
                        and abs(controller._pwms[i]) > 25
                    ):
                        raise RuntimeError("No encoder movement for 2.5 seconds")
                if time.ticks_diff(now, last_print) < 100:
                    work_us = time.ticks_diff(time.ticks_us(), tick_start)
                    audit["tick_work"].add(work_us)
                    deadline_misses += int(work_us > period * 1000)
                    continue
                last_print = now
                values = [phase, period, elapsed] + list(targets if stepped else (0, 0, 0, 0)) + list(rpms) + list(controller._pwms)
                values += [supply, loop_us, totals[0], totals[1], previous_print_us, control_dt]
                begin = time.ticks_us()
                print("D,%d,%d,%d,%.1f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%d,%d,%d,%d,%d" % tuple(values))
                previous_print_us = time.ticks_diff(time.ticks_us(), begin)
                stats[10] += previous_print_us
                stats[11] = max(stats[11], previous_print_us)
                stats[12] += 1
                work_us = time.ticks_diff(time.ticks_us(), tick_start)
                audit["tick_work"].add(work_us)
                deadline_misses += int(work_us > period * 1000)
            controller.stop_all()
            for name in names:
                print("AUDIT,%d,%s," % (phase, name) + ",".join(str(value) for value in audit[name].result()))
            print("BUDGET,%d,%d,%d,%d" % (phase, deadline_misses, skipped_slots, heap_min))
            print("TIMING,%d," % phase + ",".join(str(value) for value in stats))
            print("END_PHASE,%d" % phase)
        print("DONE")
    except BaseException:
        failed = True
        raise
    finally:
        # Timed proxy borrows the original bus; close the original owned object.
        error = None
        for resource in (controller, voltage, pca, raw_bus):
            if resource is not None and hasattr(resource, "deinit"):
                try:
                    resource.deinit()
                except Exception as exc:
                    if error is None:
                        error = exc
        if error is not None and not failed:
            raise error


if __name__ == "__main__":
    run(ARM_MOTORS)
