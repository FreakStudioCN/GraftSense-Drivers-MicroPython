# MLX90614/MLX90615 红外温度传感器驱动及测试 - MicroPython版本

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
MLX90614 和 MLX90615 是基于红外技术的非接触式温度传感器，可测量物体表面温度和环境温度。其中，MLX90614 支持单区域或双区域测温，MLX90615 为单区域测温版本，两者均通过 I2C 总线通信，具有测量精度高、响应速度快等特点，广泛应用于家电、医疗监测、工业控制等场景。

本项目提供基于 MicroPython 的传感器驱动及测试程序，实现传感器的初始化、温度读取及实时数据展示功能，方便开发者快速集成温度测量模块。

> **参考来源**：部分实现参考 [mcauser/micropython-mlx90614](https://github.com/mcauser/micropython-mlx90614) 开源项目。

---

## 主要功能
- **多型号兼容**：支持 MLX90614（单/双区域）和 MLX90615（单区域）传感器
- **温度测量范围**：
  - 环境温度：-40℃ ~ 125℃
  - 物体温度：-70℃ ~ 380℃（MLX90614）；具体范围以传感器型号为准
- **灵活的访问方式**：
  - 方法调用（`read_ambient()`、`read_object()` 等）
  - 属性访问（`ambient`、`object` 等）
  - 批量读取（`read()` 一次性获取所有温度数据）
- **实时监测**：支持自定义刷新间隔的实时数据显示
- **自动识别**：MLX90614 自动识别单/双区域型号，无需手动配置

---

## 硬件要求
### 推荐硬件
- 支持 MicroPython 的开发板（如树莓派 Pico/Pico W）
- MLX90614 或 MLX90615 红外温度传感器模块
- 杜邦线若干
- 3.3V 电源（部分模块兼容 5V，需参考模块规格）

### 引脚说明
| 传感器引脚 | 功能描述 | 开发板连接建议 |
|------------|----------|----------------|
| VCC        | 电源正极 | 3.3V（优先）或 5V（兼容模块） |
| GND        | 电源负极 | GND |
| SDA        | I2C 数据线 | 任意 I2C SDA 引脚（如树莓派 Pico 的 GP0） |
| SCL        | I2C 时钟线 | 任意 I2C SCL 引脚（如树莓派 Pico 的 GP1） |
| ADD        | 地址选择（可选） | 悬空或接 GND，用于修改 I2C 地址 |

---

## 文件说明
### mlx90614.py（驱动文件）
实现传感器核心控制逻辑，包含基础类和型号专属类：

#### 1. 基类 `SensorBase`
- **作用**：提供寄存器读取、温度转换等基础功能，供子类继承。
- **主要方法**：
  - `_read16(register: int) -> int`：从指定寄存器读取 16 位原始数据（内部方法）。
  - `_read_temp(register: int) -> float`：将寄存器数据转换为摄氏度温度（内部方法）。
  - `read_ambient() -> float`：读取环境温度。
  - `read_object() -> float`：读取第一路物体温度。
  - `read_object2() -> float`：读取第二路物体温度（仅双区域传感器支持）。
- **属性**：
  - `ambient`：环境温度（等同于 `read_ambient()`）。
  - `object`：第一路物体温度（等同于 `read_object()`）。
  - `object2`：第二路物体温度（等同于 `read_object2()`）。

#### 2. 子类 `MLX90614`
- **作用**：控制 MLX90614 传感器，支持单/双区域测温。
- **主要方法**：
  - `init(i2c, address: int =None) -> None`：初始化传感器。
  - `read() -> dict`：批量读取温度数据，返回包含 `ambient`、`object`、`object2`（双区域）的字典。
  - `get() -> dict`：`read()` 的别名方法。
- **属性**：
  - `dual_zone: bool`：自动识别是否为双区域传感器（通过寄存器配置判断）。

#### 3. 子类 `MLX90615`
- **作用**：控制 MLX90615 传感器（单区域）。
- **初始化**：`__init__(i2c, address: int = None) -> None`。
- **限制**：`dual_zone` 固定为 `False`，不支持 `object2` 相关功能。


### main.py（测试文件）
- **作用**：验证传感器驱动的各项功能，提供实时数据显示。
- **主要函数**：
  - `test_sensor_realtime(sensor, name="Sensor", interval=1.0)`：
    - 实时显示传感器的环境温度、物体温度（及双区域的第二路温度）。
    - 测试内部方法（原始数据读取）、公共方法、属性访问和批量读取功能。
    - 支持通过 `Ctrl+C` 终止测试。
  - `main()`：
    - 初始化 I2C 总线和传感器实例（MLX90614 和 MLX90615）。
    - 依次调用 `test_sensor_realtime()` 测试两个传感器。

---

## 软件设计核心思想
### 1. 继承与封装
- 基类 `SensorBase` 封装通用功能（寄存器读取、温度转换），子类 `MLX90614`/`MLX90615` 实现型号专属逻辑，提高代码复用性。

### 2. 温度转换原理
- 传感器寄存器存储的原始数据为 16 位值，通过系数 `0.02` 缩放后转换为开尔文温度，再减去 273.15 得到摄氏度。

### 3. 兼容性设计
- 统一接口：MLX90614 和 MLX90615 共享相同的方法和属性名称，简化跨型号开发。
- 自动适配：MLX90614 自动识别单/双区域，避免手动配置错误。

### 4. 易用性优化
- 提供多种数据访问方式（方法、属性、批量读取），适应不同使用场景。
- 测试程序直观展示数据，便于调试和验证硬件连接。

---

## 使用说明
### 硬件接线（树莓派 Pico 示例）
| 传感器引脚 | 树莓派 Pico 引脚 |
|------------|------------------|
| VCC        | 3.3V             |
| GND        | GND              |
| SDA        | GP0（I2C0 SDA）  |
| SCL        | GP1（I2C0 SCL）  |

> **注意**：若传感器地址与默认值不同（0x5a 或 0x5b），需在初始化时指定 `address` 参数。


### 软件部署
1. 将 `mlx90614.py`（驱动）和 `main.py`（测试程序）上传到开发板。
2. 确保开发板已烧录 MicroPython v1.23.0 及以上固件。
3. 运行 `main.py`，通过串口工具查看输出结果。


### 基本使用示例
```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/27 上午11:50
# @Author  : 缪贵成
# @File    : main.py
# @Description : mlx90614双温区温度传感器测试文件

# ======================================== 导入相关模块 =========================================

import time
from machine import I2C, Pin
from mlx90614 import MLX90614, MLX90615

# ======================================== 全局变量 =============================================

mlx61xaddr=None

# ======================================== 功能函数 =============================================

def test_sensor_realtime(sensor, name="Sensor", interval=1.0):
    """

    实时显示传感器温度数据，覆盖所有功能测试。
    Args:
        sensor: MLX90614 或 MLX90615 传感器实例
        name: 传感器名称，用于输出标识
        interval: 数据刷新间隔时间，单位秒

    Notes:
        测试内容包括内部方法、公共方法、属性访问和一次性读取功能
        双温区传感器会额外显示第二路物体温度数据
        内部方法测试可能因传感器型号不同而存在差异

    ==========================================

    Realtime display of sensor temperature data, covering all functional tests.

    Args:
        sensor: Instance of MLX90614 or MLX90615 sensor
        name: Sensor name for output identification
        interval: Data refresh interval in seconds

    Notes:
        Tests include internal methods, public methods, property access and one-time read function
        Dual-zone sensors will additionally display the second object temperature data
        Internal method tests may vary by sensor model
    """
    print("\n=== Realtime testing {} ===".format(name))
    print("Dual zone:", sensor.dual_zone)  # 输出是否为双温区传感器
    print("Press Ctrl+C to stop")  # 提示用户可以使用 Ctrl+C 停止测试

    try:
        while True:
            # ================= 内部方法测试 =================
            try:
                # 读取寄存器原始值（16 位）
                raw_ambient = sensor._read16(sensor._REGISTER_TA)
                raw_object = sensor._read16(sensor._REGISTER_TOBJ1)

                # 将寄存器原始值转换为摄氏温度
                temp_ambient_internal = sensor._read_temp(sensor._REGISTER_TA)
                temp_object_internal = sensor._read_temp(sensor._REGISTER_TOBJ1)
            except Exception as e:
                print("[Internal] Error:", e)
                raw_ambient = raw_object = temp_ambient_internal = temp_object_internal = None

            # ================= 公共方法测试 =================
            ambient = sensor.read_ambient()  # 读取环境温度
            obj = sensor.read_object()       # 读取物体温度
            # 双温区时读取第二路物体温度，否则为 None
            obj2 = sensor.read_object2() if sensor.dual_zone else None

            # ================= 属性访问测试 =================
            ambient_prop = sensor.ambient
            obj_prop = sensor.object
            obj2_prop = sensor.object2 if sensor.dual_zone else None

            # ================= 一次性读取功能测试 =================
            try:
                all_data = sensor.read()  # 一次性读取全部数据（返回字典）
            except Exception as e:
                all_data = None

            # ================= 数据输出 =================
            print("\n[{}] Data Snapshot".format(name))
            print("Raw ambient (internal):", raw_ambient)
            print("Raw object (internal):", raw_object)
            if temp_ambient_internal is not None:
                print("Temp ambient via _read_temp: {:.2f} °C".format(temp_ambient_internal))
            if temp_object_internal is not None:
                print("Temp object via _read_temp: {:.2f} °C".format(temp_object_internal))
            print("Ambient: {:.2f} °C".format(ambient))
            print("Object: {:.2f} °C".format(obj))
            if sensor.dual_zone:
                print("Object2: {:.2f} °C".format(obj2))
            print("Property ambient: {:.2f} °C".format(ambient_prop))
            print("Property object: {:.2f} °C".format(obj_prop))
            if sensor.dual_zone:
                print("Property object2: {:.2f} °C".format(obj2_prop))
            print("Read all:", all_data)

            # 间隔一段时间再刷新
            time.sleep(interval)

    except KeyboardInterrupt:
        # 用户按 Ctrl+C 时退出循环
        print("\nRealtime testing stopped")

# ======================================== 自定义类 =============================================

# ======================================== 初始化配置 ===========================================

# 硬件上电延时，保证传感器初始化完成
time.sleep(3)
print("FreakStudio: MLX90614 test start ")
# ================= I2C 初始化 =================
i2c = I2C(0, scl=1, sda=0, freq=100000)
# 开始扫描I2C总线上的设备，返回从机地址的列表
devices_list: list[int] = i2c.scan()
print('START I2C SCANNER')
# 若devices list为空，则没有设备连接到I2C总线上
if len(devices_list) == 0:
    # 若非空，则打印从机设备地址
    print("No i2c device !")
else:
    print('i2c devices found:', len(devices_list))
for device in devices_list:
    if 0x5A <= device <= 0x5D:
        print("I2c hexadecimal address:", hex(device))
        mlx61xaddr = device

# 初始化 MLX90614
sensor14 = MLX90614(i2c, mlx61xaddr)
print("[MLX90614] Sensor initialized.")
# 初始化 MLX90615
sensor15 = MLX90615(i2c, mlx61xaddr)
print("[MLX90615] Sensor initialized.")

# ======================================== 主程序 ==============================================

# ================= MLX90614 测试 =================
print("\n--- Starting MLX90614 Realtime Test ---")
test_sensor_realtime(sensor14, "MLX90614", interval=1.0)

# ================= MLX90615 测试 =================
print("\n--- Starting MLX90615 Realtime Test ---")
test_sensor_realtime(sensor15, "MLX90615", interval=1.0)

```
---
## 注意事项
### 电源要求
- 优先使用 3.3V 电源，避免 5V 电压损坏传感器。
- 确保电源稳定，波动过大会导致测量误差。

### 测量精度
- 传感器存在 ±0.5℃ 左右的误差，高精度场景需校准。
- 测量距离越近，精度越高（建议 5-10cm 内）。

### I2C 地址冲突
- MLX90614 默认地址为 0x5a，MLX90615 为 0x5b，若与其他设备冲突，可通过 ADD 引脚修改。

### 双区域限制
- MLX90615 不支持双区域，调用 `read_object2()` 会报错。
- 可通过 `dual_zone` 属性判断传感器类型，避免错误调用。

### 数据稳定性
- 连续测量时建议设置 ≥500ms 的间隔，避免数据波动过大。

### 参考文件说明
- README.md文件里面包含有具体的测试方法，当然main文件也是测试方法。

---
## 联系方式
如有任何问题或需要帮助，请通过以下方式联系开发者：  
📧 **邮箱**：10696531183@qq.com  
💻 **GitHub**：https://github.com/FreakStudioCN 

---

## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，所有由作者编写的驱动与扩展代码均采用 **知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。  

您可以自由地：  
- **共享** — 在任何媒介以任何形式复制、发行本作品  
- **演绎** — 修改、转换或以本作品为基础进行创作  

惟须遵守下列条件：  
- **署名** — 您必须给出适当的署名，提供指向本许可协议的链接，同时标明是否（对原始作品）作了修改。您可以用任何合理的方式来署名，但是不得以任何方式暗示许可人为您或您的使用背书。  
- **非商业性使用** — 您不得将本作品用于商业目的。  
- **合理引用方式** — 可在代码注释、文档、演示视频或项目说明中明确来源。  
- **声明** —此项目代码产生任何非技术性问题与署名作者无关。   

#### 参考： https://github.com/mcauser/micropython-mlx90614
**版权归 FreakStudio 所有。**



