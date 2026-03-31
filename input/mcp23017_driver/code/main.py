# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/13 下午6:20
# @Author  : hogeiha
# @File    : main.py
# @Description : MCP23017测试  配置I2C扫描、引脚输入输出、虚拟引脚操作、极性反转验证

# ======================================== 导入相关模块 =========================================

from machine import SoftI2C, Pin
import mcp23017  # 导入MCP23017驱动模块
import time

# ======================================== 全局变量 ============================================

# I2C硬件配置常量
I2C_SCL_PIN = 5
I2C_SDA_PIN = 4
I2C_FREQ = 100000
# MCP23017目标I2C地址
TARGET_SENSOR_ADDR = 0x20
# 引脚定义常量
A1_PIN = 1  # A1引脚编号（输出）
A3_PIN = 3  # A3引脚编号（输入）
# 全局MCP23017对象
mcp = None

# ======================================== 功能函数 ============================================


def test_mcp_functions():
    """
    演示MCP23017核心功能：基本电平读写、虚拟引脚操作、寄存器批量操作、输入极性反转
    Args:
        无

    Raises:
        无

    Notes:
        依次验证不同功能模块，输出关键调试信息

    ==========================================

    Demonstrate MCP23017 core functions: basic level read/write, virtual pin operation, batch register operation, input polarity inversion
    Args:
        None

    Raises:
        None

    Notes:
        Verify different function modules in sequence and output key debugging information
    """
    # ---------- 演示1：基本读写（A3输出，A3读取） ----------
    print("\n=== Demo 1: Basic Level Read/Write ===")
    # 切换A3电平为高，读取A3验证（短接后A3应同步为高）
    mcp.pin(A1_PIN, value=1)
    a3_val = mcp.pin(A3_PIN)  # 读取A3电平（返回True/False）
    print(f"A3 Output Level: HIGH (1) | A3 Read Level: {'HIGH (1)' if a3_val else 'LOW (0)'}")

    # 切换A3电平为低，读取A3验证
    mcp.pin(A1_PIN, value=0)
    a3_val = mcp.pin(A3_PIN)
    print(f"A3 Output Level: LOW (0) | A3 Read Level: {'HIGH (1)' if a3_val else 'LOW (0)'}")

    # ---------- 演示2：虚拟引脚用法（更直观的引脚操作） ----------
    print("\n=== Demo 2: Virtual Pin Operation ===")
    # 获取A3和A3的虚拟引脚对象
    A3_vpin = mcp[A1_PIN]
    a3_vpin = mcp[A3_PIN]

    # 用虚拟引脚设置A3为高
    A3_vpin.output(val=1)  # 等价于mcp.pin(A1_PIN, mode=0, value=1)
    a3_val = a3_vpin.value()  # 读取A3电平
    print(f"Virtual Pin A3 Output: HIGH (1) | Virtual Pin A3 Read: {'HIGH (1)' if a3_val else 'LOW (0)'}")

    # ---------- 演示3：批量配置/读取寄存器（进阶） ----------
    print("\n=== Demo 3: Batch Register Operation ===")
    # 读取PortA（A0-A7）的整体模式（IODIR寄存器）
    porta_mode = mcp.porta.mode
    print(f"PortA Mode Register Value: 0x{porta_mode:02X} (A3=Output(0), A3=Input(1) As Expected)")

    # 读取PortA的上拉电阻配置（GPPU寄存器）
    porta_pullup = mcp.porta.pullup
    print(f"PortA Pullup Register Value: 0x{porta_pullup:02X} (A3 Pullup Enabled(1) As Expected)")

    # ---------- 演示4：输入极性反转（可选，取消注释后验证） ----------
    print("\n=== Demo 4: Input Polarity Inversion ===")
    # 启用A3极性反转
    mcp.pin(A3_PIN, polarity=1)
    # 再次设置A3为高，A3读取应为低（因为极性反转）
    mcp.pin(A1_PIN, value=1)
    a3_val = mcp.pin(A3_PIN)
    print(f"A3 Output: HIGH (1) | A3 Inverted Read: {'HIGH (1)' if a3_val else 'LOW (0)'} (Expected LOW)")

    # 恢复A3极性为正常
    mcp.pin(A3_PIN, polarity=0)


def loop_verify():
    """
    循环验证A3输出与A3输入的电平同步性，每1秒切换一次A3电平
    Args:
        无

    Raises:
        无

    Notes:
        循环5次，输出每次的电平匹配结果，需短接A3和A3引脚

    ==========================================

    Cyclically verify the level synchronization between A3 output and A3 input, switch A3 level every 1 second
    Args:
        None

    Raises:
        None

    Notes:
        Loop 5 times, output the level matching result each time, need to short-circuit A3 and A3 pins
    """
    print("\n=== Loop Verification (Switch A3 Level Every 1 Second) ===")
    print("Short-circuit A3 and A3, observe if A3 synchronizes with A3 level changes...")
    count = 0
    while count < 5:  # 循环5次
        # 切换A3电平
        current_val = count % 2  # 0/1交替
        mcp.pin(A1_PIN, value=current_val)
        # 读取A3
        a3_val = mcp.pin(A3_PIN)
        # 打印结果
        print(f"Round {count+1} - A3 Output: {current_val} | A3 Read: {1 if a3_val else 0} | Matched: {current_val == a3_val}")
        time.sleep(1)
        count += 1


# ======================================== 自定义类 ============================================


# ======================================== 初始化配置 ===========================================

time.sleep(3)
print("FreakStudio: MCP23017 I2C Expander Function Test - Short A3 and A3 Pins")

# 初始化I2C总线（适配Raspberry Pi Pico）
i2c_bus = SoftI2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=I2C_FREQ)

# 开始扫描I2C总线上的设备
devices_list: list[int] = i2c_bus.scan()
print("START I2C SCANNER")

# 检查I2C设备扫描结果
if len(devices_list) == 0:
    print("No i2c device !")
    raise SystemExit("I2C scan found no devices, program exited")
else:
    print("i2c devices found:", len(devices_list))

# 遍历地址列表初始化目标传感器（MCP23017）
for device in devices_list:
    if device == TARGET_SENSOR_ADDR:
        print("I2c hexadecimal address:", hex(device))
        try:
            # 初始化MCP23017
            mcp = mcp23017.MCP23017(i2c=i2c_bus, address=TARGET_SENSOR_ADDR)
            print("Target sensor initialization successful")
            break
        except Exception as e:
            print(f"Sensor Initialization failed: {e}")
            continue
else:
    # 未找到目标地址时抛出明确异常
    raise Exception("No MCP23017 found at target address 0x20")

# 配置引脚（核心：A3输出，A3输入）
# 配置A3为输出模式（mode=0），初始电平低（value=0）
mcp.pin(A1_PIN, mode=0, value=0)
# 配置A3为输入模式（mode=1），启用内部上拉电阻（pullup=1）
mcp.pin(A3_PIN, mode=1, pullup=1)

# ========================================  主程序  ============================================

if __name__ == "__main__":
    try:
        # 执行核心功能测试
        test_mcp_functions()
        # 执行循环验证
        loop_verify()
        print("\nProgram execution completed successfully!")
    except OSError as e:
        print(f"Error: {e}, Please check I2C wiring or MCP23017 address!")
    except Exception as e:
        print(f"Initialization Error: {e}")
