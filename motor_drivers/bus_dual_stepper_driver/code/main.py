# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
__version__ = "0.6.0"
__author__ = "AI Assistant"
__license__ = "MIT"

import time
from machine import I2C, Pin, Timer
from pca9685 import PCA9685

class DRV8825_Dual_Stepper:
    MICROSTEP_TABLE = {1: (0,0,0),2:(1,0,0),4:(0,1,0),8:(1,1,0),16:(0,0,1),32:(1,0,1)}
    motor1_pins = {"M0":2,"M1":1,"M2":0,"STEP":3,"DIR":5,"EN":4,"RST":7,"SLP":6}
    motor2_pins = {"M0":13,"M1":14,"M2":15,"STEP":12,"DIR":9,"EN":8,"RST":11,"SLP":10}

    def __init__(self, pca9685):
        self.pca = pca9685
        self.motors = {1: self.motor1_pins, 2: self.motor2_pins}
        self._running = {1:False, 2:False}
        
        self._timers = {1: Timer(), 2: Timer()}
        self._step_busy = {1: False, 2: False}
        self._step_channel = {1: 0, 2: 0}

        for m in (1,2):
            self.disable_motor(m)
            self.set_microstep(m, 1)

    def _write_pin(self, ch, val):
        self.pca.duty(ch, 4095 if val else 0)

    def _get_motor(self, motor):
        return self.motors.get(motor)

    def set_microstep(self, motor, mode):
        m = self._get_motor(motor)
        if not m or mode not in self.MICROSTEP_TABLE: return False
        m0,m1,m2 = self.MICROSTEP_TABLE[mode]
        self._write_pin(m["M0"],m0)
        self._write_pin(m["M1"],m1)
        self._write_pin(m["M2"],m2)
        return True

    def set_direction(self, motor, dir):
        m = self._get_motor(motor)
        if not m: return False
        self._write_pin(m["DIR"], 1 if dir else 0)
        return True

    def enable_motor(self, motor):
        m = self._get_motor(motor)
        if not m: return False
        self._write_pin(m["EN"],0)
        self._write_pin(m["SLP"],1)
        self._write_pin(m["RST"],1)
        return True

    def disable_motor(self, motor):
        m = self._get_motor(motor)
        if not m: return False
        self._write_pin(m["EN"],1)
        return True

    def _start_pwm(self, motor, delay_us):
        m = self._get_motor(motor)
        ch = m["STEP"]
        self._step_channel[motor] = ch
        freq = 1000000 // (2 * delay_us)
        self.pca.freq(freq)
        self.pca.pwm(ch, 0, 2048)

    def _stop_pwm(self, motor):
        ch = self._step_channel[motor]
        self.pca.pwm(ch, 0, 4096)
        self.disable_motor(motor)
        self._step_busy[motor] = False

    def _timer_stop_callback(self, motor):
        def callback(t):
            self._stop_pwm(motor)
        return callback

    def step(self, motor, steps, delay_us=1000):
        if motor not in (1,2) or steps==0 or self._step_busy[motor]:
            return False

        m = self._get_motor(motor)
        dir = 0 if steps>0 else 1
        self.set_direction(motor, dir)
        steps = abs(steps)

        total_us = steps * 2 * delay_us
        total_ms = max(total_us // 1000, 1)

        self._step_busy[motor] = True
        self.enable_motor(motor)
        self._start_pwm(motor, delay_us)

        self._timers[motor].init(
            period=total_ms,
            mode=Timer.ONE_SHOT,
            callback=self._timer_stop_callback(motor)
        )
        return True

    def start_continuous(self, motor, dir, delay_us=1000):
        self.reset_motor(motor)
        time.sleep_ms(5)
        self.set_direction(motor, dir)
        self.enable_motor(motor)
        self._start_pwm(motor, delay_us)
        self._running[motor] = True

    def stop_continuous(self, motor):
        self._stop_pwm(motor)
        self._running[motor] = False

    def reset_motor(self, motor):
        m = self._get_motor(motor)
        if not m: return False
        self._write_pin(m["RST"],0)
        time.sleep_ms(10)
        self._write_pin(m["RST"],1)
        return True

    def sleep_motor(self, motor):
        m = self._get_motor(motor)
        if not m: return False
        self._write_pin(m["SLP"], 0)
        return True

    def wake_motor(self, motor):
        m = self._get_motor(motor)
        if not m: return False
        self._write_pin(m["SLP"], 1)
        return True

# ==================== 初始化 ====================
i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)
pca = PCA9685(i2c)
motor_driver = DRV8825_Dual_Stepper(pca)

# ==================== 全套方法测试 ====================
if __name__ == "__main__":
    print("=== 开始全功能测试 ===")

    # 测试1：电机1 正转 1圈 (200步)
    print("\n[1/7] 电机1 正转1圈")
    motor_driver.step(1, 200, 2000)
    time.sleep(3)  # 等待转完

    # 测试2：电机1 反转 0.5圈 (100步)
    print("\n[2/7] 电机1 反转0.5圈")
    motor_driver.step(1, -100, 2000)
    time.sleep(2)

    # 测试3：电机2 正转 2圈 (400步)
    print("\n[3/7] 电机2 正转2圈")
    motor_driver.step(2, 400, 2000)
    time.sleep(6)

    # 测试4：设置16细分，电机1走200步（只转1/16圈）
    print("\n[4/7] 16细分微动")
    motor_driver.set_microstep(1, 16)
    motor_driver.step(1, 200, 3000)
    time.sleep(2)
    motor_driver.set_microstep(1, 1)  # 切回整步

    # 测试5：电机1 连续正转
    print("\n[5/7] 电机1 连续正转3秒")
    motor_driver.start_continuous(1, 0, 2000)
    time.sleep(3)
    motor_driver.stop_continuous(1)
    print("停止连续旋转")

    # 测试6：电机复位
    print("\n[6/7] 电机复位")
    motor_driver.reset_motor(1)
    time.sleep_ms(100)

    # 测试7：睡眠 / 唤醒
    print("\n[7/7] 睡眠 → 唤醒 → 微动")
    motor_driver.sleep_motor(1)
    time.sleep_ms(500)
    motor_driver.wake_motor(1)
    time.sleep_ms(500)
    motor_driver.step(1, 50, 2000)
    time.sleep(2)

    print("\n=== 全部测试完成 ===")