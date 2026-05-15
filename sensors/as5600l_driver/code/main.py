# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/05/15
# @Author  : hogeiha
# @File    : main.py
# @Description : 测试 AS5600/AS5600L 12位磁性旋转编码器驱动类
# @License : MIT

__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# 时间相关接口
import time
# I2C 总线
from machine import I2C, Pin
# AS5600 驱动
from as5600 import AS5600

# ======================================== 全局变量 ============================================

# I2C 总线参数
I2C_ID = 0
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 400000

# AS5600L 默认地址（AS5600 标准件为 0x36）
AS5600_ADDR = 0x40

# AS5600 无 WHO_AM_I 寄存器，使用 STATUS 寄存器作为设备响应验证
DEVICE_VERIFY_REG = 0x1B
# STATUS 寄存器仅有效位为 bit5/bit4/bit3，其余位为 0
DEVICE_VERIFY_MASK = 0xC7
DEVICE_VERIFY_EXPECTED = 0x00

# 主循环打印间隔（毫秒）
PRINT_INTERVAL_MS = 1000
last_print_time = time.ticks_ms()

# ======================================== 功能函数 ============================================

def print_realtime_angle():
    """高频读取实时角度（默认注释执行，可在 REPL 手动调用）"""
    # 读取原始与映射角度
    raw = sensor.rawangle()
    mapped = sensor.angle()
    # 12 位分辨率换算为度
    print("Raw: %d  Angle: %d  (%.2f deg)" % (raw, mapped, mapped * 360.0 / 4096.0))


def print_status():
    """打印磁铁状态、AGC 与磁场强度"""
    # 磁铁检测三态
    md = sensor.md()
    ml = sensor.ml()
    mh = sensor.mh()
    # 自动增益与磁场强度
    agc = sensor.agc()
    mag = sensor.magnitude()
    print("Magnet: detected=%d weak=%d strong=%d  AGC=%d  Magnitude=%d"
          % (md, ml, mh, agc, mag))


def print_config():
    """打印当前配置寄存器（ZMCO/ZPOS/MPOS/MANG/CONF 各位域）"""
    # 烧录次数
    zmco = sensor.zmco()
    # 角度映射相关
    zpos = sensor.zpos()
    mpos = sensor.mpos()
    mang = sensor.mang()
    # CONF 寄存器拆位
    pm = sensor.pm()
    hyst = sensor.hyst()
    outs = sensor.outs()
    pwmf = sensor.pwmf()
    sf = sensor.sf()
    fth = sensor.fth()
    wd = sensor.watchdog()
    print("ZMCO=%d ZPOS=%d MPOS=%d MANG=%d" % (zmco, zpos, mpos, mang))
    print("CONF: PM=%d HYST=%d OUTS=%d PWMF=%d SF=%d FTH=%d WD=%d"
          % (pm, hyst, outs, pwmf, sf, fth, wd))


def test_boundary_write():
    """边界参数场景：ZPOS 写入 0 与 4095（12 位最小/最大）"""
    # 写入最小值
    sensor.zpos(0)
    v0 = sensor.zpos()
    # 写入最大值
    sensor.zpos(4095)
    v1 = sensor.zpos()
    print("Boundary ZPOS write: 0 -> %d, 4095 -> %d" % (v0, v1))


def test_invalid_args():
    """异常参数场景：验证非法参数能正确抛出 ValueError"""
    # 非法寄存器地址
    try:
        sensor.readwrite(0x100, 7, 0)
    except ValueError as e:
        print("Caught register out-of-range: %s" % e)
    # 非法位域
    try:
        sensor.readwrite(0x07, 3, 5)
    except ValueError as e:
        print("Caught invalid bitfield: %s" % e)
    # 写入超出位域范围
    try:
        sensor.zpos(0x10000)
    except ValueError as e:
        print("Caught value out-of-range: %s" % e)
    # 错误类型
    try:
        sensor.zpos("bad")
    except ValueError as e:
        print("Caught wrong type: %s" % e)


def burn_angle_once():
    """烧录角度（ZPOS/MPOS）到 OTP，不可逆，仅 REPL 手动触发"""
    sensor.burn_angle()
    print("burn_angle issued")


def burn_setting_once():
    """烧录配置（MANG/CONF）到 OTP，不可逆，仅 REPL 手动触发"""
    sensor.burn_setting()
    print("burn_setting issued")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio: AS5600/AS5600L magnetic encoder driver test")

# 初始化 I2C 总线
i2c = I2C(I2C_ID, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 扫描 I2C 总线
devices = i2c.scan()
if not devices:
    raise RuntimeError("No I2C device found")
print("I2C scan result: %s" % [hex(d) for d in devices])

# 验证目标地址在线
if AS5600_ADDR not in devices:
    raise RuntimeError("Device not found at expected address 0x%02X" % AS5600_ADDR)
print("Target device 0x%02X present on bus" % AS5600_ADDR)

# 设备响应验证（AS5600 无 WHO_AM_I，改读 STATUS 寄存器并按掩码比对保留位）
_probe = i2c.readfrom_mem(AS5600_ADDR, DEVICE_VERIFY_REG, 1)[0]
if (_probe & ~DEVICE_VERIFY_MASK) == DEVICE_VERIFY_EXPECTED:
    print("Device found (STATUS=0x%02X)" % _probe)
else:
    print("Device not found (STATUS=0x%02X, unexpected reserved bits)" % _probe)

# 创建驱动实例
sensor = AS5600(i2c, device=AS5600_ADDR, debug=False)

# ========================================  主程序  ===========================================

try:
    # 启动时打印一次配置与状态
    print_config()
    print_status()
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= PRINT_INTERVAL_MS:
            # 低频核心采集：角度 + 状态
            raw = sensor.rawangle()
            mapped = sensor.angle()
            md = sensor.md()
            print("Angle raw=%d mapped=%d (%.2f deg)  magnet=%d"
                  % (raw, mapped, mapped * 360.0 / 4096.0, md))
            last_print_time = current_time
        # print_realtime_angle()   # 高频角度读取，默认注释，REPL 手动调用
        # print_status()           # 状态/AGC/magnitude，默认注释，REPL 手动调用
        # print_config()           # 配置回读，默认注释，REPL 手动调用
        # test_boundary_write()    # 边界参数，默认注释，REPL 手动调用
        # test_invalid_args()      # 异常参数，默认注释，REPL 手动调用
        # burn_angle_once()        # OTP 烧录不可逆，仅 REPL 手动触发
        # burn_setting_once()      # OTP 烧录不可逆，仅 REPL 手动触发
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("Program interrupted by user")
except OSError as e:
    print("Hardware communication error: %s" % str(e))
except Exception as e:
    print("Unknown error: %s" % str(e))
finally:
    print("Cleaning up resources...")
    try:
        sensor.deinit()
    except Exception:
        pass
    del sensor
    print("Program exited")
