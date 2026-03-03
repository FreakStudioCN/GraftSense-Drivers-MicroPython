from machine import UART, Pin
from ewm550_driver import EWM550
import time
uart1 = UART(1, baudrate=921600, tx=Pin(8), rx=Pin(9), bits=8, parity=None, stop=1)
ewm550_base = EWM550(uart1, rx_timeout_ms=600)

print("\n===== 开始配置为基站模式 =====")
# 1. 进入AT模式
ok, resp = ewm550_base.enter_at_mode()
print(ok, resp, "进入AT模式")

# 2. 检测模块通信
ok, resp = ewm550_base.check()
print(ok, resp, "检测模块通信")

# 3. 配置核心参数（与标签地址匹配）
# 设为标签
ok, resp = ewm550_base.set_role(ewm550_base.Role["BASE"])    
print(ok, resp, "设置为基站模式")
# 标签源地址：0000（与标签目标地址匹配）
ok, resp = ewm550_base.set_src_addr("0000")            
print(ok, resp, "设置标签源地址0000")

# 目标地址：前4位为基站地址1111，后16位补0（标签仅前4位生效）
ok, resp = ewm550_base.set_dst_addr("11110000000000000000")
print(ok, resp, "绑定基站地址1111")

# 4. 复位+退出AT模式
ok, resp = ewm550_base.reset_module()
print(ok, resp, "复位并退出AT模式")



uart = UART(0, baudrate=921600, tx=Pin(16), rx=Pin(17), bits=8, parity=None, stop=1)
ewm550_tag = EWM550(uart, rx_timeout_ms=600)

print("\n===== 开始配置为标签模式 =====")
# 1. 进入AT模式
ok, resp = ewm550_tag.enter_at_mode()
print(ok, resp, "进入AT模式")

# 2. 检测模块通信
ok, resp = ewm550_tag.check()
print(ok, resp, "检测模块通信")

# 3. 配置核心参数（与基站地址匹配）
# 设为标签
ok, resp = ewm550_tag.set_role(ewm550_tag.Role["TAG"])    
print(ok, resp, "设置为标签模式")
# 标签源地址：1111（与基站目标地址匹配）
ok, resp = ewm550_tag.set_src_addr("1111")            
print(ok, resp, "设置标签源地址1111")

# 目标地址：前4位为基站地址0000，后16位补0（标签仅前4位生效）
ok, resp = ewm550_tag.set_dst_addr("00000000000000000000")
print(ok, resp, "绑定基站地址0000")

# 4. 复位+退出AT模式
ok, resp = ewm550_tag.reset_module()
print(ok, resp, "复位并退出AT模式")


while True:
    if uart.any():  # 先判断是否有数据
        data = uart.read()
        parsed_data = ewm550_tag.parse_ranging_data(data)
        print(parsed_data)
            
    time.sleep_ms(10)  # 避免占用过多资源