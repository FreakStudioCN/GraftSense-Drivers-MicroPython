# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : main.py
# @Description : cc253x_ttl node_to_node测试文件

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
import time
from machine import UART,Pin
# 导入第三方驱动模块
from cc253x_ttl import CC253xTTL

# ======================================== 全局变量 ============================================

# 协调器的pamid和信道（具体情况修改）
pamid =0xc535
ch = 0x0b

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio： cc253x_ttl node_to_node test")

# 声明串口实例
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
uart1 = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))

# 路由器1
env1 = CC253xTTL(uart0)
# 路由器
env2 = CC253xTTL(uart1)

# 查看入网状态和指令响应情况
while env1.read_status() is None:
    pass
while env2.read_status() is None:
    pass

# 将路由器与协调器设置成相同PAMID
# 获取路由器1 PAMID与通道
while env1.set_panid(pamid) is False:
    pass
while env1.set_channel(ch) is False:
    pass

# 获取路由器2 PAMID与通道
while env2.set_panid(pamid) is False:
    pass
while env2.set_channel(ch) is False:
    pass


# 输出路由器PAMID与通道
time.sleep(0.5)
pamid,ch=env1.read_panid_channel()
print(f"cor1:pamid:{pamid},channel:{ch}")
time.sleep(0.5)
pamid,ch=env2.read_panid_channel()
print(f"cor2:pamid:{pamid},channel:{ch}")

# 路由器1地址为0xaaff
while env1.set_custom_short_addr(0xaaff)[0] is False:
    pass

# 路由器2地址为0xffaa
while env2.set_custom_short_addr(0xffaa)[0] is False:
    pass

# ========================================  主程序  ===========================================

while True:
    # 协调器对路由器发送
    env2.send_node_to_node(source_addr=0xaaff ,target_addr=0xffaa ,data="node_to_node")
    time.sleep(0.5)
    # 协调器接收并且输出
    mode, data, addr1, addr2 = env1.recv_frame()
    print(f"📥 Coordinator Received Data:")
    print(f"   Mode: {mode}")
    print(f"   Data: {data}")
    # node_to_coord 返回 协调器地址addr1
    print(f"   Address 1: {addr1}")
    print(f"   Address 2: {addr2}")
    time.sleep(1)
