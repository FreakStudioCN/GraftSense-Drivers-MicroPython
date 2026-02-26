# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/5 下午10:11
# @Author  : ben0i0d
# @File    : udp_server.py
# @Description : tas755c server测试文件

# ======================================== 导入相关模块 =========================================

# 导入硬件相关模块
import time
from machine import UART, Pin

# 导入第三方驱动模块
from tas_755c_eth import TAS_755C_ETH

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 上电延时3s
time.sleep(3)
# 打印调试信息
print("FreakStudio:tas755c server test")

# 初始化 UART 通信（按硬件实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建 HC14_Lora 实例
tas = TAS_755C_ETH(uart0)
# 切换AT模式
tas.enter_command_mode()

# 配置tas的IP参数
tas.set_ip_config(
    # (0=静态, 1=DHCP)
    mode=0,
    # tas设备静态IP
    ip="192.168.2.251",
    # 网关地址
    gateway="192.168.2.1",
    # 子网掩码
    subnet="255.255.255.0",
    # DNS服务器地址
    dns="223.5.5.5",
)

# 配置TCP/UDP参数
tas.set_tcp_config(
    # tas设备本地端口
    local_port=8080,
    # 远程服务端口
    remote_port=9000,
    # 0=TCP Client 1=TCP SERVER 2=UDP Client 3=UDP SERVER 8=HTTP模式
    mode=3,
    # 远程服务器IP（与通信主机IP一致，需要用户自己查看修改）
    # 域名需解析请加引号'"域名"'
    # IP地址不需加引号"IP地址"
    remote_address="192.168.2.97",
)

# 保存当前设置并重启使配置生效
tas.save()
tas.restart()
time.sleep(5)

# 切换AT模式
tas.enter_command_mode()

# 查看当前配置，检查是否生效
print(tas.get_ip_config())
print(tas.get_tcp_config())

# 切换回数据模式
tas.enter_data_mode()

# ========================================  主程序  ===========================================

while True:
    if tas.has_data():
        tas.send_data("Data received!")
        print(tas.read_data().decode("utf-8"))
