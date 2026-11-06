# Python env   : MicroPython v1.29.0 / ESP32-C3
# -*- coding: utf-8 -*-
# @Time    : 2026/11/06
# @Author  : 赵岩松
# @File    : performance_profile.py
# @Description : Bounded four-motor timing experiment, launched explicitly by PC.
# @License : MIT

# ======================================== 导入相关模块 ========================================
import time
from board_setup import create_pca, create_controller
from voltage_monitor import VoltageMonitor

# ======================================== 全局变量 ========================================
ARM_MOTORS = False
TARGETS = (30, -40, 50, -60)


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


# ======================================== 自定义类 ========================================
class TimedI2C:
    """Borrowed bus: measure the actual I2C calls, not the whole PWM calculation."""

    def __init__(self, bus: object, totals: list) -> None:
        self.writeto_mem = measure_us(totals, 0)(bus.writeto_mem)
        self.readfrom_mem = measure_us(totals, 0)(bus.readfrom_mem)


# ======================================== 初始化配置 ========================================
# ======================================== 主程序 ========================================
def run(armed: bool = False, seconds: int = 10) -> None:
    """Compare periods, cached PWM and an explicit 80 ms speed window; stop on exit."""
    if not armed:
        print("Motion disabled. Launch explicitly with the PC recorder.")
        return
    if not 5 <= seconds <= 20:
        raise ValueError("Duration must be 5..20 seconds")
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
        original_duty = pca.duty
        cache = {}

        def cached_duty(index: int, value: int, invert: bool = False) -> int:
            key = (value, invert)
            if cache.get(index) == key:
                return 4095 - value if invert else value
            result = original_duty(index, value, invert)
            cache[index] = key
            return result

        print("META,USB_serial_requested_baud=921600,PID=0.15/0.6/0,raw_encoder_PPR=260")
        for phase, (period, cached) in enumerate(((100, False), (30, False), (20, False), (20, True), (20, True)), 1):
            controller.stop_all()
            controller.set_target_rpms((0, 0, 0, 0))
            time.sleep(3)
            cache.clear()
            pca.duty = cached_duty if cached else original_duty
            if phase == 5:
                for encoder in controller._encoders:
                    original_rpm = encoder.get_rpm
                    history = []

                    def windowed(delta: int, dt: float, original: object = original_rpm, samples: list = history) -> float:
                        samples.append((delta, dt))
                        if len(samples) > 4:
                            samples.pop(0)
                        return original(sum(item[0] for item in samples), sum(item[1] for item in samples))

                    encoder.get_rpm = windowed
            controller.update()
            start = time.ticks_ms()
            deadline = time.ticks_add(start, period)
            previous_tick = start
            stats = [0] * 13
            stepped = False
            previous_print_us = 0
            last_print = start
            last_counts = [encoder.get_count() for encoder in controller._encoders]
            last_motion = [start] * 4
            while time.ticks_diff(time.ticks_ms(), start) < (seconds + 1) * 1000:
                if time.ticks_diff(time.ticks_ms(), deadline) < 0:
                    time.sleep_ms(1)
                    continue
                now = time.ticks_ms()
                deadline = time.ticks_add(now, period)
                control_dt = time.ticks_diff(now, previous_tick)
                previous_tick = now
                elapsed = time.ticks_diff(now, start)
                if elapsed >= 1000 and not stepped:
                    controller.set_target_rpms(TARGETS)
                    controller.start_all()
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
                    last_counts[i] = count
                    if stepped and time.ticks_diff(now, last_motion[i]) > 2500 and abs(controller._pwms[i]) > 25:
                        raise RuntimeError("No encoder movement for 2.5 seconds")
                if time.ticks_diff(now, last_print) < 100:
                    continue
                last_print = now
                values = [phase, period, elapsed] + list(TARGETS if stepped else (0, 0, 0, 0)) + list(rpms) + list(controller._pwms)
                values += [supply, loop_us, totals[0], totals[1], previous_print_us, control_dt]
                begin = time.ticks_us()
                print("D,%d,%d,%d,%.1f,%.1f,%.1f,%.1f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f,%.3f,%d,%d,%d,%d,%d" % tuple(values))
                previous_print_us = time.ticks_diff(time.ticks_us(), begin)
                stats[10] += previous_print_us
                stats[11] = max(stats[11], previous_print_us)
                stats[12] += 1
            controller.stop_all()
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
