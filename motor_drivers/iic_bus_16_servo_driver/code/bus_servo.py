# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/08 10:00
# @Author  : 侯钧瀚
# @File    : bus_servo.py
# @Description : PCA9685 16路 PWM 驱动 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================

#导入时间模块
import time
#导入常量模块
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class BusPWMServoController:
    """
    基于 PCA9685 的 16 路 PWM 舵机控制器，支持 180° 舵机角度控制、360° 连续舵机速度控制，以及脉宽直接写入。

    Attributes:
        _pca: PCA9685 实例，需支持 freq(hz)、duty(channel, value) 方法。
        _freq (int): PWM 输出频率（Hz）。
        _cfg (dict): 通道配置字典。

    Methods:
        __init__(pca, freq=50): 初始化并设置频率。
        attach_servo(...): 注册通道与校准参数。
        detach_servo(channel): 取消注册并停止输出。
        set_angle(...): 设置 180° 舵机角度。
        set_speed(...): 设置 360° 舵机速度。
        set_pulse_us(channel, pulse_us): 直接写入脉宽。
        stop(channel): 回中或关闭输出。
        to_pwm_ticks(pulse_us): µs 转 tick。
    ==========================================
    16-channel PWM servo controller based on PCA9685. Supports 180°/360° servos and direct pulse write.

    Attributes:
        _pca: An instance of PCA9685, which needs to support the freq(hz) and duty(channel, value) methods.
        _freq (int): PWM output frequency (Hz).
        _cfg (dict): Channel configuration dictionary.

    Methods:
        __init__(pca, freq=50): Initialize and set the frequency.
        attach_servo(...): Register the channel and calibration parameters.
        detach_servo(channel): Unregister and stop the output.
        set_angle(...): Set the angle of a 180° servo.
        set_speed(...): Set the speed of a 360° servo.
        set_pulse_us(channel, pulse_us): Directly write the pulse width.
        stop(channel): Return to the middle position or turn off the output.
        to_pwm_ticks(pulse_us): Convert µs to ticks.
    """

    SERVO_180 = const(0x00)
    SERVO_360 = const(0x01)

    def __init__(self, pca, freq=50):
        """
        初始化 BusPWMServoController 类。

        Args:
            pca: 兼容 freq(hz)、duty(channel, value) 方法的 PCA9685 实例。
            freq (int): PWM 频率（Hz），默认 50。

        Raises:
            ValueError: pca 不符合接口或 freq 非正整数。
            RuntimeError: 设置频率失败。

        ==========================================
        Initialize BusPWMServoController.

        Args:
            pca: PCA9685-like object with freq(hz), duty(channel, value).
            freq (int): PWM frequency in Hz, default 50.

        Raises:
            ValueError: If pca lacks required methods or freq invalid.
            RuntimeError: If setting frequency fails.
        """
        if not hasattr(pca, "freq") or not hasattr(pca, "duty"):
            raise ValueError("pca must provide freq(hz) and duty(channel, value)")
        if not isinstance(freq, int) or freq <= 0:
            raise ValueError("freq must be a positive integer")
        self._pca = pca
        self._freq = freq
        try:
            if hasattr(self._pca, "reset"):
                self._pca.reset()
            self._pca.freq(freq)
        except Exception as e:
            raise RuntimeError("Failed to set PCA9685 frequency") from e
        self._cfg = {}

    def _ensure_channel(self, channel):
        """
        校验通道号是否在 0–15。

        Args:
            channel (int): 通道号。

        Raises:
            ValueError: 通道号不是0–15通道。

        ==========================================
        Ensure channel index in 0–15.

        Args:
            channel (int): Channel index.

        Raises:
            ValueError: The channel number is not in the 0–15 range.
        """
        if not isinstance(channel, int) or not (0 <= channel <= 15):
            raise ValueError("channel must be int in 0..15")

    def _ensure_attached(self, channel):
        """
        确保通道已注册。

        Args:
            channel (int): 通道号。

        Raises:
            ValueError: 未注册的通道号。

        ==========================================
        Ensure channel is attached.

        Args:
            channel (int): Channel index.

        Raises:
            ValueError: Unregistered channel number.
        """
        if channel not in self._cfg:
            raise ValueError("channel {} not attached; call attach_servo() first".format(channel))

    def _clip(self, x, lo, hi):
        """
        限幅。

        Args:
            x (float): 输入值。
            lo (float): 下界。
            hi (float): 上界。

        Returns:
            float: 限幅后。

        ==========================================
        Clamp value.

        Args:
            x (float): Input.
            lo (float): Lower.
            hi (float): Upper.

        Returns:
            float: Clamped.
        """
        return max(lo, min(hi, x))

    def to_pwm_ticks(self, pulse_us):
        """
        微秒脉宽转 tick。

        Args:
            pulse_us (int): 脉宽（µs）。

        Returns:
            int: tick 值。

        Raises:
            ValueError: pulse_us 为非正数（≤ 0）。

        ==========================================
        Convert pulse width (µs) to ticks.

        Args:
            pulse_us (int): Pulse width.

        Returns:
            int: Tick value.

        Raises:
            ValueError: pulse_us is a non-positive number (≤ 0).
        """
        if not isinstance(pulse_us, int) or pulse_us <= 0:
            raise ValueError("pulse_us must be positive int")
        period_us = 1000000.0 / float(self._freq)
        duty = pulse_us / period_us
        ticks = int(round(self._clip(duty, 0.0, 1.0) * 4095.0))
        return self._clip(ticks, 0, 4095)

    def _write_pulse(self, channel, pulse_us):
        """
        写脉宽到指定通道。

        Args:
            channel (int): 通道号。
            pulse_us (int): 脉宽（微秒，µs）。必须为正数。

        Raises:
            ValueError:  pulse_us 为非正数（< 0）。
            RuntimeError: PCA9685 IIC 操作失败。

        ==========================================
        Write pulse width to the specified channel.

        Args:
            channel (int): Channel number.
            pulse_us (int): Pulse width in microseconds (µs). Must be a positive number.

        Raises:
            ValueError: pulse_us is non-positive (≤ 0).
            RuntimeError: PCA9685 I/O operation fails.
        """
        # 显式检查 pulse_us 是否为正数
        if pulse_us < 0:
            raise ValueError("pulse_us must be a positive number (greater than 0).")

        try:
            ticks = self.to_pwm_ticks(pulse_us)
            self._pca.duty(channel, ticks)
        except Exception as e:
            raise RuntimeError("PCA9685 I/O failed") from e

    def attach_servo(self, channel, servo_type=0, *, min_us=500, max_us=2500, neutral_us=1500, reversed=False):
        """
        注册通道与校准参数。

        Args:
            channel (int): 通道号。
            servo_type (int): 舵机类型。应为 `SERVO_180` 或 `SERVO_360`。
            min_us (int): 最小脉宽，必须是正整数且小于最大脉宽。
            max_us (int): 最大脉宽，必须是正整数且大于最小脉宽。
            neutral_us (int|None): 中立脉宽，必须是 `min_us` 和 `max_us` 之间的整数，或者为 `None`。
            reversed (bool): 是否反向控制。

        Raises:
            ValueError: 如果参数无效，详细错误信息如下：
                - servo_type 不是 `SERVO_180` 或 `SERVO_360`。
                - min_us 和 max_us 必须为正整数，并且 min_us 小于 max_us。
                - neutral_us 必须是整数，且在 `min_us` 和 `max_us` 之间，或者为 `None`。

        ==========================================
        Attach servo and calibration.

        Args:
            channel (int): Channel number.
            servo_type (int): Servo type. Must be `SERVO_180` or `SERVO_360`.
            min_us (int): Min pulse width, must be a positive integer and less than max_us.
            max_us (int): Max pulse width, must be a positive integer and greater than min_us.
            neutral_us (int|None): Neutral pulse width, must be an integer within [min_us, max_us] or None.
            reversed (bool): Reverse control.

        Raises:
            ValueError: If invalid parameters are provided, detailed error messages as follows:
                - `servo_type` must be `SERVO_180` or `SERVO_360`.
                - `min_us` and `max_us` must be positive integers, and `min_us` must be less than `max_us`.
                - `neutral_us` must be an integer within the range of [min_us, max_us] or None.
        """
        self._ensure_channel(channel)

        # 检查舵机类型
        if servo_type not in (self.SERVO_180, self.SERVO_360):
            raise ValueError("servo_type must be either SERVO_180 or SERVO_360, got {}".format(servo_type))

        # 检查 min_us 和 max_us
        if not (isinstance(min_us, int) and isinstance(max_us, int) and min_us > 0 and max_us > 0 and min_us < max_us):
            raise ValueError(
                "min_us and max_us must be positive integers and min_us must be less than max_us. Got min_us={}, max_us={}".format(
                    min_us, max_us))

        # 检查 neutral_us
        if neutral_us is not None:
            if not isinstance(neutral_us, int):
                raise ValueError("neutral_us must be an integer if specified. Got neutral_us={}".format(neutral_us))
            if not (min_us <= neutral_us <= max_us):
                raise ValueError(
                    "neutral_us must be in the range [min_us, max_us]. Got neutral_us={}, min_us={}, max_us={}".format(
                        neutral_us, min_us, max_us))

        # 配置舵机
        self._cfg[channel] = {
            "type": servo_type,
            "min": min_us,
            "max": max_us,
            "neutral": neutral_us,
            "rev": bool(reversed),
            "angle": None,
        }

    def detach_servo(self, channel):
        """
        取消注册并停止输出。

        Args:
            channel (int): 通道号。

        Raises:
            RuntimeError: 如果写入 PCA9685 时失败。
            ValueError: 如果给定的通道无效（不存在或未注册）。

        ==========================================
        Detach and stop output.

        Args:
            channel (int): Channel number.

        Raises:
            RuntimeError: If writing to PCA9685 fails.
            ValueError: If the provided channel is invalid (not registered or does not exist).
        """
        # 确保通道有效
        self._ensure_channel(channel)

        try:
            # 停止输出，通过将 duty 设置为 0
            self._pca.duty(channel, 0)
        except Exception as e:
            raise RuntimeError("PCA9685 I/O failed while stopping output on channel {}".format(channel)) from e

        # 移除通道的配置
        if channel not in self._cfg:
            raise ValueError("Channel {} is not registered or invalid.".format(channel))

        self._cfg.pop(channel, None)

    def set_angle(self, channel, angle, *, speed_deg_per_s=None):
        """
        设置 180° 舵机角度。

        Args:
            channel (int): 通道号。
            angle (float): 角度 0–180。
            speed_deg_per_s (float|None): 平滑速度。

        Raises:
            ValueError: 如果参数非法（如角度不在0–180范围内，或非数值类型）。
            RuntimeError: 如果类型不符（如非 SERVO_180 类型的舵机）或写入失败。

        ==========================================
        Set 180° servo angle.

        Args:
            channel (int): Channel number.
            angle (float): Angle 0–180.
            speed_deg_per_s (float|None): Smoothing speed.

        Raises:
            ValueError: If invalid parameters are provided (e.g., angle out of range, or not a number).
            RuntimeError: If the type is not `SERVO_180` or write fails.
        """
        self._ensure_channel(channel)
        self._ensure_attached(channel)
        cfg = self._cfg[channel]

        # 确保舵机类型是 SERVO_180
        if cfg["type"] != self.SERVO_180:
            raise RuntimeError("Channel {} is not SERVO_180, it is {}".format(channel, cfg["type"]))

        # 检查 angle 是否为有效的数值
        if not isinstance(angle, (int, float)):
            raise ValueError("Angle must be a number, got {}".format(type(angle)))

        # 限制角度范围
        angle = self._clip(float(angle), 0.0, 180.0)
        min_us, max_us = cfg["min"], cfg["max"]

        # 如果是反向，调整角度
        if cfg["rev"]:
            angle = 180.0 - angle

        pulse = int(round(min_us + (max_us - min_us) * (angle / 180.0)))

        # 如果没有平滑速度，直接设置脉宽
        if speed_deg_per_s is None or cfg.get("angle") is None or speed_deg_per_s <= 0:
            self._write_pulse(channel, pulse)
            cfg["angle"] = 180.0 - angle if cfg["rev"] else angle

        # 处理平滑角度变化
        current = cfg.get("angle", angle)
        target = 180.0 - angle if cfg["rev"] else angle

        if current == target:
            return

        step = max(0.5, float(speed_deg_per_s) * 0.02)
        direction = 1.0 if target > current else -1.0
        a = current

        while (direction > 0 and a < target) or (direction < 0 and a > target):
            a += direction * step
            tmp_angle = self._clip(a, 0.0, 180.0)
            phys_angle = 180.0 - tmp_angle if cfg["rev"] else tmp_angle
            pulse_i = int(round(min_us + (max_us - min_us) * (phys_angle / 180.0)))
            self._write_pulse(channel, pulse_i)
            time.sleep_ms(20)

        # 最后一次脉宽写入
        self._write_pulse(channel, pulse)
        cfg["angle"] = target

    def set_speed(self, channel, speed):
        """
        设置 360° 舵机速度。

        Args:
            channel (int): 通道号。
            speed (float): 速度 -1.0~1.0。

        Raises:
            ValueError: 如果速度不在有效范围内或参数非法。
            RuntimeError: 如果舵机类型不符或写入失败。

        ==========================================
        Set 360° servo speed.

        Args:
            channel (int): Channel number.
            speed (float): Speed -1.0~1.0.

        Raises:
            ValueError: If the speed is not in the valid range or invalid parameters are provided.
            RuntimeError: If the servo type is not `SERVO_360` or writing to the servo fails.
        """
        self._ensure_channel(channel)
        self._ensure_attached(channel)
        cfg = self._cfg[channel]

        # 确保舵机类型是 SERVO_360
        if cfg["type"] != self.SERVO_360:
            raise RuntimeError("Channel {} is not a 360° servo (SERVO_360)".format(channel))

        # 检查 speed 是否为有效数值
        if not isinstance(speed, (int, float)):
            raise ValueError("Speed must be a number, got {}".format(type(speed)))

        # 限制速度范围
        speed = self._clip(float(speed), -1.0, 1.0)

        # 如果是反向舵机，改变速度符号
        if cfg["rev"]:
            speed = -speed

        min_us, max_us = cfg["min"], cfg["max"]
        neutral = cfg["neutral"] if cfg["neutral"] is not None else (min_us + max_us) // 2

        # 根据速度计算脉宽
        if speed == 0.0:
            pulse = int(neutral)
        elif speed > 0.0:
            pulse = int(round(neutral + (max_us - neutral) * speed))
        else:
            pulse = int(round(neutral + (neutral - min_us) * speed))

        self._write_pulse(channel, pulse)

    def set_pulse_us(self, channel, pulse_us):
        """
        直接写脉宽（µs）。

        Args:
            channel (int): 通道号。
            pulse_us (int): 脉宽。

        Raises:
            ValueError: pulse_us 为非正数（≤ 0）。

        ==========================================
        Write pulse width (µs) directly.

        Args:
            channel (int): pulse_us is a non-positive number (≤ 0).
            pulse_us (int): Pulse width.

        Raises:
            ValueError: pulse_us is a non-positive number (≤ 0).
        """
        self._ensure_channel(channel)
        self._ensure_attached(channel)

        # 检查 pulse_us 是否为正整数
        if not isinstance(pulse_us, int) or pulse_us <= 0:
            raise ValueError("pulse_us must be a positive integer, got {}".format(pulse_us))

        cfg = self._cfg[channel]

        # 限制脉宽在最小和最大值范围内
        pulse_us = int(self._clip(pulse_us, cfg["min"], cfg["max"]))

        # 写入脉宽
        self._write_pulse(channel, pulse_us)

    def stop(self, channel):
        """
        停止输出或回中。

        Args:
            channel (int): 通道号。

        Raises:
            RuntimeError: 写入失败。

        ==========================================
        Stop output or set to neutral.

        Args:
            channel (int): Channel number.

        Raises:
            RuntimeError: writing to the PCA9685 fails.
        """
        self._ensure_channel(channel)
        self._ensure_attached(channel)
        cfg = self._cfg[channel]
        neutral = cfg.get("neutral")

        try:
            if neutral is None:
                # 如果没有中立脉宽，停止输出
                self._pca.duty(channel, 0)
            else:
                # 设置为中立脉宽
                self._write_pulse(channel, int(neutral))
        except Exception as e:
            raise RuntimeError("PCA9685 I/O failed while stopping output on channel {}".format(channel)) from e

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================