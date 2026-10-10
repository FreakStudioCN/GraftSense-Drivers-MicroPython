# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : alankrantas
# @File    : main.py
# @Description : SIM7600模块HTTP功能示例，实现HTTP POST/GET请求、响应解析及JSON数据保存

# ======================================== 导入相关模块 =========================================

# 导入SIM7600核心类
from sim7600 import SIM7600

# 从sim7600模块导入HTTP功能类
from sim7600.http import HTTP

# 从machine模块导入UART和Pin类，用于硬件引脚和串口配置
from machine import UART, Pin

# 导入time模块，用于延时操作
import time

# 导入json模块，用于JSON数据解析
import json

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================


def http_post_demo():
    """
    HTTP POST请求演示函数，完整实现HTTP服务开启、URL设置、POST数据发送、响应读取、服务关闭流程
    Args:
        无

    Raises:
        无

    Notes:
        步骤对应AT指令：HTTPINIT->HTTPPARA->HTTPDATA->HTTPACTION->HTTPHEAD->HTTPREAD->HTTPTERM

    ==========================================
    HTTP POST request demo function, fully implement HTTP service enable, URL setting, POST data sending, response reading, service shutdown process
    Args:
        None

    Raises:
        None

    Notes:
        Steps correspond to AT commands: HTTPINIT->HTTPPARA->HTTPDATA->HTTPACTION->HTTPHEAD->HTTPREAD->HTTPTERM
    """
    # 步骤1：开启HTTP服务（对应 AT+HTTPINIT 指令）
    print("=== Step 1: Enable HTTP Service ===")
    resp = http.enable_http()
    print(resp)

    # 步骤2：设置URL地址（对应 AT+HTTPPARA="URL","http://transl..." 指令）
    print("\n=== Step 2: Set Target URL ===")
    target_url = "http://translate.google.cn/"  # 替换为你的实际URL
    resp = http.set_url(target_url)
    print(resp)

    # 步骤3：准备POST数据（对应 AT+HTTPDATA=4,1000 指令）
    print("\n=== Step 3: Prepare POST Data ===")
    post_data = "Message=中国"
    data_len = len(post_data.encode("utf-8"))  # 计算UTF-8编码后的字节长度
    timeout = 1000  # 超时时间1000ms
    resp = http.http_data(data_len, timeout)
    http.sim7600.uart.write(post_data)
    print(resp)

    # 发送实际POST数据（对应 Message=中国）
    if "DOWNLOAD" in resp:
        print("Sending POST data content...")
        sim7600.uart.write(post_data)  # 直接通过UART发送数据内容

    # 步骤4：发送HTTP POST请求（对应 AT+HTTPACTION=1 指令）
    print("\n=== Step 4: Execute POST Request ===")
    resp = http.send_head(1)  # 1代表POST请求
    print(resp)
    # 等待请求完成

    # 步骤5：读取HTTP响应头（对应 AT+HTTPHEAD 指令）
    print("\n=== Step 5: Read Response Header ===")
    resp = http.get_head()
    print(resp)

    # 步骤6：读取HTTP响应信息（对应 AT+HTTPREAD=0,330 指令）
    print("\n=== Step 6: Read Response Data ===")
    resp = http.get_read(offset=0, length=330)
    print(resp)

    # 步骤7：结束HTTP服务（对应 AT+HTTPTERM 指令）
    print("\n=== Step 7: Disable HTTP Service ===")
    resp = http.disable_http()
    print(resp)


def http_get_demo():
    """
    HTTP GET请求演示函数，实现网络参数配置、HTTP GET请求、JSON数据解析及文件保存
    Args:
        无

    Raises:
        无

    Notes:
        包含APN配置、IP获取、JSON解析和文件保存功能，适配Raspberry Pi Pico文件系统

    ==========================================
    HTTP GET request demo function, implement network parameter configuration, HTTP GET request, JSON data parsing and file saving
    Args:
        None

    Raises:
        None

    Notes:
        Includes APN configuration, IP acquisition, JSON parsing and file saving functions, adapted to Raspberry Pi Pico file system
    """
    # 设置APN并获取IP信息
    print("=== 1. Configure Network Parameters ===")
    apn_result = http.set_apn(cid=1, pdp_type="IP", apn="CMNET")
    print(f"APN setting result: {apn_result}")

    # 获取IP地址信息
    ip_info = http.get_ip()
    print(f"IP configuration info: {ip_info}")

    # 启用HTTP功能
    print("\n=== 2. Initialize HTTP Service ===")
    http_enable = http.enable_http()
    print(f"HTTP enable result: {http_enable}")

    # 设置请求URL
    print("\n=== 3. Set Request URL ===")
    url_result = http.set_url("https://upypi.net/pkgs/PIO_SPI_RP2040/1.0.1/package.json")
    print(f"URL setting result: {url_result}")

    # 发送HEAD请求并获取响应头
    print("\n=== 4. Get HTTP Response Header ===")
    send_head = http.send_head(0)
    print(f"HEAD request send result: {send_head}")

    head_info = http.get_head()
    print(f"Response header info:\n{head_info}")

    # 发送GET请求并读取数据
    print("\n=== 5. Read HTTP Response Content ===")
    send_get = http.send_head(0)  # 发送GET请求
    print(f"GET request send result: {send_get}")

    # 读取响应数据
    raw_data = http.get_read(offset=0, length=512)
    print(f"Raw response data:\n{raw_data}")

    # 解析JSON数据（提取有用信息）
    print("\n=== 6. Parse JSON Data ===")
    # 提取JSON部分（从{开始到}结束）
    start_idx = raw_data.find("{")
    end_idx = raw_data.rfind("}") + 1
    if start_idx != -1 and end_idx != -1:
        json_str = raw_data[start_idx:end_idx]
        try:
            # 解析JSON
            json_data = json.loads(json_str)
            # 打印解析后的信息
            print(f"Package name: {json_data.get('name')}")
            print(f"Version: {json_data.get('version')}")
            print(f"Author: {json_data.get('author')}")
            print(f"Description: {json_data.get('description')}")
            print(f"Supported chips: {json_data.get('chips')}")
            print(f"File list: {json_data.get('urls')}")

            # ========== 核心新增：直接保存json_str到文件 ==========
            print("\n=== 7. Save JSON String to File ===")
            try:
                # 以写入模式打开文件（不存在则创建，存在则覆盖）
                with open("package.json", "w", encoding="utf-8") as f:
                    f.write(json_str)  # 直接写入提取到的json_str
                print("✅ JSON string saved to package.json successfully")

                # 验证保存结果（可选）
                with open("package.json", "r", encoding="utf-8") as f:
                    saved_content = f.read()
                    print(f"📄 Saved file content preview:\n{saved_content[:100]}...")  # 打印前100个字符
            except Exception as e:
                print(f"❌ Failed to save file: {e}")
                # ========== 核心新增结束 ==========

        except Exception as e:
            print(f"JSON parsing failed: {e}")
    else:
        print("No JSON data found")

    # 关闭HTTP连接
    print("\n=== 8. Close HTTP Connection ===")
    disable_http = http.disable_http()
    print(f"HTTP disable result: {disable_http}")


# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保SIM7600模块完成初始化
time.sleep(3)
# 打印HTTP模块初始化完成提示信息
print("FreakStudio: SIM7600 HTTP module initialized successfully")
# 配置UART0串口，波特率115200，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
# 实例化SIM7600核心类，传入配置好的UART对象
sim7600 = SIM7600(uart)
# 实例化HTTP功能类，传入SIM7600核心实例
http = HTTP(sim7600)

# ========================================  主程序  ============================================

# 执行HTTP POST请求演示
http_post_demo()
# 执行HTTP GET请求演示
http_get_demo()
