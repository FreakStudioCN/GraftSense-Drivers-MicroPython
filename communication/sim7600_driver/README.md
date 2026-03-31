# sim7600_driver

# sim7600_driver

## 目录

- 简介
- 主要功能
- 硬件要求
- 文件说明
- 软件设计核心思想
- 使用说明
- 示例程序
- 注意事项
- 联系方式
- 许可协议

---

## 简介

`sim7600_driver` 是一个为 MicroPython 环境设计的 SIM7600 系列 4G 模块驱动库，提供了简洁易用的 API，帮助开发者快速实现 4G 通信、短信、通话、定位、TCP/IP 及 HTTP 等功能。

---

## 主要功能

- **基础通信控制**：模块初始化、AT 指令交互、状态检测
- **短信功能**：短信发送、接收、读取与删除
- **通话功能**：拨号、接听、挂断等通话控制
- **定位功能**：GNSS 定位数据获取与解析
- **网络通信**：TCP/IP 连接、HTTP 请求（GET/POST）
- **状态管理**：信号强度、网络注册状态、SIM 卡状态查询

---

## 硬件要求

- 主控：支持 MicroPython 的开发板（如 ESP32、PyBoard 等）
- 模块：SIM7600 系列 4G 模块（SIM7600E/SIM7600G 等）
- 连接：UART 串口（TX/RX）、电源（3.7V~4.2V 锂电池或 5V 电源）
- 其他：SIM 卡（需开通数据 / 短信 / 通话业务）、天线

---

## 文件说明

## 软件设计核心思想

- **模块化设计**：将不同功能（短信、通话、定位等）拆分为独立模块，便于维护与扩展
- **面向对象封装**：通过 `SIM7600` 核心类统一管理硬件资源，对外提供简洁 API
- **异步 / 同步兼容**：支持阻塞式指令调用，适配 MicroPython 轻量运行环境
- **低耦合**：核心通信逻辑与业务功能分离，方便移植到不同硬件平台

---

## 使用说明

1. **安装依赖**：将 `sim7600` 文件夹拷贝到 MicroPython 设备的 `lib` 目录或根目录
2. **硬件连接**：将 SIM7600 模块的 TX/RX 引脚连接到开发板的 UART 端口
3. **初始化模块**：

```
from sim7600 import SIM7600
from machine import UART

uart = UART(1, baudrate=115200, tx=17, rx=16)  # 根据实际硬件修改引脚
sim7600 = SIM7600(uart)
sim7600.init()
```

1. **调用功能**：根据需求调用短信、通话、定位等方法

---

## 示例程序

### 示例 1：发送短信

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午4:52
# @Author  : alankrantas
# @File    : main.py
# @Description : SIM7600模块短信功能示例，实现短信模式配置、发送短信、查询所有短信

# ======================================== 导入相关模块 =========================================

# 导入SIM7600核心类
from sim7600 import SIM7600

# 从sim7600模块导入短信功能类
from sim7600.sms import SMS

# 从machine模块导入UART和Pin类，用于硬件引脚和串口配置
from machine import UART, Pin

# 导入time模块，用于延时操作
import time

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 延时3秒，确保SIM7600模块完成初始化
time.sleep(3)
# 打印短信模块初始化完成提示信息
print("FreakStudio: SIM7600 SMS module initialized successfully")
# 配置UART0串口，波特率115200，TX引脚16，RX引脚17（适配Raspberry Pi Pico）
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))
# 实例化SIM7600核心类，传入配置好的UART对象
sim7600 = SIM7600(uart)
# 实例化短信功能类，传入SIM7600核心实例
sms = SMS(sim7600)

# ========================================  主程序  ============================================

# 配置短信模式参数（gmgf=1，csmp=17,11,0,0，字符集IRA）
sms.set_sms_mode(gmgf=1, csmp="17,11,0,0", CSCS="IRA")
# 发送短信到指定号码，内容为Hello, world!
sms.send_sms("19524162399", "FreakStudio: SIM7600 SMS module initialized successfully")

# 再次配置短信模式参数（确保参数生效）
sms.set_sms_mode(gmgf=1, csmp="17,11,0,0", CSCS="IRA")

# 查询所有短信列表
sms.list_sms("ALL")

```

### 示例 2：HTTP

```python
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

```

## 注意事项

- 模块供电需稳定，建议使用 3.7V 锂电池或 5V/2A 以上电源，避免电压波动导致模块重启
- UART 波特率需与模块配置一致（默认 115200），否则无法正常通信
- 首次使用需确认 SIM 卡已激活、开通对应业务，且模块信号正常
- 定位功能需在室外开阔环境下使用，室内可能无法获取有效定位数据
- 网络通信功能需先确认模块已成功注册到网络

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

**📧 邮箱**：liqinghsui@freakstudio.cn

**💻GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

```
MIT License

Copyright (c) 2026 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copyof this software and associated documentation files (the "Software"), to dealin the Software without restriction, including without limitation the rightsto use, copy, modify, merge, publish, distribute, sublicense, and/or sellcopies of the Software, and to permit persons to whom the Software isfurnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in allcopies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS ORIMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THEAUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHERLIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THESOFTWARE.
```
