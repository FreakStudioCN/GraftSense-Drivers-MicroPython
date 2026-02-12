# GraftSense TAS-755C 串口转以太网模块 （MicroPython）

# GraftSense TAS-755C 串口转以太网模块 （MicroPython）

## 目录

- [简介](#简介)
- [主要功能](#主要功能)
- [硬件要求](#硬件要求)
- [文件说明](#文件说明)
- [软件设计核心思想](#软件设计核心思想)
- [使用说明](#使用说明)
- [示例程序](#示例程序)
- [注意事项](#注意事项)
- [联系方式](#联系方式)
- [许可协议](#许可协议)

---

## 简介

本项目为 **GraftSense TAS-755C-based Serial-to-Ethernet Module V1.0** 提供了完整的 MicroPython 驱动支持，基于 TAS-755C 芯片实现串口数据与以太网的双向转换，支持 TCP/UDP/HTTP/MQTT 等多种网络协议，适用于电子 DIY 网络通信实验、远程设备监控、工业数据采集等场景，具有通信稳定、接口兼容性好、传输速率高的优势，遵循 Grove 接口标准。

---

## 主要功能

- ✅ **AT 命令配置**：通过 UART 发送 AT 命令，支持串口参数、网络配置、协议模式等全功能配置
- ✅ **IP 配置**：支持静态 IP（手动设置 IP / 网关 / 子网掩码 / DNS）和 DHCP 自动获取 IP
- ✅ **多协议支持**：TCP Client/Server、UDP Client/Server、HTTP Client、MQTT Client 等多种工作模式
- ✅ **串口适配**：支持波特率（9600/115200 等）、数据位、校验位、停止位灵活配置
- ✅ **心跳 / 注册 / 轮询**：支持心跳包、注册包、轮询字符串配置，保障连接稳定性
- ✅ **Modbus 转换**：支持 Modbus RTU 转 TCP 协议转换，适配工业设备通信
- ✅ **MQTT 集成**：支持 MQTT 客户端配置（Client ID、用户名 / 密码、订阅 / 发布主题、保活时间等）
- ✅ **云平台 / Web 登录**：支持 DTU 云平台接入和 Web 登录配置，便于远程管理
- ✅ **模式切换**：支持命令模式（AT 配置）和数据模式（透传收发）无缝切换
- ✅ **超时 / 重启管理**：支持断开连接重启、无下行 / 上行重启、周期性重启等策略，提升可靠性

---

## 硬件要求

1. **核心硬件**：GraftSense TAS-755C-based Serial-to-Ethernet Module V1.0（基于 TAS-755C 芯片，内置 DC-DC 5V 转 3.3V 电路，支持 Grove 接口）
2. **主控设备**：支持 MicroPython v1.23.0 及以上版本的开发板（如树莓派 Pico、ESP32 等）
3. **接线配件**：

   - Grove 4Pin 线或杜邦线：连接模块的 MRX（对应 MCU RXD）、MTX（对应 MCU TXD）、GND、VCC 引脚（注意：MRX 需接 MCU 的 TXD，MTX 需接 MCU 的 RXD，避免交叉错误）
   - 调试工具：USB-TTL 模块（可选，用于固件烧录或串口调试）
4. **电源**：3.3V~5V 稳定电源（模块内置电平转换电路，兼容两种供电方式）
5. **按键与接口**：

   - SW1：指令模式按键（进入 AT 命令模式）
   - SW2：复位按键（硬件复位模块）
   - SW3：固件烧录按键（配合 ISP 接口进行固件更新）
   - ISP 接口：固件烧录串口接口
   - MCU 接口：与主控 MCU 通信的串口接口

---

## 文件说明

---

## 软件设计核心思想

1. **AT 命令分层封装**：底层封装 UART 读写与 AT 命令发送 / 响应解析（`_send_at` 私有方法），上层提供配置 API（如 `set_ip_config`、`set_tcp_config`），隐藏硬件细节，简化用户操作
2. **统一返回值规范**：所有配置方法返回 `(bool, str)` 元组，`bool` 表示执行状态（成功 / 失败），`str` 表示响应内容或错误信息，便于用户判断执行结果
3. **模式状态管理**：内置命令模式 / 数据模式切换逻辑（`enter_command_mode`/`enter_data_mode`），保障配置与透传的隔离，避免数据干扰配置
4. **参数校验与容错**：对所有配置参数进行类型检查（如 int/str 校验）和范围校验（如 IP 格式、端口范围、协议模式），避免非法参数导致模块异常
5. **协议可扩展性**：支持 TCP/UDP/HTTP/MQTT 等多种协议，通过统一的配置接口适配不同应用场景，便于功能扩展
6. **资源安全释放**：提供 `save`（保存配置）、`restart`（重启模块）方法，确保配置生效，同时支持超时重启策略，提升系统可靠性

---

## 使用说明

### 环境准备

- 在开发板上烧录 **MicroPython v1.23.0+** 固件
- 将 `tas755.py` 和测试示例文件上传至开发板文件系统

### 硬件连接

- 使用 Grove 线或杜邦线连接模块与主控 MCU：

  - 模块 `MRX` → MCU `TXD`（如树莓派 Pico 的 GP16）
  - 模块 `MTX` → MCU `RXD`（如树莓派 Pico 的 GP17）
  - 模块 `GND` → MCU `GND`
  - 模块 `VCC` → MCU `3.3V` 或 `5V`
- 确保 UART 交叉连接正确，避免通信失败

### 代码配置（以 TCP 客户端为例）

```python
import time
from machine import UART, Pin
from tas755c_eth import TAS_755C_ETH

# 初始化 UART（按实际接线调整 TX/RX）
uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
# 创建 TAS_755C 实例
tas = TAS_755C_ETH(uart0)
# 进入命令模式
tas.enter_command_mode()

# 配置 IP 参数（静态模式）
tas.set_ip_config(
    mode=0,  # 0=静态, 1=DHCP
    ip="192.168.2.251",
    gateway="192.168.2.1",
    subnet="255.255.255.0",
    dns="223.5.5.5"  # 阿里云公共 DNS
)

# 配置 TCP 客户端参数
tas.set_tcp_config(
    local_port=8080,
    remote_port=9000,
    mode=0,  # 0=TCP Client
    remote_address='"www.cnblogs.com"'  # 域名需加引号，IP 地址不加引号
)

# 保存配置并重启生效
tas.save()
tas.restart()
time.sleep(5)

# 切换回数据模式
tas.enter_data_mode()
```

### 数据收发

在数据模式下，直接调用 `send_data` 发送数据，`has_data` 检查是否有数据可读，`read_data` 读取数据：

```python
while True:
    if tas.has_data():
        recv_data = tas.read_data().decode('utf-8')
        print("Received:", recv_data)
        tas.send_data("Data received!".encode())
    time.sleep(0.1)
```

---

## 示例程序

### 示例 1：TCP 客户端（域名解析）

```
import time
from machine import UART, Pin
from tas755c_eth import TAS_755C_ETH

time.sleep(3)print("FreakStudio:tas755c dns test")

uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
tas = TAS_755C_ETH(uart0)
tas.enter_command_mode()# 配置 IP
tas.set_ip_config(mode=0, ip="192.168.2.251", gateway="192.168.2.1", subnet="255.255.255.0", dns="223.5.5.5")# 配置 TCP 客户端（域名解析）
tas.set_tcp_config(local_port=8080, remote_port=9000, mode=0, remote_address='"www.cnblogs.com"')

tas.save()
tas.restart()
time.sleep(5)

tas.enter_command_mode()print(tas.get_ip_config())print(tas.get_tcp_config())while True:
    tas.enter_command_mode()if tas.enter_command_mode()[0]:
        tcp_cfg = tas.get_tcp_config()[1]
        parts = tcp_cfg.split(',')
        ip = parts[3]
        domain = parts[4].strip('"')print("IP:", ip)print("Domain Name:", domain)
        time.sleep(5)
```

### 示例 2：HTTP 模式测试

```
import time
from machine import UART, Pin
from tas755c_eth import TAS_755C_ETH

time.sleep(3)print("FreakStudio:tas755c http test")

uart0 = UART(0, baudrate=9600, tx=Pin(16), rx=Pin(17))
tas = TAS_755C_ETH(uart0)
tas.enter_command_mode()# 配置 IP
tas.set_ip_config(mode=0, ip="192.168.2.251", gateway="192.168.2.1", subnet="255.255.255.0", dns="223.5.5.5")# 配置 HTTP 模式
tas.set_tcp_config(local_port=8080, remote_port=8080, mode=8, remote_address='192.168.2.97')
tas.set_http_config(net_status=1, method=0, header_return=1)  # 启用网络，POST 方法，返回 Header

tas.save()
tas.restart()
time.sleep(5)

tas.enter_command_mode()print(tas.get_ip_config())print(tas.get_tcp_config())

tas.enter_data_mode()
tas.send_data("http.request.test".encode())while True:if tas.has_data():print(tas.read_data().decode('utf-8'))
        time.sleep(5)
```

---

## 注意事项

1. **UART 交叉连接**：模块 `MRX` 必须接 MCU 的 `TXD`，`MTX` 必须接 MCU 的 `RXD`，切勿交叉，否则无法通信
2. **域名解析格式**：使用域名作为远程地址时，需在域名两侧添加双引号（如 `"www.cnblogs.com"`），IP 地址则无需引号（如 `192.168.2.97`）
3. **配置生效规则**：所有配置修改后需调用 `save()` 保存，并通过 `restart()` 重启模块才能生效
4. **HTTP 模式限制**：HTTP 模式下，远程端口需与 HTTP 服务器端口一致（通常为 80 或 8080），且需正确配置请求方法（GET/POST）和 Header
5. **MQTT 配置要求**：MQTT 客户端需配置合法的 Client ID、用户名 / 密码（若服务器要求），并确保订阅 / 发布主题格式正确
6. **超时重启策略**：合理设置断开连接重启、无下行 / 上行重启时间，避免频繁重启导致通信不稳定
7. **固件烧录注意**：固件烧录时需按住 `SW3` 按键，配合 ISP 接口使用 USB-TTL 模块，烧录完成后需复位模块
8. **电源稳定性**：模块对电源纹波敏感，建议使用稳压电源，避免电压波动导致通信异常

---

## 联系方式

如有任何问题或需要帮助，请通过以下方式联系开发者：

📧 **邮箱**：liqinghsui@freakstudio.cn

💻 **GitHub**：[https://github.com/FreakStudioCN](https://github.com/FreakStudioCN)

---

## 许可协议

本项目采用 **MIT License** 开源协议，具体内容如下：

```
MIT License

Copyright (c) 2025 FreakStudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
