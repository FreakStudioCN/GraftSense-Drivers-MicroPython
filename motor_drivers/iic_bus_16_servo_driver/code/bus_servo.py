# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/09/04 10:00
# @Author  : 侯钧瀚
# @File    : bus_servo.py
# @Description : PCA9685 16路 PWM 驱动 for MicroPython
# @Repository  : https://github.com/FreakStudioCN/GraftSense-Drivers-MicroPython
# @License : CCBYNC

__version__ = "0.1.0"
__author__ = "侯钧瀚"
__license__ = "CCBYNC"
__platform__ = "MicroPython v1.19+"

# ======================================== 导入相关模块 =========================================

# 导入时间相关模块
import time

# 导入const
from micropython import const

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class BusPWMServoController:
    """
    基于 PCA9685 的 16 路 PWM 舵机控制器，支持 180° 舵机角度控制、360° 连续舵机速度控制，以及脉宽直接写入。
    通过注册通道与校准参数，可灵活实现舵机的绑定、运动与停止控制。

    Class Variables:
        SERVO_180 (int): 180° 舵机类型常量。
        SERVO_360 (int): 360° 连续旋转舵机类型常量。

    Attributes:
        _pca (PCA9685): 控制 PWM 信号输出的 PCA9685 实例。
        _freq (int): PWM 输出频率（Hz），舵机常用 50Hz。
        _cfg (dict): 各通道配置字典（类型、脉宽范围、中立值、反向标志、当前角度等）。

    Methods:
        __init__(pca, freq=50) -> None: 构造并设置输出频率。
        attach_servo(...): 注册/配置指定通道，不移动舵机。
        detach_servo(channel) -> None: 取消注册并停止输出。
        set_angle(...): 针对 180° 舵机设置角度，可选平滑速度。
        set_speed(...): 针对 360° 舵机设置速度（-1..+1）。
        set_pulse_us(channel, pulse_us) -> None: 直接写入脉宽（µs）。
        stop(channel) -> None: 回中或关闭输出。
        to_pwm_ticks(pulse_us) -> int: 将 µs 转为 PCA9685 tick 值（0–4095）。
    ==============
    A 16-channel PWM servo controller based on PCA9685. Supports 180° positional servos,
    360° continuous servos (speed control), and direct pulse-width writes. By registering
    channels with calibration parameters, you can flexibly bind servos and control move/stop.

    Class Variables:
        SERVO_180 (int): Constant for 180° positional servos.
        SERVO_360 (int): Constant for 360° continuous rotation servos.

    Attributes:
        _pca (PCA9685): PCA9685 instance driving PWM signals.
        _freq (int): PWM output frequency in Hz (50 Hz is typical for servos).
        _cfg (dict): Per-channel config dict (type, pulse range, neutral, reverse flag, current angle, etc.).

    Methods:
        __init__(pca, freq=50) -> None: Construct and set output frequency.
        attach_servo(...): Register/configure a channel without moving the servo.
        detach_servo(channel) -> None: Unregister and stop output.
        set_angle(...): Set angle for 180° servo with optional smoothing speed.
        set_speed(...): Set speed (-1..+1) for 360° continuous servo.
        set_pulse_us(channel, pulse_us) -> None: Write pulse width (µs) directly.
        stop(channel) -> None: Return to neutral or disable output.
        to_pwm_ticks(pulse_us) -> int: Convert µs to PCA9685 tick value (0–4095).
    """

    SERVO_180 = const(0x00)
    SERVO_360 = const(0x01)

    def __init__(self, pca, freq=50):
        """
        构造函数，保存传入的 PCA9685 实例并设置 PWM 频率（Hz）。不做耗时 I/O。

        Args:
            pca (object): 兼容 `freq(hz)`、`duty(channel, value)`（可选 `reset()`）方法的 PCA9685 实例。
            freq (int): PWM 频率（Hz），通常为 50Hz。

        Raises:
            ValueError: 传入的 `pca` 不符合接口要求，或 `freq` 非正整数。
            RuntimeError: 设置 PCA9685 频率失败。
        ==============
        Constructor that stores the given PCA9685 instance and sets the PWM frequency (Hz).
        No time-consuming I/O is performed.

        Args:
            pca (object): PCA9685-like object with `freq(hz)`, `duty(channel, value)`, and optional `reset()`.
            freq (int): PWM frequency in Hz, typically 50 Hz.

        Raises:
            ValueError: If `pca` lacks required methods or `freq` is not a positive integer.
            RuntimeError: If setting the PCA9685 frequency fails.
        """

        if not hasattr(pca, "freq") or not hasattr(pca, "duty"):
            raise ValueError("pca object must provide freq(hz) and duty(channel, value) methods")

        if not isinstance(freq, int) or freq <= 0:
            raise ValueError("freq must be a positive integer")

        self._pca = pca
        self._freq = freq
        # 设置 PCA9685 输出频率
        try:
            self._pca.reset() if hasattr(self._pca, "reset") else None
            self._pca.freq(freq)
        except Exception as e:
            raise RuntimeError("Failed to set PCA9685 frequency") from e

        # 每个通道的配置与状态
        self._cfg = {}

    def _ensure_channel(self, channel):
        """
        校验通道号是否在 0–15 范围内。

        Args:
            channel (int): PCA9685 通道编号。

        Raises:
            ValueError: 当通道不是整型或不在 0–15 时抛出。
        ==============
        Validate that channel index is in the range 0–15.

        Args:
            channel (int): PCA9685 channel number.

        Raises:
            ValueError: If channel is not an int or is outside 0–15.
        """

        if not isinstance(channel, int) or not (0 <= channel <= 15):
            raise ValueError("channel must be an int in 0..15")

    def _ensure_attached(self, channel):
        """
        确保通道已通过 attach_servo() 绑定。

        Args:
            channel (int): PCA9685 通道编号。

        Raises:
            ValueError: 当通道未绑定时抛出。
        ==============
        Ensure the channel has been registered via attach_servo().

        Args:
            channel (int): PCA9685 channel number.

        Raises:
            ValueError: If the channel is not attached.
        """

        if channel not in self._cfg:
            raise ValueError("channel {} not attached; call attach_servo() first".format(channel))

    def _clip(self, x, lo, hi):
        """
        将值限制在区间 [lo, hi] 内。

        Args:
            x (float): 输入值。
            lo (float): 下界。
            hi (float): 上界。

        Returns:
            float: 限幅后的数值。
        ==============
        Clamp a value into the interval [lo, hi].

        Args:
            x (float): Input value.
            lo (float): Lower bound.
            hi (float): Upper bound.

        Returns:
            float: Clamped value.
        """

        return lo if x < lo else (hi if x > hi else x)

    def to_pwm_ticks(self, pulse_us):
        """
        将微秒脉宽转换为 PCA9685 的 tick（0–4095），基于当前频率。

        Args:
            pulse_us (int): 输入的脉宽（微秒），必须为正整数。

        Returns:
            int: 转换后的 tick 值，范围 0–4095。

        Raises:
            ValueError: 当 `pulse_us` 非正整数时抛出。
        ==============
        Convert pulse width in microseconds to PCA9685 ticks (0–4095), based on current frequency.

        Args:
            pulse_us (int): Pulse width in microseconds; must be a positive integer.

        Returns:
            int: Tick value in the range 0–4095.

        Raises:
            ValueError: If `pulse_us` is not a positive integer.
        """

        if not isinstance(pulse_us, int) or pulse_us <= 0:
            raise ValueError("pulse_us must be a positive int")
        # 一个周期（微秒）= 1e6 / freq ============== # One period (µs) = 1e6 / freq
        period_us = 1000000.0 / float(self._freq)
        # 占空比（0..1） -> ticks（0..4095），与 pca.duty 的“value”一致
        duty = pulse_us / period_us
        ticks = int(round(self._clip(duty, 0.0, 1.0) * 4095.0))
        if ticks < 0:
            ticks = 0
        elif ticks > 4095:
            ticks = 4095
        return ticks

    def _write_pulse(self, channel, pulse_us):
        """
        以微秒写入指定通道，内部转换为 PCA9685 的 tick 并下发。

        Args:
            channel (int): PCA9685 通道编号（0–15）。
            pulse_us (int): 脉宽（微秒）。

        Raises:
            RuntimeError: 底层 PCA9685 写入失败时抛出。
        ==============
        Write pulse width (µs) to a channel; internally converts to PCA9685 ticks and sends.

        Args:
            channel (int): PCA9685 channel index (0–15).
            pulse_us (int): Pulse width in microseconds.

        Raises:
            RuntimeError: If the underlying PCA9685 I/O fails.
        """

        try:
            ticks = self.to_pwm_ticks(pulse_us)
            self._pca.duty(channel, ticks)
        except Exception as e:
            raise RuntimeError("PCA9685 I/O failed") from e


    def attach_servo(
        self,
        channel,
        servo_type=0,
        *,
        min_us=500,
        max_us=2500,
        neutral_us=1500,
        reversed=False
    ):
        """
        注册/配置指定通道的舵机与校准参数（µs），不立即移动舵机。

        Args:
            channel (int): PCA9685 通道编号（0–15）。
            servo_type (int): 舵机类型，`SERVO_180` 或 `SERVO_360`。
            min_us (int): 最小脉宽（µs）。
            max_us (int): 最大脉宽（µs）。
            neutral_us (Optional[int]): 中立脉宽（µs），可为 None。
            reversed (bool): 是否反向控制（True 时角度/速度方向相反）。

        Raises:
            ValueError: 任一参数无效（类型/范围错误）。
        ==============
        Register/configure a servo on a channel with calibration (µs), without moving it.

        Args:
            channel (int): PCA9685 channel (0–15).
            servo_type (int): Servo type: `SERVO_180` or `SERVO_360`.
            min_us (int): Minimum pulse width (µs).
            max_us (int): Maximum pulse width (µs).
            neutral_us (int|None): Neutral pulse (µs), or None.
            reversed (bool): Reverse control direction (angle/speed inverted when True).

        Raises:
            ValueError: If any parameter is invalid (type/range).
        """

        self._ensure_channel(channel)
        if servo_type not in (self.SERVO_180, self.SERVO_360):
            raise ValueError("servo_type must be SERVO_180 or SERVO_360")
        if not (isinstance(min_us, int) and isinstance(max_us, int) and min_us > 0 and max_us > 0 and min_us < max_us):
            raise ValueError("min_us/max_us must be positive ints and min_us < max_us")
        if neutral_us is not None:
            if not isinstance(neutral_us, int) or not (min_us <= neutral_us <= max_us):
                raise ValueError("neutral_us must be int in [min_us, max_us] or None")

        self._cfg[channel] = {
            "type": servo_type,
            "min": min_us,
            "max": max_us,
            "neutral": neutral_us,
            "rev": bool(reversed),
            # 仅对 180° 舵机使用的“当前角度”缓存（None 表示未知）
            "angle": None,
        }

    def detach_servo(self, channel):
        """
        取消该通道注册并停止输出（将 PWM 置 0）。

        Args:
            channel (int): PCA9685 通道编号（0–15）。

        Raises:
            RuntimeError: 底层 PCA9685 写入失败。
            ValueError: 通道编号无效。
        ==============
        Unregister the channel and stop output (set PWM to 0).

        Args:
            channel (int): PCA9685 channel (0–15).

        Raises:
            RuntimeError: Underlying PCA9685 write failed.
            ValueError: Invalid channel number.
        """

        self._ensure_channel(channel)
        # 停止输出 ============== # Stop output
        try:
            self._pca.duty(channel, 0)
        except Exception as e:
            raise RuntimeError("PCA9685 I/O failed") from e
        # 移除配置 ============== # Remove configuration
        self._cfg.pop(channel, None)

    def set_angle(self, channel, angle, *, speed_deg_per_s=None):
        """
        针对 `SERVO_180`（180°）设置目标角度（0.0–180.0）。可选 `speed_deg_per_s` 平滑移动。

        Args:
            channel (int): PCA9685 通道编号（0–15）。
            angle (float): 目标角度，范围 0–180°。超出范围将被限幅。
            speed_deg_per_s (Optional[float]): 平滑移动速度（度/秒）。为 None 或 <=0 时直接跳转。

        Raises:
            ValueError: 参数类型错误或未绑定通道。
            RuntimeError: 指定通道不是 `SERVO_180`，或底层写入失败。
        ==============
        Set the target angle (0.0–180.0) for a `SERVO_180`. Optional smoothing via `speed_deg_per_s`.

        Args:
            channel (int): PCA9685 channel (0–15).
            angle (float): Target angle in degrees (0–180); values are clamped.
            speed_deg_per_s (float|None): Smoothing speed in deg/s. If None or <=0, jump directly.

        Raises:
            ValueError: Invalid parameter type or channel not attached.
            RuntimeError: Channel is not `SERVO_180`, or write failed.
        """

        self._ensure_channel(channel)
        self._ensure_attached(channel)
        cfg = self._cfg[channel]
        if cfg["type"] != self.SERVO_180:
            raise RuntimeError("channel {} is not SERVO_180".format(channel))

        if not isinstance(angle, (int, float)):
            raise ValueError("angle must be a number")
        angle = float(angle)
        angle = self._clip(angle, 0.0, 180.0)

        # 角度->脉宽映射（线性）。 ============== # Angle-to-pulse mapping (linear).
        min_us, max_us = cfg["min"], cfg["max"]
        if cfg["rev"]:
            angle = 180.0 - angle
        pulse = int(round(min_us + (max_us - min_us) * (angle / 180.0)))

        if speed_deg_per_s is None or cfg.get("angle") is None or speed_deg_per_s <= 0:
            # 直接落位 ============== # Jump directly to position
            self._write_pulse(channel, pulse)
            cfg["angle"] = 180.0 - angle if cfg["rev"] else angle  # 缓存“人眼角度”
            return

        # 平滑移动：以固定时间步进角度 ============== # Smooth move: step angle at fixed time intervals
        current = cfg.get("angle", angle)  # 若未知，则直接跳 ============== # If unknown, jump directly
        target = 180.0 - angle if cfg["rev"] else angle  # 以“人眼角度”作为轨迹变量
        if current == target:
            return

        step = max(0.5, float(speed_deg_per_s) * 0.02)  # 每 20ms 的角度步长；至少 0.5°
        direction = 1.0 if target > current else -1.0
        a = current
        while (direction > 0 and a < target) or (direction < 0 and a > target):
            a += direction * step
            # 计算对应脉宽（先考虑反向标志，再映射到物理脉宽）
            tmp_angle = self._clip(a, 0.0, 180.0)
            phys_angle = 180.0 - tmp_angle if cfg["rev"] else tmp_angle
            pulse_i = int(round(min_us + (max_us - min_us) * (phys_angle / 180.0)))
            self._write_pulse(channel, pulse_i)
            time.sleep_ms(20)
        # 最后一拍对齐目标 ============== # Final write to align with target
        self._write_pulse(channel, pulse)
        cfg["angle"] = target

    def set_speed(self, channel, speed):
        """
        针对 `SERVO_360`（连续舵机）按归一化速度控制，`speed` ∈ [-1.0, 1.0]（0 停止）。

        Args:
            channel (int): PCA9685 通道编号（0–15）。
            speed (float): 归一化速度，-1.0（满反转）到 +1.0（满正转），0 为停止。

        Raises:
            ValueError: 参数类型错误或未绑定通道。
            RuntimeError: 指定通道不是 `SERVO_360`，或底层写入失败。
        ==============
        Control a `SERVO_360` (continuous) by normalized speed, `speed` ∈ [-1.0, 1.0] (0 stops).

        Args:
            channel (int): PCA9685 channel (0–15).
            speed (float): Normalized speed: -1.0 (full reverse) to +1.0 (full forward), 0 to stop.

        Raises:
            ValueError: Invalid parameter type or channel not attached.
            RuntimeError: Channel is not `SERVO_360`, or write failed.
        """

        self._ensure_channel(channel)
        self._ensure_attached(channel)
        cfg = self._cfg[channel]
        if cfg["type"] != self.SERVO_360:
            raise RuntimeError("channel {} is not SERVO_360".format(channel))

        if not isinstance(speed, (int, float)):
            raise ValueError("speed must be a number")
        speed = float(speed)
        speed = self._clip(speed, -1.0, 1.0)
        if cfg["rev"]:
            speed = -speed

        min_us, max_us = cfg["min"], cfg["max"]
        neutral = cfg["neutral"]
        if neutral is None:
            # 没有中立值则按[min,max]线性映射：0 -> (min+max)/2
            neutral = (min_us + max_us) // 2

        if speed == 0.0:
            pulse = int(neutral)
        elif speed > 0.0:
            pulse = int(round(neutral + (max_us - neutral) * speed))
        else:
            pulse = int(round(neutral + (neutral - min_us) * speed))  # speed<0

        self._write_pulse(channel, pulse)

    def set_pulse_us(self, channel, pulse_us):
        """
        以微秒直接写脉宽到指定通道（不做角度/速度映射），受 `min_us/max_us` 限制。

        Args:
            channel (int): PCA9685 通道编号（0–15）。
            pulse_us (int): 脉宽（µs），写入前会被限幅到该通道配置区间。

        Raises:
            ValueError: 参数无效或通道未绑定。
            RuntimeError: 底层写入失败。
        ==============
        Write pulse width in microseconds directly to the channel (no angle/speed mapping),
        clamped by `min_us/max_us`.

        Args:
            channel (int): PCA9685 channel (0–15).
            pulse_us (int): Pulse width (µs); will be clamped to the channel’s configured range.

        Raises:
            ValueError: Invalid parameter or channel not attached.
            RuntimeError: Underlying write failed.
        """

        self._ensure_channel(channel)
        self._ensure_attached(channel)
        if not isinstance(pulse_us, int) or pulse_us <= 0:
            raise ValueError("pulse_us must be positive int")
        cfg = self._cfg[channel]
        pulse_us = int(self._clip(pulse_us, cfg["min"], cfg["max"]))
        self._write_pulse(channel, pulse_us)

    def stop(self, channel):
        """
        停止该通道：若存在 `neutral_us` 则置为中立，否则完全关闭输出（`duty=0`）。

        Args:
            channel (int): PCA9685 通道编号（0–15）。

        Raises:
            ValueError: 通道未绑定或编号无效。
            RuntimeError: 底层写入失败。
        ==============
        Stop a channel: if `neutral_us` exists, set to neutral; otherwise, fully disable output (`duty=0`).

        Args:
            channel (int): PCA9685 channel (0–15).

        Raises:
            ValueError: Channel not attached or invalid index.
            RuntimeError: Underlying write failed.
        """

        self._ensure_channel(channel)
        self._ensure_attached(channel)
        cfg = self._cfg[channel]
        neutral = cfg.get("neutral")
        try:
            if neutral is None:
                self._pca.duty(channel, 0)  # 关闭输出
            else:
                self._write_pulse(channel, int(neutral))  # 回中立
        except Exception as e:
            raise RuntimeError("PCA9685 I/O failed") from e

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
