# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 上午11:42
# @Author  : 缪贵成
# @File    : main.py
# @Description : 五向按键测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time
from pcf8574 import PCF8574
from pcf8574keys import PCF8574Keys, KEYS_MAP

# ======================================== 全局变量 ============================================

# I2C配置
I2C_ID = 0
# 根据实际硬件修改
SCL_PIN = 5
# 根据实际硬件修改
SDA_PIN = 4

PCF8574_ADDR = None



# ======================================== 功能函数 ============================================

def key_callback(key_name, state):
    """
    按键事件回调函数，当按键状态发生变化时调用此函数。

    Args:
        key_name (str): 按键名称或标识符，用于区分不同按键。
        state (bool): 按键状态，True 表示按下，False 表示释放。

    Raises:
        TypeError: 当key_name不是str类型或者state不是bool类型抛出异常。
        ValueError: 当key_name不在 KEYS_MAP 中时抛出。

    ===========================================

    Key event callback function, this function is called when the key state changes.

    Args:
        key_name (str): The name or identifier of the key, used to differentiate between different keys.
        state (bool): The key state, True indicates pressed, False indicates released.

    Raises:
        TypeError: Throw an exception when key_name is not of type str or state is not of type bool.
        ValueError: Raised when key_name is not defined in KEYS_MAP.
    """
    # 参数校验
    if not isinstance(key_name, str):
        raise TypeError(f"key_name must be a str, got {type(key_name).__name__}")
    if not isinstance(state, bool):
        raise TypeError(f"state must be a bool, got {type(state).__name__}")
    status = "press" if state else "release"
    print(f"key {key_name} {status}")

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ==========================================

time.sleep(3)
print("FreakStudio:PCF8574 Five-way Button Test Program")
# 初始化I2C
i2c = I2C(I2C_ID, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    # 遍历从机设备地址列表
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    # 判断设备地址是否为的PCF8574地址
    if 0x20 <= device <= 0x28:
        # 假设第一个找到的设备是PCF8574地址
        print("I2c hexadecimal address:", hex(device))
        PCF8574_ADDR = device
# 初始化PCF8574
pcf = PCF8574(i2c, PCF8574_ADDR)
# 初始化五向按键
keys = PCF8574Keys(pcf, KEYS_MAP)
# ========================================  主程序  ============================================
while True:
    # 打印当前所有按键状态
    all_states = keys.read_all()
    print("status:", {k: "release" if v else "press" for k, v in all_states.items()})
    if not all_states['SW1']:
        keys.on()
    if not all_states['SW2']:
        keys.off()
    # 500ms刷新一次状态显示
    time.sleep(0.5)


