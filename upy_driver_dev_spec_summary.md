# GraftSense-Drivers-MicroPython 驱动开发规范

> 本文档基于仓库实际代码与 `code_checker.py` 自动化检查规则整理，所有带"自动检查"标注的规范均由 pre-commit 钩子强制执行。

---

## 目录

1. [总体要求](#一总体要求)
2. [文件头部格式](#二文件头部格式)
3. [模块级全局变量](#三模块级全局变量)
4. [文件分区结构](#四文件分区结构)
5. [code_checker 8 条规则详解](#五code_checker-8-条规则详解)
6. [类设计规范](#六类设计规范)
7. [通信协议实现模式](#七通信协议实现模式)
8. [异常处理规范](#八异常处理规范)
9. [核心设计与实现细则](#九核心设计与实现细则)
10. [导入规范](#十导入规范)
11. [pre-commit 工具链配置](#十一pre-commit-工具链配置)
12. [package.json 规范](#十二packagejson-规范)
13. [驱动目录结构与命名规范](#十三驱动目录结构与命名规范)
14. [注释风格](#十四注释风格)
15. [实例属性命名约定](#十五实例属性命名约定)
16. [函数设计规范](#十六函数设计规范)
17. [类型注解规范](#十七类型注解规范)
18. [code_checker 手动使用](#十八code_checker-手动使用)
19. [规范总览速查表](#十九规范总览速查表)

---

## 一、总体要求

- **目标**：驱动代码易读、可复用、资源友好（内存/闪存）、带完整文档和测试例程，适用于 MicroPython v1.x（Raspberry Pi Pico / ESP 系列等）。
- **遵循风格**：参考 PEP8（缩进 4 空格、函数/变量小写下划线），但在受限环境更关注可读性与内存分配控制。
- **文件头注释**：代码必须包含文件头注释（环境、作者、许可证、简短描述、参考链接、时间），详见[第二节](#二文件头部格式)。
- **单一职责**：每个驱动模块对应一个芯片/一类外设，避免把多个外设功能塞进同一文件。
- **参数校验**：对输入参数进行校验，抛出有意义的异常（如 `ValueError`、`TypeError`），详见[第六节](#六类设计规范)。
- **英文输出 + 类型注解**：除注释外，`raise`/`print` 全部使用英文；使用 MicroPython 支持的内置类型注解（`: int`、`-> None` 等）。

---

## 二、文件头部格式

每个**非 `main.py`** 驱动文件必须以如下固定格式开头：

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2026/3/14 下午3:00
# @Author  : 作者名
# @File    : filename.py
# @Description : 模块功能简述
# @License : MIT
```

**注意事项：**

- `# @License : MIT` 必须作为**独立注释行**单独存在，不能与其他内容合并（code_checker 规则 2 的精准匹配对象，缺失则 `[FAIL]`）
- `@Author` 可以是中文名或英文名
- `@Description` 内容允许包含中文

---

## 三、模块级全局变量

文件头部之后，紧跟四个必须存在的模块全局变量（**code_checker 规则 1，自动检查**）：

```python
__version__ = "1.0.0"
__author__ = "作者名"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"
```

> **缺少任何一个**均会导致 `[FAIL]`。`main.py` 跳过此项检查。

**可选：`__chip__` 变量**

若驱动依赖特定芯片特性（如 RP2040 的 PIO），需额外声明：

```python
__chip__ = "RP2040"
```

运行时可据此做硬件适配：

```python
if "rp2040" in __chip__.lower():
    self._i2c = I2C(0, sda=Pin(0), scl=Pin(1))
elif "esp32" in __chip__.lower():
    self._i2c = I2C(scl=Pin(22), sda=Pin(21))
```

---

## 四、文件分区结构

所有文件均需使用固定的分区标注注释。code_checker 对分区使用**模糊匹配**（忽略 `=` 数量和空格），只匹配核心标题文字。

### 3.1 驱动文件（非 main.py）结构

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : YYYY/MM/DD HH:MM
# @Author  : 作者名
# @File    : filename.py
# @Description : 功能描述
# @License : MIT

__version__ = "1.0.0"
__author__ = "作者名"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

# ... import 语句 ...

# ======================================== 全局变量 ============================================

# ... 常量 / 寄存器地址定义 ...

# ======================================== 功能函数 ============================================

# ... 模块级工具函数（可为空）...

# ======================================== 自定义类 ============================================

# ... 类定义 ...

# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
```

> 驱动文件末尾的"初始化配置"和"主程序"分区留空即可，但**分区标注必须存在**。

### 4.1 各分区内容规范

**导入相关模块区**

- 放：标准库 → MicroPython 硬件模块 → 第三方/本地模块，分组按字母或使用频率排序
- 不得放：长延时操作（如 `time.sleep`）、硬件实例化

**全局变量区**

- 放：模块级常量（I2C 默认地址、寄存器地址）、`DEBUG` 开关、复用缓冲区
- 不得放：硬件对象实例化（`I2C()`、`Pin()` 等）

复用缓冲区可减少运行时内存分配：

```python
# 正确：全局复用 buffer
_BUF2 = bytearray(2)

def read_data():
    i2c.readfrom_mem_into(addr, reg, _BUF2)  # 零内存分配

# 错误：每次调用新建 buffer
def read_data():
    buf = bytearray(2)  # 每次分配新内存
    i2c.readfrom_mem_into(addr, reg, buf)
```

**功能函数区**

- 放：模块级纯工具函数（不做硬件 I/O，利于单元测试），如 `clamp()`、地址格式化等
- 不得放：频繁创建大对象的函数、占用大量内存的 I/O 操作

**自定义类区**

- 类内部顺序：类级常量 → `__init__` → 公共方法 → 私有方法（`_` 前缀）→ `deinit()`
- `__init__` 中避免长延时；若需检测/重置，把重试和延时参数化

**初始化配置区（main.py）**

- 放：硬件对象实例化、设备扫描与地址选择、初始参数配置、短暂开机自检
- 库模块中此区留空，不得在导入时创建硬件实例（避免导入副作用）

**主程序区（main.py）**

- 放：主流程逻辑，使用 `try/except/finally` 确保外设安全退出
- 不得放：无退出条件的无限循环（示例循环需提供中断方式）

```python
# ========================================  主程序  ===========================================
try:
    while True:
        # 主逻辑
        pass
except Exception as e:
    print("ERROR:", e)
finally:
    try:
        sensor.deinit()
    except Exception:
        pass
```

### 3.2 main.py 专属结构

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : YYYY/MM/DD HH:MM
# @Author  : 作者名
# @File    : main.py
# @Description : XXX 传感器测试文件

# ======================================== 导入相关模块 =========================================

from machine import I2C, Pin
import time
from bh_1750 import BH1750

# ======================================== 全局变量 ============================================

# 只允许简单变量赋值，禁止出现任何实例化
bh_addr = None
SAMPLE_INTERVAL = 1000

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

# ======================================== 初始化配置 ===========================================

# 必须包含 time.sleep(3)
time.sleep(3)
# 必须包含以 "FreakStudio:" 开头的 print
print("FreakStudio: test Light Intensity Sensor now")

# 实例化对象必须放在这里
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=100000)
sensor = BH1750(bh_addr, i2c)

# ========================================  主程序  ===========================================

# while 循环只允许在此分区内出现
while True:
    lux = sensor.measurement
    print(lux)
    time.sleep(1)
```

---

## 五、code_checker 8 条规则详解

这是整个规范的核心，所有规则通过 AST 或正则表达式在 `code_checker.py` 中自动执行。

### 规则 1：必须包含 4 个模块全局变量（非 main.py）

- **检查方式：** AST 解析 `ast.Assign` 节点
- **检查内容：** `__version__`、`__author__`、`__license__`、`__platform__`
- **main.py 跳过**

### 规则 2：必须有独立的 `# @License : MIT` 注释行（非 main.py）

- **检查方式：** 逐行精准匹配（`strip()` 后对比）
- 必须是独立行，不能写成 `# @License : MIT, Apache`
- **main.py 跳过**

### 规则 3：raise/print 中不得含中文字符（所有文件）

- **检查范围：** 包含 `raise` 或 `print(` 的所有行
- **检查内容：** 提取字符串字面量后，用正则 `[\u4e00-\u9fff]` 匹配
- **注释、docstring 不受限制**，只有运行时字符串受限

```python
# 违规 - 检查失败
raise ValueError("参数不合法")
print("传感器初始化完成")

# 合规 - 允许通过
raise ValueError("parameter is invalid")
print("Sensor initialized successfully")
```

### 规则 4：main.py 实例化位置校验

- **全局变量区**：不得出现任何实例化（匹配 `x = Class()`、`x = module.Class()`、`module.Class()` 等模式）
- **初始化配置区**：必须存在至少一个实例化
- **非 main.py 跳过**

### 规则 5：while 循环位置校验（main.py）

- `while` 循环**只允许**出现在"主程序"分区之后
- 出现在其他任何位置均为违规
- 检查使用正则 `^\s*while\s+` 多行匹配，并剥离注释后再检查
- **非 main.py 跳过**

### 规则 6：初始化配置区必要内容（main.py）

- 必须包含 `time.sleep(3)`（支持空格变体：`time.sleep ( 3 )`）
- 必须包含 `print("FreakStudio: ...")` 格式的打印语句
- **非 main.py 跳过**

### 规则 7：`__init__` 方法参数类型注解（所有文件）

- 使用 AST 遍历找到 `__init__` 方法
- 检查参数是否有 `annotation`（即 `: Type` 标注）
- **没有 `__init__` 方法的文件跳过此检查**

### 规则 8：类方法的参数校验（非 main.py）

检查器遍历所有类的所有方法（排除 `self`/`cls`），对于有参数的方法，方法体内必须同时满足：

**条件一，至少包含以下之一：**
- `isinstance(param, Type)` 调用
- `hasattr(obj, "attr")` 调用
- 比较表达式（`==`、`!=`、`>`、`<`、`<=`、`>=`）或布尔组合（`and`/`or`）

**条件二：**
- 上述条件所在的 `if` 块内部有 `raise` 语句

- **main.py 跳过**

---

## 六、类设计规范

### 6.1 设计原则

- **单一职责**：每个类只封装一种外设或一组密切相关功能
- **最小副作用**：构造函数只做必要验证与轻量初始化，重置/校准等操作提供独立方法
- **显式依赖注入**：不在类内创建硬件总线对象（I2C/SPI/Pin），作为参数传入
- **可测试**：纯逻辑（校准/转换）抽成纯函数；I/O 封装为小型易 mock 的方法（`_read_reg`、`_write_reg`）
- **异常策略**：参数错误抛 `ValueError`；I/O/硬件错误抛 `RuntimeError` 或自定义 `DeviceError`

```python
# 错误：内部创建硬件对象（无法复用总线，无法测试）
class MPU6050:
    def __init__(self):
        self.i2c = I2C(1)  # 硬编码

# 正确：依赖注入
class MPU6050:
    def __init__(self, i2c_bus):
        self.i2c = i2c_bus

shared_i2c = I2C(1)
sensor1 = MPU6050(shared_i2c)
sensor2 = BMP280(shared_i2c)  # 总线复用
```

### 6.2 MicroPython 平台特性

- **类型注解**：只使用原生类型（`int`、`float`、`bytes`、`bytearray` 等）及 `I2C`/`Pin`，回调注解写 `callable`
- **避免多重继承**：优先使用组合模式，多重继承在 MicroPython 上可能引发内存问题
- **预声明所有属性**：在 `__init__` 中声明所有字段；可用 `__slots__` 固定属性槽减少内存

```python
# 推荐：__slots__ 优化内存
class Sensor:
    __slots__ = ('temp', 'humidity', '_buf')
    def __init__(self):
        self.temp = 0
        self.humidity = 0
        self._buf = bytearray(4)
```

### 6.3 类结构布局顺序

1. 类级常量（`UPPER_CASE`）
2. `__init__`（参数校验 → 属性赋值 → 轻量初始化）
3. 公共 API 方法（按常用程度排列）
4. `@property` 访问器
5. 私有方法（`_` 前缀）
6. `deinit()` / `close()`（资源清理，放最后）

### 6.4 类级别 docstring（中英双语）

```python
class BH1750:
    """
    该类用于控制 BH1750 数字环境光传感器，支持测量模式、分辨率、测量时间的配置，
    并可获取光照强度（lux）数据。

    Attributes:
        _address (int): BH1750 I2C 地址。
        _i2c (I2C): machine.I2C 实例，用于 I2C 通信。
        _measurement_mode (int): 测量模式（连续测量或一次测量）。
        _resolution (int): 分辨率模式（高分辨率、高分辨率2、低分辨率）。
        _measurement_time (int): 测量时间（范围 31-254，默认 69）。

    Methods:
        configure(measurement_mode, resolution, measurement_time): 配置测量参数。
        reset(): 重置传感器，清除寄存器。
        power_on(): 开启传感器。
        power_off(): 关闭传感器。
        measurement -> float: 获取当前光照强度（lux）。
        measurements(): 生成器，持续获取光照强度数据。

    Notes:
        - I2C 操作不是 ISR-safe，请避免在中断中调用。
        - 传感器测量时间和分辨率直接影响 lux 计算结果。

    ==========================================

    BH1750 driver for digital ambient light sensor.

    Attributes:
        _address (int): I2C address of the sensor.
        _i2c (I2C): machine.I2C instance for bus communication.
        _measurement_mode (int): Measurement mode (continuous or one-time).
        _resolution (int): Resolution mode (high, high2, low).
        _measurement_time (int): Measurement time (31-254, default 69).

    Methods:
        configure(...): Configure measurement mode and resolution.
        reset(): Reset sensor, clear illuminance data register.
        power_on(): Power on the sensor.
        power_off(): Power off the sensor.
        measurement -> float: Get current lux reading.
        measurements(): Generator for continuous lux readings.

    Notes:
        - Methods performing I2C are not ISR-safe.
        - Lux calculation depends on configured resolution and measurement time.
    """
```

**规律：**
- 中文在前，英文在后
- 以 `==========================================` 分隔中英文部分
- 包含 `Attributes`、`Methods`、`Notes` 三个标准 section

### 6.5 类级别常量（使用 `micropython.const()`）

```python
from micropython import const

class BH1750:
    MEASUREMENT_MODE_CONTINUOUSLY = const(1)
    MEASUREMENT_MODE_ONE_TIME     = const(2)

    RESOLUTION_HIGH   = const(0)
    RESOLUTION_HIGH_2 = const(1)
    RESOLUTION_LOW    = const(2)

    MEASUREMENT_TIME_DEFAULT = const(69)
    MEASUREMENT_TIME_MIN     = const(31)
    MEASUREMENT_TIME_MAX     = const(254)
```

也可在模块顶层定义为普通常量（寄存器地址等）：

```python
DATA_FORMAT = 0x31
BW_RATE     = 0x2C
POWER_CTL   = 0x2D
INT_ENABLE  = 0x2E
OFSX        = 0x1E
OFSY        = 0x1F
OFSZ        = 0x20
```

### 6.6 `__init__` 方法规范

**完整示例（ADXL345 驱动）：**

```python
def __init__(self, bus: int, scl: int, sda: int, cs: Pin) -> None:
    """
    传感器初始化并配置工作参数

    Args:
        bus (int): I2C总线编号（通常为0或1）
        scl (int): I2C SCL引脚编号（有效GPIO引脚号）
        sda (int): I2C SDA引脚编号（有效GPIO引脚号）
        cs (Pin): 片选引脚对象（已配置的Pin实例）

    Raises:
        ValueError: 任何参数为None或值超出范围
        TypeError: 参数类型不符合要求
        OSError: I2C总线初始化失败或传感器未找到

    Notes:
        初始化流程：配置片选引脚 → 初始化I2C总线 → 扫描并匹配传感器地址 → 配置寄存器

    ==========================================
    Initialize sensor and configure working parameters

    Args:
        bus (int): I2C bus number (usually 0 or 1)
        scl (int): I2C SCL pin number (valid GPIO pin number)
        sda (int): I2C SDA pin number (valid GPIO pin number)
        cs (Pin): Chip select pin object (configured Pin instance)

    Raises:
        ValueError: Any parameter is None or value out of range
        TypeError: Parameter type does not meet requirements
        OSError: I2C bus initialization failed or sensor not found

    Notes:
        Initialization: Configure chip select → Initialize I2C bus → Scan and match sensor address → Configure registers
    """
    # 参数验证（必须在逻辑代码之前）
    if bus is None:
        raise ValueError("bus cannot be None")
    if not isinstance(bus, int):
        raise TypeError(f"bus must be int, got {type(bus).__name__}")
    if bus not in (0, 1):
        raise ValueError(f"bus must be 0 or 1, got {bus}")

    if scl is None:
        raise ValueError("scl cannot be None")
    if not isinstance(scl, int):
        raise TypeError(f"scl must be int, got {type(scl).__name__}")
    if scl < 0:
        raise ValueError(f"scl must be a valid GPIO pin number, got {scl}")

    if sda is None:
        raise ValueError("sda cannot be None")
    if not isinstance(sda, int):
        raise TypeError(f"sda must be int, got {type(sda).__name__}")
    if sda < 0:
        raise ValueError(f"sda must be a valid GPIO pin number, got {sda}")

    if cs is None:
        raise ValueError("cs cannot be None")
    if not isinstance(cs, Pin):
        raise TypeError(f"cs must be Pin object, got {type(cs).__name__}")

    # 初始化逻辑
    self.scl = scl
    self.sda = sda
    self.cs  = cs
    cs.value(1)
    time.sleep(1)
    self.i2c = I2C(bus, scl=self.scl, sda=self.sda, freq=10000)

    # 扫描并匹配设备
    slv = self.i2c.scan()
    for s in slv:
        buf = self.i2c.readfrom_mem(s, 0, 1)
        if buf[0] == 0xE5:          # ADXL345 设备 ID
            self.slvAddr = s
            print("adxl345 found")
            break

    # 配置寄存器
    self.writeByte(DATA_FORMAT, 0x2B)   # 16g量程，全分辨率
    self.writeByte(BW_RATE,     0x0A)   # 100Hz 输出速率
    self.writeByte(INT_ENABLE,  0x00)   # 不使用中断
    self.writeByte(OFSX,        0x00)
    self.writeByte(OFSY,        0x00)
    self.writeByte(OFSZ,        0x00)
    self.writeByte(POWER_CTL,   0x28)   # 测量模式
    time.sleep(1)
```

**要求：**
1. 所有参数必须有类型注解（`: int`、`: Pin` 等）
2. 返回值注解 `-> None`
3. 参数校验必须写在初始化逻辑之前
4. 每个参数至少两步校验：None 检查 + 类型检查，必要时追加值范围检查

### 6.7 普通方法规范

**完整示例：**

```python
def writeByte(self, addr: int, data: int) -> None:
    """
    向传感器指定寄存器写入单个字节数据

    Args:
        addr (int): 寄存器地址（8位，0x00-0x3F）
        data (int): 要写入的字节数据（0-255）

    Raises:
        ValueError: 参数为None或值超出范围
        TypeError: 参数类型错误
        OSError: I2C写入失败

    Notes:
        采用I2C内存写操作，将数据写入指定寄存器地址

    ==========================================
    Write a single byte of data to the specified register of the sensor

    Args:
        addr (int): Register address (8-bit, 0x00-0x3F)
        data (int): Byte data to be written (0-255)

    Raises:
        ValueError: Parameter is None or value out of range
        TypeError: Parameter type error
        OSError: I2C write failure
    """
    # 参数校验（code_checker 规则 8 要求）
    if addr is None:
        raise ValueError("addr cannot be None")
    if not isinstance(addr, int):
        raise TypeError(f"addr must be int, got {type(addr).__name__}")
    if addr < 0 or addr > 0x3F:
        raise ValueError(f"addr must be 0x00-0x3F, got {hex(addr)}")

    if data is None:
        raise ValueError("data cannot be None")
    if not isinstance(data, int):
        raise TypeError(f"data must be int, got {type(data).__name__}")
    if data < 0 or data > 255:
        raise ValueError(f"data must be 0-255, got {data}")

    d = bytearray([data])
    self.i2c.writeto_mem(self.slvAddr, addr, d)
```

### 6.8 参数校验的三种模式

**模式一：`isinstance` + `raise`（类型检查，最常用）**

```python
if not isinstance(address, int):
    raise TypeError("address must be an integer")
```

**模式二：`hasattr` + `raise`（鸭子类型检查，用于验证对象接口）**

```python
# 避免直接导入 machine.I2C 带来的兼容性问题，改用 duck-typing
if not hasattr(i2c, "writeto") or not hasattr(i2c, "readfrom_into"):
    raise TypeError("i2c must be a machine.I2C instance")
```

**模式三：值范围比较 + `raise`**

```python
if not (address == 0x23 or address == 0x5C):
    raise ValueError("address must be 0x23 or 0x5C")

if not (BH1750.MEASUREMENT_TIME_MIN <= measurement_time <= BH1750.MEASUREMENT_TIME_MAX):
    raise ValueError(
        "measurement_time must be between {0} and {1}".format(
            BH1750.MEASUREMENT_TIME_MIN, BH1750.MEASUREMENT_TIME_MAX
        )
    )
```

### 6.9 `@property` 装饰器

适合只读数据访问的方法：

```python
@property
def measurement(self) -> float:
    """
    获取当前光照强度（lux）。

    Returns:
        float: 光照强度，单位 lux。

    Notes:
        如果为一次测量模式，会在调用时触发测量。

    ==========================================

    Get current light intensity (lux).

    Returns:
        float: Light intensity in lux.

    Notes:
        If in one-time mode, triggers a measurement when called.
    """
    if self._measurement_mode == BH1750.MEASUREMENT_MODE_ONE_TIME:
        self._write_measurement_mode()

    buffer = bytearray(2)
    self._i2c.readfrom_into(self._address, buffer)
    lux = (buffer[0] << 8 | buffer[1]) / (1.2 * (BH1750.MEASUREMENT_TIME_DEFAULT / self._measurement_time))

    if self._resolution == BH1750.RESOLUTION_HIGH_2:
        return lux / 2
    return lux
```

### 6.10 私有方法命名

内部辅助方法使用单下划线前缀：

```python
def _write_measurement_time(self):
    """
    写入测量时间到传感器寄存器。

    Notes:
        内部方法，不建议用户直接调用。

    ==========================================

    Write measurement time to sensor registers.

    Notes:
        Internal method, not intended for direct use.
    """
    buffer = bytearray(1)
    high_bit = 1 << 6 | self._measurement_time >> 5
    low_bit  = 3 << 5 | (self._measurement_time << 3) >> 3
    buffer[0] = high_bit
    self._i2c.writeto(self._address, buffer)
    buffer[0] = low_bit
    self._i2c.writeto(self._address, buffer)
```

### 6.11 生成器方法

```python
def measurements(self):
    """
    光照强度数据生成器，持续提供测量值。

    Returns:
        generator: 每次迭代返回 float 型 lux 值。

    Notes:
        睡眠时间根据分辨率和测量时间自动计算。

    ==========================================

    Generator for continuous light intensity measurements.

    Returns:
        generator: Returns float lux value on each iteration.

    Notes:
        Sleep time is calculated based on resolution and measurement time.
    """
    while True:
        yield self.measurement
        if self._measurement_mode == BH1750.MEASUREMENT_MODE_CONTINUOUSLY:
            base = 16 if self._resolution == BH1750.RESOLUTION_LOW else 120
            sleep_ms(math.ceil(base * self._measurement_time / BH1750.MEASUREMENT_TIME_DEFAULT))
```

### 6.12 方法注释补充规范

**副作用说明**

若方法除主要功能外还会改变外部状态，必须在 Notes 中明确标注：

```python
def read_acceleration(self) -> tuple:
    """
    读取三轴加速度值。

    Notes:
        - 执行一次 I2C 读取事务（6 字节）。
        - 调用过程中会更新内部 `_last_read` 时间戳。
        - 若传感器处于睡眠模式，该方法会隐式唤醒传感器。

    ==========================================

    Notes:
        - Performs one I2C read transaction (6 bytes).
        - Updates internal `_last_read` timestamp.
        - Implicitly wakes up the sensor if in sleep mode.
    """
```

**ISR-Safe 标注**

在 Notes 中明确标注方法是否可在中断中安全调用：

```python
def _handle_interrupt(self, pin) -> None:
    """
    Notes:
        - ISR-safe，可安全在中断服务程序中调用。
        - 执行时间 < 50 μs，不进行内存分配，不涉及 I2C/SPI 操作。
    ==========================================
    Notes:
        - ISR-safe, can be safely invoked inside ISR.
        - Execution time < 50 μs. No memory allocation. No I2C/SPI.
    """

def calibrate_zero(self) -> None:
    """
    Notes:
        - Main-only，非 ISR 安全。包含阻塞延时 (10 ms)，发起 I2C 写事务。
    ==========================================
    Notes:
        - Main-only, not ISR-safe. Contains blocking delay (10 ms).
    """
```

**回调函数规范**

在 Args 中写明回调签名与调用上下文：

```python
def start_listening(self, callback: callable) -> None:
    """
    Args:
        callback (callable): 检测到卡片时调用。
            签名：``def cb(card_id: int, uid: bytes) -> None``。
            调用上下文：ISR，执行时间 < 100 μs，禁止内存分配。
    ==========================================
    Args:
        callback (callable): Invoked when a card is detected.
            Signature: ``def cb(card_id: int, uid: bytes) -> None``.
            Context: ISR. Execution < 100 μs. No memory allocation.
    """
```

---

## 七、通信协议实现模式

### 7.1 I2C 协议（传感器类最常用）

```python
from machine import I2C, Pin
import ustruct

# 初始化
self.i2c = I2C(bus, scl=Pin(scl), sda=Pin(sda), freq=10000)

# 设备扫描 + ID 验证
slv = self.i2c.scan()
for s in slv:
    buf = self.i2c.readfrom_mem(s, DEVICE_ID_REG, 1)
    if buf[0] == 0xE5:          # 比对设备 ID
        self.slvAddr = s
        print("Device found")
        break

# 写寄存器（单字节）
d = bytearray([data])
self.i2c.writeto_mem(self.slvAddr, register_addr, d)

# 读寄存器（单字节）
result = self.i2c.readfrom_mem(self.slvAddr, register_addr, 1)

# 直接读写字节流（无寄存器地址）
self.i2c.writeto(self._address, bytearray(b"\x01"))
buffer = bytearray(2)
self.i2c.readfrom_into(self._address, buffer)

# 数据解包（小端有符号 16 位）
(value,) = ustruct.unpack("<h", buf)
```

### 7.2 UART 协议（通信模块常用）

```python
from machine import UART

# UART 对象作为参数传入（外部初始化后传入，便于复用）
self._uart = uart

# 发送十六进制帧
self._uart.write(bytes.fromhex(cmd_hex_string))
time.sleep(0.05)

# 接收响应
if self._uart.any():
    resp    = self._uart.read()
    tag     = resp[4]       # 协议标签字节
    payload = resp[5:]      # 有效载荷
    payload_hex = payload.hex()
```

### 7.3 Timer 回调模式（看门狗 / 周期任务）

```python
from machine import Pin, Timer

# 初始化定时器
self.wdi   = Pin(wdi_pin, Pin.OUT)
self.state = 0
self.timer = Timer(-1)
self.timer.init(
    period=feed_interval,
    mode=Timer.PERIODIC,
    callback=self._feed
)

def _feed(self, t: Timer) -> None:
    """ISR-safe 定时器回调，通过状态翻转喂狗"""
    self.state ^= 1
    self.wdi.value(self.state)
```

---

## 八、异常处理规范

### 8.1 总体原则

- **清晰且可预测**：对外抛出的异常应有稳定语义（参数错误、通信失败、设备错误等）
- **最小化裸露底层异常**：捕获底层 `OSError`/`ValueError`，用明确的自定义或标准异常重新抛出
- **参数验证优先**：函数入口做参数验证并立即抛 `ValueError`，避免进入不确定状态
- **不得在 ISR 中抛异常**：ISR 中记录错误标志，由主循环处理异常
- **幂等清理**：在异常路径中确保资源安全，`finally` 中调用 `deinit()` 或恢复默认状态
- **文档化**：每个方法的 docstring 必须列出 `Raises:` 条目

**封装底层异常示例：**

```python
class DeviceError(RuntimeError):
    pass

class I2CDevice:
    def _read_reg(self, reg: int) -> int:
        try:
            return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
        except OSError as e:
            raise DeviceError(f"读取寄存器0x{reg:02X}失败") from e
```

**ISR 错误处理示例：**

```python
class Encoder:
    def __init__(self):
        self._error_flags = 0

    def _isr_handler(self, pin):
        try:
            # 核心逻辑
            pass
        except Exception:
            self._error_flags |= 0x01  # 记录错误标志，不抛异常

    def check_errors(self):
        if self._error_flags:
            raise DeviceError(f"编码器错误: flags={bin(self._error_flags)}")
```

### 8.2 异常分类

- **`ValueError`**：参数校验错误（索引超界、频率不在允许范围、类型错误）
- **`RuntimeError` 或自定义 `DeviceError`**：硬件通信失败（I2C/SPI 读写失败、超时、CRC 校验失败）
- **自定义异常**（如 `PCA9685Error`、`SensorError`）：不可恢复或严重故障，便于上层按类型区分
- **返回值或 debug 输出**：警告/非致命情况
- **错误标志位**：ISR 中的错误，在 ISR 中不抛异常

### 8.3 捕获与包装

在所有底层 I/O 方法捕获 `OSError` 并抛出 `DeviceError` 或 `RuntimeError`，保留原始信息：

```python
def _write_reg(self, reg: int, value: int) -> None:
    try:
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))
    except OSError as e:
        raise DeviceError(f"写入寄存器0x{reg:02X}失败") from e
```

### 8.4 重试机制

对瞬态 I2C/SPI 错误可实现有限重试（2-3 次），提供可选参数 `retries=1, delay_ms=5`：

```python
def read_with_retry(self, reg: int, retries: int = 2) -> int:
    for attempt in range(retries + 1):
        try:
            return self._read_reg(reg)
        except DeviceError:
            if attempt == retries:
                raise
            time.sleep_ms(5)
```

### 8.5 资源清理

使用 `try/except/finally` 确保外设置入安全状态：

```python
def move_to_position(self, pos: int):
    self.enable()
    try:
        self._set_target(pos)
        self._wait_until_done(timeout=10.0)
    except TimeoutError:
        self.emergency_stop()
        raise
    finally:
        self._release_brake()
        self._set_power(0)
```

### 8.6 调试输出

避免使用大型 logging 库，用轻量 debug 开关控制 `print()`：

```python
def _log_error(self, msg: str):
    if self.debug:
        print(f"[ERROR] {msg}")
```

异常消息应简洁，包含关键信息（函数/寄存器/通道/地址）：

```
"I2C write failed reg=0x06 ch=3: [Errno 5]"
```

---

## 九、核心设计与实现细则

传感器驱动开发围绕"硬件逻辑内聚、对外接口简洁、异常处理完善、资源管理闭环"的核心原则，覆盖功能抽离、参数管理、硬件适配等全维度。

### 9.1 通用功能抽离

将与硬件无关、可复用的通用功能（数据格式转换、CRC 校验、单位转换等）抽离到类外声明，降低类的耦合度：

```python
# 类外通用工具函数
def sht30_crc8(data: bytes) -> int:
    POLYNOMIAL = 0x31
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc << 1) ^ POLYNOMIAL if crc & 0x80 else crc << 1
        crc &= 0xFF
    return crc

def raw_temp_to_celsius(raw_temp: int) -> float:
    return -45.0 + 175.0 * raw_temp / 65535.0

def raw_hum_to_percent(raw_hum: int) -> float:
    return 100.0 * raw_hum / 65535.0

# 传感器类只负责硬件交互
class SHT30:
    def __init__(self, i2c, addr: int = 0x44):
        self.i2c = i2c
        self.addr = addr
```

### 9.2 自定义异常类

针对典型异常场景定义专属异常类，提升错误定位效率：

```python
class SensorError(Exception):
    pass

class SensorCommunicationError(SensorError):
    def __init__(self, msg: str = "Sensor communication failed"):
        super().__init__(msg)

class SensorInvalidParamError(SensorError):
    def __init__(self, param: str, value, valid_range: tuple):
        super().__init__(f"Invalid param {param}={value}, valid: {valid_range}")

class SensorDataError(SensorError):
    def __init__(self, msg: str = "Sensor data validation failed"):
        super().__init__(msg)
```

### 9.3 参数管理：类属性定义寄存器/指令/默认参数

将固定硬件参数和默认配置声明为类属性（大写常量），避免硬编码：

```python
class SHT30:
    CMD_MEASURE_HIGH_REP = b'\x2C\x06'
    CMD_SOFT_RESET       = b'\x30\xA2'
    DEFAULT_SAMPLING_RATE = 1000   # ms
    TEMP_RANGE = (-45.0, 125.0)
    HUM_RANGE  = (0.0, 100.0)
```

### 9.4 私有/公共方法划分

- 公共方法：对外暴露的 API（`init`、`read_temp_hum`、`soft_reset`）
- 私有方法（`_` 前缀）：底层硬件交互（`_read_raw_data`、`_parse_raw_data`、`_validate_data`）

```python
class SHT30:
    def read_temp_hum(self) -> tuple:
        raw = self._read_raw_data()
        temp, hum = self._parse_raw_data(raw)
        self._validate_data(temp, hum)
        return temp, hum

    def _read_raw_data(self) -> bytes:
        try:
            return self.i2c.readfrom(self.addr, 6)
        except OSError as e:
            raise SensorCommunicationError(f"I2C read failed: {e}") from e

    def _validate_data(self, temp: float, hum: float) -> None:
        if not (self.TEMP_RANGE[0] <= temp <= self.TEMP_RANGE[1]):
            raise SensorDataError(f"Temperature {temp} out of range {self.TEMP_RANGE}")
```

### 9.5 中断适配：micropython.schedule

中断回调函数仅执行轻量操作，通过 `micropython.schedule` 将核心处理逻辑调度到主循环：

```python
import micropython
from machine import Pin

class SHT30:
    def __init__(self, i2c, addr: int = 0x44, int_pin: int = None):
        self._int_flag = False
        if int_pin is not None:
            self._int_pin = Pin(int_pin, Pin.IN, Pin.PULL_UP)
            self._int_pin.irq(trigger=Pin.IRQ_FALLING, handler=self._int_callback)

    def _int_callback(self, pin):
        micropython.schedule(self._handle_interrupt, None)

    def _handle_interrupt(self, _):
        if not self._int_flag:
            self._int_flag = True
            try:
                temp, hum = self.read_temp_hum()
                print(f"Interrupt: {temp:.2f}C, {hum:.2f}%")
            except SensorError as e:
                print(f"Interrupt failed: {e}")
            self._int_flag = False
```

### 9.6 非阻塞执行：定时器实现周期性采样

避免 `time.sleep()` 阻塞主循环，使用 `machine.Timer` 实现非阻塞周期性采样：

```python
from machine import Timer

class SHT30:
    def start_periodic_sampling(self, interval: int = None):
        interval = interval or self.DEFAULT_SAMPLING_RATE
        self._timer = Timer(-1)
        self._timer.init(period=interval, mode=Timer.PERIODIC, callback=self._sampling_callback)

    def stop_periodic_sampling(self):
        if self._timer:
            self._timer.deinit()
            self._timer = None

    def _sampling_callback(self, timer):
        try:
            self._latest_temp, self._latest_hum = self.read_temp_hum()
        except SensorError as e:
            print(f"Sampling failed: {e}")
```

### 9.7 资源管理：上下文管理器

实现 `__enter__`/`__exit__` 支持 `with` 语句自动管理资源：

```python
class SHT30:
    def deinit(self):
        if self._timer:
            self._timer.deinit()
            self._timer = None
        if self._int_pin:
            self._int_pin.irq(handler=None)
            self._int_pin = None
        self._is_init = False

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()
        return False

# 使用示例
with SHT30(i2c, addr=0x44) as sht30:
    sht30.start_periodic_sampling(1000)
    # 退出时自动释放资源
```

### 9.8 参数配置：Setter/Getter 封装

禁止外部直接修改配置属性，通过 `set_xxx()`/`get_xxx()` 方法封装并校验：

```python
class SHT30:
    def set_sampling_rate(self, rate: int) -> None:
        if not (100 <= rate <= 10000):
            raise SensorInvalidParamError("sampling_rate", rate, (100, 10000))
        self._sampling_rate = rate
        if self._timer:
            self.stop_periodic_sampling()
            self.start_periodic_sampling(rate)

    def get_sampling_rate(self) -> int:
        return self._sampling_rate
```

### 9.9 平台兼容性

通过 `sys.platform` 自动适配不同硬件平台的默认引脚：

```python
import sys

class SHT30:
    def __init__(self, i2c=None, addr: int = 0x44):
        if i2c is None:
            platform = sys.platform
            if platform == "esp32":
                i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=400000)
            elif platform == "rp2":
                i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
            elif platform == "esp8266":
                i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
            else:
                raise SensorError(f"Unsupported platform: {platform}")
        self.i2c = i2c
```

### 9.10 数据防抖与缓存

缓存最新有效数据，避免频繁读取硬件；支持连续多次采样取平均：

```python
class SHT30:
    DEBOUNCE_COUNT = 3
    CACHE_EXPIRE   = 500  # ms

    def read_temp_hum(self, debounce: bool = True) -> tuple:
        now = time.ticks_ms()
        if (self._cache_temp is not None and
                time.ticks_diff(now, self._cache_time) < self.CACHE_EXPIRE):
            return self._cache_temp, self._cache_hum

        if debounce:
            temps, hums = [], []
            for _ in range(self.DEBOUNCE_COUNT):
                t, h = self._read_once()
                temps.append(t); hums.append(h)
                time.sleep_ms(10)
            temp = sum(temps) / len(temps)
            hum  = sum(hums)  / len(hums)
        else:
            temp, hum = self._read_once()

        self._cache_temp, self._cache_hum, self._cache_time = temp, hum, now
        return temp, hum
```

---

### 9.11 类型注解与文档字符串

函数签名使用 MicroPython 原生类型注解，文档字符串说明参数、返回值和异常：

```python
def read_temp_hum(self, debounce: bool = True) -> tuple:
    """
    读取温湿度值（支持防抖和缓存）
    Args:
        debounce: 是否开启防抖（默认True）
    Returns:
        tuple: (温度℃, 湿度%RH)
    Raises:
        SensorError: 传感器未初始化
        SensorCommunicationError: I2C通信失败
    """
```

---

### 9.12 单例模式

避免重复初始化硬件资源，使用类变量 `_instance` 实现单例：

```python
class SHT30:
    _instance = None

    @staticmethod
    def get_instance(i2c=None, addr=0x44):
        if SHT30._instance is None:
            SHT30._instance = SHT30(i2c, addr)
        return SHT30._instance
```

---

## 十、测试文件main.py要求

### 10.1 核心设计原则

测试文件遵循 "全量覆盖、灵活调试、安全可控" 原则：

- **全量覆盖**：完整覆盖驱动库所有 API，按芯片类型的核心功能维度拆解接口：

| 芯片类型 | 核心 API 功能维度 |
|---|---|
| 传感器类 | 基础状态查询、核心数据采集、参数配置、模式切换、校准补偿 |
| 电机驱动类 | 硬件初始化、动作控制、状态读取、复位/休眠 |
| 通信模块类 | 网络/协议配置、数据收发、状态查询、功耗控制 |
| 存储芯片类 | 数据读写、地址配置、擦除/复位 |
| GPIO/总线扩展类 | 引脚配置、电平读写、中断配置 |

覆盖正常参数、边界参数、异常参数三类场景：

| 测试场景类型 | 核心验证目标 |
|---|---|
| 正常参数场景 | 验证 API 在默认/常用参数下的基础可用性 |
| 边界参数场景 | 验证 API 对硬件极限参数的适配能力 |
| 异常参数/环境场景 | 验证 API 的容错性与异常反馈能力 |

不同 API 特性的代码处理方式：

| API 特性类型 | 代码处理方式 |
|---|---|
| 低频核心 API | 保留自动执行逻辑，主循环中定期调用 |
| 高频更新 API | 保留函数定义，注释自动执行，供 REPL 手动调用 |
| 模式切换 API | 保留调用代码，注释自动执行，供 REPL 手动触发 |
| 批量操作 API | 封装为批量测试函数，供 REPL 一键调用 |

- **灵活调试**：高频更新/模式切换类函数注释默认自动执行，仅保留函数定义，供 REPL 手动调用。
- **安全可控**：标准化初始化、异常捕获、资源清理，确保无资源泄露、硬件卡死等问题。

---

### 10.2 初始化配置区

硬件对象创建前必须包含 3 秒上电延时和固定格式调试打印：

```python
# ======================================== 初始化配置 ==========================================

# 上电延时3s（强制保留，不可删除）
time.sleep(3)
# 打印调试消息（格式统一：FreakStudio: Using + 硬件/驱动名称 + 功能说明）
print("FreakStudio: Using R60ABD1 millimeter wave information collection")

uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)
processor = DataFlowProcessor(uart)
device = R60ABD1(processor, parse_interval=200)
```

---

### 10.3 文件顶部元信息注释规范

```python
# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/11/4 下午5:33
# @Author  : 李清水
# @File    : main.py
# @Description : 测试R60ABD1雷达设备驱动类的代码
# @License : CC BY-NC 4.0
```

---

### 10.4 固定注释区块顺序

文件内容严格遵循以下区块顺序，每个区块使用统一分隔符 `# ======================================== 区块名称 =========================================`：

```python
# ======================================== 导入相关模块 =========================================
from machine import UART, Pin, Timer
import time
from data_flow_processor import DataFlowProcessor
from r60abd1 import R60ABD1, format_time

# ======================================== 全局变量 ============================================
last_print_time = time.ticks_ms()
print_interval = 2000

# ======================================== 功能函数 ============================================
def print_report_sensor_data():
    """打印高频上报的传感器数据（变化快，默认注释调用）"""
    ...

# ======================================== 自定义类 ============================================
# （无自定义类时可保留空或注释）

# ======================================== 初始化配置 ==========================================
time.sleep(3)
print("FreakStudio: Using R60ABD1 millimeter wave information collection")
uart = UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17), timeout=0)
...

# ========================================  主程序  ===========================================
try:
    while True:
        ...
        # print_report_sensor_data()  # 高频打印函数，注释默认执行，供REPL手动调用
except KeyboardInterrupt:
    ...
finally:
    ...
```

---

### 10.5 异常处理与安全关机规范

```python
# ========================================  主程序  ===========================================
try:
    while True:
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, last_print_time) >= print_interval:
            success, presence_status = device.query_presence_status()
            if success:
                print("Presence Status: %s" % ("Someone" if presence_status == 1 else "No one"))
            else:
                print("Query Presence Status failed")
            last_print_time = current_time
            time.sleep(0.2)
        time.sleep_ms(10)

except KeyboardInterrupt:
    print("%s Program interrupted by user" % format_time())
except OSError as e:
    print("%s Hardware communication error: %s" % (format_time(), str(e)))
except Exception as e:
    print("%s Unknown error: %s" % (format_time(), str(e)))

finally:
    print("%s Cleaning up resources..." % format_time())
    device.close()
    del device
    del uart
    print("%s Program exited" % format_time())
```

---

## 十一、README.md 编写规范

### 11.1 基本结构要求

README.md 必须包含以下章节（按顺序）：

| 章节 | 说明 |
|---|---|
| 项目标题 | `# [传感器/外设名称] MicroPython 驱动` |
| 描述 | 简短介绍驱动作用、主要功能、适用场景 |
| 主要特性 | 列表列出功能亮点 |
| 硬件要求 | 测试硬件表格 + 接线示例 |
| 软件环境 | 固件版本、驱动版本、依赖库 |
| 文件结构 | 文件树结构 |
| 文件说明 | 按文件逐个解释用途 |
| 设计思路 | 驱动实现方式或结构思路（可选） |
| 快速开始 | 分步说明使用流程 + 代码示例 |
| 注意事项 | 芯片工作条件、使用限制、兼容性等 |
| 版本记录 | 表格形式：版本号、日期、作者、修改说明 |
| 联系开发者 | 邮箱或其他联系方式 |
| 许可协议 | CC BY-NC 4.0，区分官方模块（MIT）与自编驱动 |

---

### 11.2 项目标题与描述

```markdown
# RCWL9623 收发一体超声波模块驱动 - MicroPython版本

## 简介
基于RCWL9623芯片的超声波测距模块，支持多种通信模式（GPIO、1-Wire、UART、I2C）。
广泛应用于机器人避障、智能家居测距、安全监测等场景。

> **注意**：不能应用于高精度案例，如安全救生等特殊场合。
```

---

### 11.3 主要特性

用列表列出驱动功能亮点：

```markdown
## 主要功能
- **多种工作模式支持**：GPIO触发/Echo回波、单总线（1-Wire）、UART、I2C
- **测距范围**：约20cm到7m，超出范围返回无效
- **统一单位**：单位统一为厘米（cm）
- **简洁易用**：提供统一接口 `read_distance()`
- **跨平台支持**：兼容多种 MicroPython 兼容开发板
```

---

### 11.4 硬件要求

包含推荐测试硬件和引脚说明表格：

```markdown
## 硬件要求
### 推荐测试硬件
- 树莓派 Pico/Pico W
- RCWL9623 超声波模块

### 模块引脚说明
| 引脚  | 功能描述           |
|-------|--------------------|
| VCC   | 电源正极（3.3V-5V）|
| GND   | 电源负极           |
| TRIG  | 触发引脚（GPIO模式）|
| ECHO  | 回波引脚（GPIO模式）|
| SCL/SDA | I2C通信引脚     |
```

---

### 11.5 文件结构与文件说明

```markdown
## 文件结构
├── rcwl9623.py   # 核心驱动
├── main.py       # 测试示例
└── README.md     # 说明文档

## 文件说明
- `rcwl9623.py`：核心驱动，实现四种工作模式
- `main.py`：示例主程序，循环读取距离
- `README.md`：说明文档
```

---

### 11.6 快速开始

分步说明使用流程，附代码示例：

```markdown
## 快速开始
1. 将 `rcwl9623.py` 上传到开发板
2. 按硬件要求接线
3. 运行示例程序：

\`\`\`python
from machine import Pin
from rcwl9623 import RCWL9623

sensor = RCWL9623(mode=RCWL9623.GPIO_MODE, gpio_pins=(5, 4))
print(sensor.read_distance())
\`\`\`
```

---

### 11.7 许可协议

明确区分官方模块与自编驱动的许可证：

```markdown
## 许可协议
本项目中，除 `machine` 等 MicroPython 官方模块（MIT 许可证）外，
所有由作者编写的驱动与扩展代码均采用
**知识共享署名-非商业性使用 4.0 国际版 (CC BY-NC 4.0)** 许可协议发布。

**版权归 FreakStudio 所有。**
```

---

## 十二、导入规范

```python
# 1. MicroPython 机器相关模块
from machine import Pin, I2C, UART, Timer, SPI

# 2. MicroPython 标准模块
import time
from time import sleep_ms
import ustruct
import math

# 3. micropython 特定模块
from micropython import const

# 4. 第三方 / 项目内部依赖
from pca9685 import PCA9685
```

> **关于 `const()`：** `const()` 在标准 Python 中是未定义名称，会触发 flake8 的 `F821` 错误。项目中已广泛使用，且 flake8 配置未将其屏蔽，提交时如遇此错误需手动添加 `# noqa: F821` 或在 flake8 配置中增加忽略。

---

## 十三、pre-commit 工具链配置

**`.pre-commit-config.yaml`：**

```yaml
repos:
  - repo: git@github.com:psf/black.git
    rev: 24.3.0
    hooks:
      - id: black
        args: [--line-length=150]         # 最大行长 150 字符

  - repo: git@github.com:pycqa/flake8.git
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--ignore=E203,E501,W503", "--max-line-length=150"]

  - repo: local
    hooks:
      - id: run-code-checker
        name: Run Code Checker
        entry: python code_checker.py
        language: system
        pass_filenames: true
        types: [python]
```

**忽略的 Flake8 错误码：**

| 错误码 | 含义 |
|--------|------|
| E203   | 冒号前的空白（Black 格式化会产生） |
| E501   | 行过长（Black 已处理） |
| W503   | 换行在二元运算符之前 |

**Black 重新格式化后的工作流：**

```bash
# Black 修改文件后会返回非零退出码，导致提交失败
# 处理方式：重新暂存已修改的文件，再次提交
git add <被 Black 格式化的文件>
git commit -m "同上次提交信息"
```

**紧急跳过钩子（仅用于紧急情况，用后必须恢复）：**

```bash
# 跳过
git config --local core.hooksPath NUL
# 恢复
git config --local --unset core.hooksPath
```

---

## 十四、package.json 规范

每个驱动目录根目录下必须有一个 `package.json`：

```json
{
  "name": "adxl345_driver",
  "version": "1.0.1",
  "description": "A MicroPython library to control adxl345_driver",
  "author": "leeqingshui",
  "license": "MIT",
  "chips": "all",
  "fw": "all",
  "_comments": {
    "chips": "该包支持运行的芯片型号，all表示无芯片限制",
    "fw": "该包依赖的特定固件如ulab、lvgl,all表示无固件依赖"
  },
  "urls": [
    ["adxl345.py", "code/adxl345.py"]
  ]
}
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | String | ✅ | 包名，小写字母+下划线，与目录名一致 |
| `urls` | 二维数组 | ✅ | 文件映射：`[["目标文件名", "源路径"], ...]` |
| `version` | String | ✅ | 语义化版本号 `主版本.次版本.修订版` |
| `_comments` | Object | ❌ | 注释字段，说明 chips/fw 含义，不影响解析 |
| `description` | String | ❌ | 功能描述（英文） |
| `author` | String | ❌ | 作者信息，参考他人代码需与原作者一致 |
| `license` | String | ❌ | 许可证，参考他人代码遵循原仓库，原创默认 MIT |
| `chips` | String/数组 | ❌ | 支持芯片：`"all"` 或 `["ESP32", "STM32F407"]` |
| `fw` | String/数组 | ❌ | 固件依赖：`"all"` 或 `["ulab", "lvgl"]` |
| `deps` | 数组 | ❌ | 依赖包列表，见 14.4 |

**多文件驱动示例：**

```json
"urls": [
  ["bus_dc_motor.py", "code/bus_dc_motor.py"],
  ["pca9685.py",      "code/pca9685.py"]
]
```

**三种安装方式：**

```python
# 方式一：mip（在设备上运行）
import mip
mip.install("github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/adxl345_driver")

# 方式二：mpremote（命令行）
# mpremote mip install github:FreakStudioCN/GraftSense-Drivers-MicroPython/sensors/adxl345_driver

# 方式三：upypi（推荐，访问 https://upypi.net/ 搜索包名获取命令）
```

### 14.3 示例文件（以 bmp280_driver 为例）

```json
{
  "name": "bmp280_driver",
  "urls": [
    ["bmp280_float.py", "code/bmp280_float.py"]
  ],
  "version": "1.0.0",
  "_comments": {
    "chips": "该包支持运行的芯片型号，all表示无芯片限制",
    "fw": "该包依赖的特定固件如ulab、lvgl,all表示无固件依赖"
  },
  "description": "A MicroPython library to control BMP280 pressure sensor",
  "author": "robert-hh",
  "license": "MIT",
  "chips": "all",
  "fw": "all"
}
```

> 该驱动参考了 robert-hh 的开源代码，`author` 和 `license` 字段与原仓库保持一致。

### 14.4 deps 依赖字段

有外部依赖时使用 `deps` 字段：

```json
{
  "urls": [
    ["mlx90640/__init__.py", "mlx90640/__init__.py"],
    ["mlx90640/utils.py", "mlx90640/utils.py"]
  ],
  "deps": [
    ["collections-defaultdict", "latest"],
    ["os-path", "latest"],
    ["github:org/micropython-additions", "main"],
    ["gitlab:org/micropython-otheradditions", "main"]
  ],
  "version": "0.2"
}
```

第三方平台依赖示例：

```json
{
  "name": "xfyun_asr",
  "version": "1.0.1",
  "description": "iFlytek online ASR WebSocket driver for MicroPython",
  "author": "leeqingsui",
  "license": "MIT",
  "chips": "all",
  "fw": "all",
  "deps": [
    ["https://upypi.net/pkgs/async_websocket_client/1.0.0", "latest"]
  ],
  "urls": [
    ["xfyun_asr.py", "code/xfyun_asr.py"]
  ]
}
```

### 14.5 许可证与版权声明注意事项

- **参考他人代码**：`author` 和 `license` 字段必须与原仓库保持一致；若原仓库无许可证，使用 MIT 并在 README.md 中注明参考来源。
- **原创代码**：使用 FreakStudio 版权声明，遵循 MIT 协议。

---

## 十五、驱动目录结构与命名规范

每个驱动模块的标准目录结构：

```
sensors/adxl345_driver/
├── code/
│   ├── adxl345.py      # 驱动实现（主文件）
│   └── main.py         # 使用示例 / 测试代码
├── package.json         # mip 包配置
├── README.md            # 使用文档（中文）
└── LICENSE              # MIT 许可证文件
```

**分类目录（9 大类）：**

| 目录 | 内容 |
|------|------|
| `sensors/` | 传感器（温湿度、IMU、气体、光线、距离、ECG 等） |
| `communication/` | 通信模块（NFC、4G、蓝牙、RF、以太网） |
| `motor_drivers/` | 电机驱动（直流、步进、舵机） |
| `lighting/` | 显示与照明（LED、OLED、LCD、数码管） |
| `input/` | 输入设备（按键、触摸屏、编码器、摇杆） |
| `signal_acquisition/` | 信号采集（ADC 模块） |
| `signal_generation/` | 信号生成（波形发生器、DAC） |
| `storage/` | 存储（EEPROM、SD 卡） |
| `misc/` | 杂项（RTC、音频、继电器、I2C 多路复用器） |

### 11.1 文件夹命名规范

- 使用小写字母 + 下划线命名，格式：`[传感器名称]_driver` 或 `[功能]_driver`
- 示例：`pca9685_driver`、`bus_dc_motor_driver`

**各文件/文件夹用途说明：**

| 文件 / 文件夹 | 作用说明 |
|--------------|---------|
| `sensor_driver/` | 项目根目录，命名遵循 `[传感器名称]_driver` 规范，作为整个驱动包的容器 |
| `code/` | 源码根目录，烧录到设备时作为代码执行的根目录 |
| `code/sensor.py` | 驱动实现文件，与传感器同名，封装初始化、数据读取、配置等核心逻辑 |
| `code/main.py` | 测试/示例入口文件（也可命名为 `demo.py`），提供使用示例和功能验证代码 |
| `package.json` | 包配置文件，定义名称、版本、文件映射、依赖、兼容芯片/固件等元数据，用于 `mip` 安装 |
| `README.md` | 项目说明文档，包含驱动功能、安装方法、API 参考、注意事项等 |
| `LICENSE` | 开源许可证文件，明确使用、修改和分发规则（MIT） |

### 11.2 驱动文件命名规范

**四条规则：**

1. **小写字母 + 下划线**：文件名全部小写，单词间用下划线分隔
2. **基于传感器/芯片型号**：优先使用传感器型号或芯片型号命名
3. **简洁明确**：文件名准确反映驱动功能，避免模糊命名
4. **避免冲突**：不与 MicroPython 内置模块重名

**命名示例：**

| 传感器/模块 | 规范命名 | 说明 |
|------------|---------|------|
| PCA9685（PWM 控制器） | `pca9685.py` | 直接使用芯片型号 |
| BMP280（气压传感器） | `bmp280.py` | 直接使用传感器型号 |
| DHT11（温湿度传感器） | `dht11.py` | 具体到型号，避免与 `dht22` 混淆 |
| L298N（电机驱动） | `l298n.py` | 优先使用芯片型号 |
| HC-SR04（超声波） | `hc_sr04.py` | 横杠转换为下划线 |
| MPU6050（IMU） | `mpu6050.py` | 直接使用芯片型号 |
| WS2812B（RGB 灯带） | `ws2812b.py` | 避免使用内置模块名 `neopixel` |
| DS18B20（温度传感器） | `ds18b20.py` | 避免使用内置模块名 `ds18x20` |
| 热敏电阻（无型号） | `analog_temp.py` | 按功能命名，确保不与内置模块冲突 |

**需避免的 MicroPython 内置模块名：**

```
machine, time, os, sys, math, network,
uos, usys, utime, ubinascii, ustruct, ucollections,
uhashlib, uheapq, uio, ujson, ure, uzlib,
uarray, uasyncio, ucryptolib, uctypes,
neopixel, dht, ds18x20, onewire
```

---

## 十六、注释风格

驱动文件中的**行内注释全部使用中文**，注释密度较高，以提高可读性：

```python
# 赋值SCL引脚编号
self.scl = scl
# 赋值SDA引脚编号
self.sda = sda
# 设置片选引脚为高电平
cs.value(1)
# 延时1秒等待硬件稳定
time.sleep(1)
# 初始化I2C总线通信对象
self.i2c = I2C(bus, scl=self.scl, sda=self.sda, freq=10000)
# 扫描I2C总线上的从机地址
slv = self.i2c.scan()
```

docstring 使用**中英双语**，行内注释使用**中文**。

---

## 十七、实例属性命名约定

| 场景 | 命名风格 | 示例 |
|------|---------|------|
| 公共属性 | `camelCase` 或 `snake_case` | `self.slvAddr`、`self.scl`、`self.sda` |
| 私有属性 | `_snake_case`（前缀单下划线） | `self._address`、`self._i2c`、`self._measurement_mode` |
| 类级别常量 | `UPPER_CASE` | `MEASUREMENT_MODE_CONTINUOUSLY`、`RESOLUTION_HIGH` |
| 模块级寄存器常量 | `UPPER_CASE` | `DATA_FORMAT`、`POWER_CTL`、`BW_RATE` |

---

## 十八、函数设计规范

### 14.1 设计原则

- **单一职责**：每个函数只做一件事（读取寄存器 / 计算值 / 格式化输出），便于测试与复用
- **小而明确**：复杂流程拆成多个小函数（IO / 解析 / 校验分离），每个函数尽量不超过一屏（20行）
- **无副作用优先**：把带副作用（I2C/SPI 写入/读出/GPIO 控制）的代码与纯计算分开
- **可测试性**：把纯算法放入独立函数，便于在主机端用 unittest/pytest 测试（mock 硬件层）
- **资源意识**：避免在热循环或 ISR 中做大量分配；尽量复用 bytearray/缓冲区

**单一职责示例：**

```python
# 错误：混合职责
def read_temperature():
    i2c.writeto(0x40, b'\xF3')
    time.sleep_ms(50)
    raw = i2c.readfrom(0x40, 2)
    return round((raw[0] << 8 | raw[1]) / 256, 1)

# 正确：职责分离
def _trigger_measurement():
    i2c.writeto(0x40, b'\xF3')

def _read_raw_data():
    return i2c.readfrom(0x40, 2)

def _convert_to_temp(raw) -> float:
    return (raw[0] << 8 | raw[1]) / 256

def get_temperature() -> float:
    _trigger_measurement()
    time.sleep_ms(50)
    return round(_convert_to_temp(_read_raw_data()), 1)
```

**无副作用优先示例：**

```python
# 错误：硬件操作污染计算逻辑
def calculate_pressure():
    i2c.readfrom_mem(addr, 0xF7, buf)
    raw = (buf[0] << 12) | (buf[1] << 4) | (buf[2] >> 4)
    return raw * 0.01

# 正确：隔离副作用
def _read_pressure_raw() -> int:
    i2c.readfrom_mem(addr, 0xF7, buf)
    return (buf[0] << 12) | (buf[1] << 4) | (buf[2] >> 4)

def raw_to_pressure(raw_val: int) -> float:
    return raw_val * 0.01  # 纯函数，无硬件依赖，可独立测试
```

### 14.2 ISR 规范

ISR 只做最小、确定、无分配的工作；把会分配、耗时或可能失败的操作推到主循环或用 `micropython.schedule` 处理。

**规则：**
- 绝对不在 ISR 中分配内存（`bytearray(...)`、字符串拼接、创建列表/元组）
- 不在 ISR 中做阻塞 I/O（I²C/SPI/网络/文件）
- 不在 ISR 中抛异常或 `print`
- 并发访问共享变量时用 `machine.disable_irq()` / `machine.enable_irq()` 保护
- 启动时调用 `micropython.alloc_emergency_exception_buf(100)` 预留调试缓冲

```python
import micropython
micropython.alloc_emergency_exception_buf(100)

# 预分配缓冲（启动时一次性分配）
IRQ_BUF = bytearray(4)

def isr_handler(pin):
    i2c.readfrom_into(addr, IRQ_BUF)  # 零内存分配
    value = IRQ_BUF[0]

# 把重工作推给主线程
def heavy_task(arg):
    do_i2c_read_and_process()

def irq(pin):
    micropython.schedule(heavy_task, 0)  # 立即返回，主线程执行
```

### 14.3 命名规范

- 函数名使用 `snake_case`，动词开头表示行为

| 动词前缀 | 用途 | 示例 |
|---------|------|------|
| `read_` | 读取数据 | `read_temperature`, `read_register` |
| `write_` / `set_` | 写入/设置 | `write_register`, `set_frequency` |
| `get_` | 获取计算值 | `get_status`, `get_humidity` |
| `init_` / `reset_` | 初始化/复位 | `init_sensor`, `reset_device` |
| `_` 前缀 | 私有/内部方法 | `_read_raw`, `_convert_value` |

### 14.4 返回值设计

- 返回明确类型（`bool`/`int`/`float`/`tuple`），避免用 `None` 混合语义
- 多值返回用 `tuple`，在 docstring 说明各元素含义
- 结构化数据用 `dict`，在 docstring 列出所有键
- 原始数据用 `bytearray`，调用方直接解析避免拷贝

```python
def read_acceleration() -> tuple:
    """
    Returns:
        tuple: (x, y, z) 三轴加速度，单位 m/s²。
    """
    return 0.12, -0.05, 9.81

def get_sensor_status() -> dict:
    """
    Returns:
        dict: 包含 'temp'(float,℃)、'humidity'(float,%)、'error_code'(int) 键。
    """
    return {'temp': 23.4, 'humidity': 45.6, 'error_code': 0}
```

### 14.5 日志与调试

库函数默认静默，通过 `debug` 参数控制输出：

```python
class BMP280:
    def __init__(self, i2c, address: int = 0x77, debug: bool = False):
        self.debug = debug
        self._log("BMP280 initialized")

    def _log(self, message: str) -> None:
        if self.debug:
            print("[BMP280]", message)
```

- 示例脚本（`main.py`）可使用详细打印
- 库函数内部不得无条件 `print`，统一走 `_log` 方法

---

## 十九、类型注解规范

### 15.1 注意事项

- **不使用 `typing` 模块**：MicroPython 通常不包含或不完整支持 `typing` 模块
- **仅使用运行时存在的类型**：`int`、`float`、`bool`、`str`、`bytes`、`bytearray`、`list`、`tuple`、`dict`、`None`，以及硬件类如 `I2C`、`Pin`（需先从 `machine` 导入）
- **回调/函数类型**：使用 `callable`（或 `object` + 运行时 `callable()` 检查），在 docstring 中明确回调签名
- **容器元素类型**：不使用 `List[int]` 泛型写法，用 `list` 注解并在 docstring 说明元素类型
- **注解必须可执行**：避免引用不存在的名称；若注解 `I2C`/`Pin`，需在文件顶部导入
- **目的是可读性**：注解用于提高可读性与运行时文档化，配合 `isinstance`/`callable` 做运行时检查，而非静态类型检查

### 15.2 允许使用的注解类型

**可直接使用：**
- 标量：`int`、`float`、`bool`、`str`
- 二进制/缓冲：`bytes`、`bytearray`、`memoryview`
- 集合：`list`、`tuple`、`dict`（元素类型在 docstring 说明）
- 特殊：`None`（用于返回类型 `-> None`）
- 硬件对象：`I2C`、`Pin`（需在文件顶部导入）
- 回调/函数：`callable`（或 `object` 并用 `callable()` 验证）
- 泛用：`object`（当无法或不想更精确时）

**禁止使用：**
- `typing.Any`、`typing.List[int]`、`typing.Optional[...]`、`typing.Callable[...]` 等泛型写法
- 任何第三方 typing 扩展

### 15.3 回调函数注解示例

```python
from machine import I2C

def set_timer_callback(self, callback: callable, period_ms: int) -> None:
    """
    设置定时器回调。

    Args:
        callback (callable): 回调函数，签名为 func(arg:int) -> None。
            回调将在主循环上下文被调用（非 ISR）。
        period_ms (int): 定时周期，单位毫秒。

    Raises:
        ValueError: 当 callback 不是可调用对象，或 period_ms 非法时抛出。

    ==========================================
    Set timer callback function.

    Args:
        callback (callable): Callback function, signature func(arg:int) -> None.
        period_ms (int): Timer period in milliseconds.

    Raises:
        ValueError: If callback is not callable or period_ms is invalid.
    """
    if not callable(callback):
        raise ValueError("callback must be callable")
    if period_ms <= 0:
        raise ValueError("period_ms must be > 0")
    self._cb = callback
    self._period = period_ms
```

---

## 二十、code_checker 手动使用

```bash
# 检查单个文件
python code_checker.py ./sensors/BH1750_driver/code/bh_1750.py

# 检查目录（非递归，仅当前层）
python code_checker.py ./sensors/BH1750_driver/code/

# 检查全仓库（递归遍历所有子目录）
python code_checker.py . -r

# 运行所有 pre-commit 钩子（等效于提交时自动触发）
pre-commit run --all-files

# 安装 pre-commit 钩子（首次克隆仓库后执行）
pre-commit install
```

**输出格式：**

```
[DOING] Checking file: sensors/BH1750_driver/code/bh_1750.py
[PASS]  sensors/BH1750_driver/code/bh_1750.py: All 4 required global variables exist
[PASS]  sensors/BH1750_driver/code/bh_1750.py: # @License : MIT comment exists
[PASS]  sensors/BH1750_driver/code/bh_1750.py: No Chinese in raise/print messages
...
[DONE]  [SUMMARY] Total: 1 | Passed: 1 | Failed: 0
```

---

## 二十一、规范总览速查表

| 规范点 | 适用范围 | 是否自动检查 | 对应规则 |
|--------|---------|:-----------:|--------|
| 文件头 7 行注释（含 `# @License : MIT`） | 非 main.py | 是（`# @License`） | 规则 2 |
| 4 个模块全局变量 | 非 main.py | **是** | 规则 1 |
| 5 个分区标注注释 | 所有文件 | 间接依赖 | 规则 4/5/6 |
| `raise`/`print` 无中文 | 所有文件 | **是** | 规则 3 |
| 全局变量区禁止实例化 | main.py | **是** | 规则 4 |
| 初始化区有 `sleep(3)` 和 FreakStudio print | main.py | **是** | 规则 6 |
| `while` 只在主程序区 | main.py | **是** | 规则 5 |
| `__init__` 参数类型注解 | 所有文件 | **是** | 规则 7 |
| 方法参数校验 + `raise` | 非 main.py | **是** | 规则 8 |
| 中英双语 docstring | 所有类和方法 | 否（约定） | — |
| 行内注释使用中文 | 所有文件 | 否（约定） | — |
| Black 格式化（行长 150） | 所有文件 | **是**（pre-commit） | — |
| `package.json` 完整字段 | 每个驱动目录 | 否（工具辅助） | — |

---

*文档版本：1.0 | 生成日期：2026-04-09 | 基于仓库 commit: `1fb7f3e`*

---

## 二十二、规范化改写优先级表（Skill 专用）

> 本节供 `/upy-norm-driver`、`/upy-norm-main`、`/upy-gen-main`、`/upy-gen-readme`、`/upy-gen-pkg` 五个 skill 使用。
> **核心约束（所有 skill 通用）**：改写过程中不得修改对外 API 名称、方法签名语义、核心业务逻辑、硬件通信时序。

---

### 22.1 `/upy-norm-driver` 驱动文件规范化

**P0 — 必改（code_checker 强制 + 可读性基础）**

| # | 改写项 | 规范来源 |
|---|---|---|
| 1 | 补全文件头 7 行注释，`# @License : MIT` 独立成行；`@Author` 从原文件 `__author__` 字段读取并沿用，若无则提示用户填写，不得使用占位符 | 二 |
| 2 | 补全 `__version__`、`__author__`、`__license__`、`__platform__`；`__author__` 从原文件读取并沿用 | 三 |
| 3 | 补全 6 个分区标注注释，顺序正确；驱动文件末尾初始化配置区和主程序区留空但必须存在 | 四 |
| 4 | 所有 `raise`/`print` 字符串改为英文 | 五·规则3 |
| 5 | `__init__` 所有参数加类型注解，返回值注解 `-> None`；参数校验必须在初始化逻辑之前 | 五·规则7、六·6.6 |
| 6 | 每个有参数的方法加参数校验 + `raise` | 五·规则8、六·6.8 |
| 7 | 类和每个公共方法加中英双语 docstring（含 Args/Returns/Raises/Notes）；Notes 中标注副作用和 ISR-safe | 六·6.4、6.7、6.12 |
| 8 | 行内注释改为中文；**注释必须写在对应代码行上方（独立注释行），禁止写在代码行末尾（行尾 `#` 注释）** | 十六 |
| 9 | 公共方法返回值加类型注解（仅用 MicroPython 原生类型，禁用 typing 泛型） | 十九·15.1 |
| 10 | 类级常量改用 `micropython.const()` + `UPPER_CASE` 命名 | 六·6.5 |
| 11 | 私有属性加 `_` 前缀，公共属性遵循命名约定 | 十七 |
| 12 | 异常类型规范化：参数错误 `ValueError`，I/O 错误 `RuntimeError`/`DeviceError` | 八·8.2 |
| 13 | 底层 I/O 捕获 `OSError` 后包装重抛，保留 `from e` | 八·8.3 |
| 14 | 补全 `deinit()` 方法，释放硬件资源 | 六·6.3 |
| 15 | 类结构布局：类级常量→`__init__`→公共方法→`@property`→私有方法→`deinit()` | 六·6.3 |
| 16 | 显式依赖注入：不在类内创建硬件总线对象（I2C/SPI/UART），硬件实例必须作为参数传入 `__init__` | 六·6.1 |
| 16a | 引脚参数改为总线实例：若原驱动传入 I2C/UART 引脚号（`scl_pin`/`sda_pin` 等），改写为接受 `I2C`/`UART` 实例参数 | 六·6.1 |
| 16b | INT 引脚改为回调注入：若原驱动传入中断引脚号，改写为接受 Pin 实例 + `callback: callable` + `trigger: int`（默认 `Pin.IRQ_FALLING`），在 `__init__` 内完成 `pin.irq()` 注册 | 六·6.1 |
| 16c | 定时器改为实例注入：若原驱动内部创建 `machine.Timer`，改写为接受外部传入的 Timer 实例 | 六·6.1 |
| 17 | 函数命名遵循动词前缀约定（`read_`/`set_`/`get_`/`init_`/`reset_`/`_`私有） | 十八·14.3 |
| 18 | 多值返回改用 `tuple`，原始数据用 `bytearray`，避免 `None` 混合语义 | 十八·14.4 |
| 19 | 通用功能（CRC、单位转换）抽离到类外 | 九·9.1 |
| 20 | 固定硬件参数和默认配置声明为类属性大写常量 | 九·9.3 |
| 21 | 配置属性通过 `set_xxx()`/`get_xxx()` 封装，禁止外部直接修改 | 九·9.8 |
| 22 | 瞬态 I2C/SPI 错误可实现有限重试（2-3次），提供可选参数 `retries=1, delay_ms=5` | 八·8.4 |
| 23 | debug 日志开关：通过 `debug` 参数控制，统一走 `_log()` 方法，不得无条件 `print` | 十八·14.5 |

**P2 — 可选（按实际代码硬件特性决定）**

| # | 改写项 | 适用场景 | 规范来源 |
|---|---|---|---|
| 24 | ISR 回调改用 `micropython.schedule` | 有中断回调 | 九·9.5、十八·14.2 |
| 25 | 高频读取改用 bytearray 复用缓冲区 | 有频繁 I/O | 四·4.1 |
| 26 | 添加 `__enter__`/`__exit__` 上下文管理器 | 需资源自动释放 | 九·9.7 |
| 27 | 平台兼容性适配（`sys.platform` 判断） | 多平台部署 | 九·9.9 |
| 28 | 数据防抖与缓存 | 高频采样传感器 | 九·9.10 |
| 29 | 单例模式（`_instance`/`get_instance()`） | 硬件资源唯一性 | 九·9.12 |
| 30 | 非阻塞采样改用 `machine.Timer` | 有 `time.sleep` 阻塞主循环 | 九·9.6 |
| 31 | 自定义异常类（`SensorError` 等） | 复杂错误场景 | 九·9.2 |

---

### 22.2 `/upy-norm-main` 测试文件规范化

**P0 — 必改**

| # | 改写项 | 规范来源 |
|---|---|---|
| 1 | 补全文件头 7 行注释 | 十·10.3 |
| 2 | 补全 6 个分区标注注释，顺序正确 | 十·10.4 |
| 3 | 初始化配置区必须有 `time.sleep(3)` | 十·10.2、五·规则6 |
| 4 | 初始化配置区必须有 `print("FreakStudio: ...")` | 十·10.2、五·规则6 |
| 5 | 全局变量区禁止实例化，实例化移至初始化配置区 | 五·规则4 |
| 6 | `while` 循环只允许在主程序区 | 五·规则5 |
| 7 | 所有 `raise`/`print` 字符串改为英文 | 五·规则3 |
| 8 | 主程序区用 `try/except KeyboardInterrupt/OSError/Exception/finally` 包裹 | 十·10.5 |
| 9 | `finally` 中调用 `device.close()`/`deinit()`，`del` 硬件对象，打印退出提示 | 十·10.5 |
| 10 | 行内注释改为中文；**注释必须写在对应代码行的上方（独立注释行），禁止写在代码行末尾（行尾 `#` 注释）** | 十六 |

**P1 — 尽量改**

| # | 改写项 | 规范来源 |
|---|---|---|
| 11 | 高频更新/模式切换函数注释默认调用，保留定义供 REPL 手动调用 | 十·10.1 |
| 12 | 检查已有测试代码是否覆盖正常参数场景、边界参数场景、异常参数场景，缺少的场景应补全调用代码 | 十·10.1 |
| 12a | 若驱动使用 I2C，检查初始化配置区是否包含完整扫描逻辑（`i2c.scan()` 为空报错、遍历找目标地址报错、读取芯片 ID 比对）；缺少则补全；ID 寄存器地址和期望值须声明为全局变量区 `UPPER_CASE` 常量 | 十·10.2 |
| 13 | 功能函数加简短中文 docstring | 十·10.4 |
| 14 | 全局变量命名遵循 `snake_case` | 十八·14.3 |

**P2 — 可选**

| # | 改写项 | 适用场景 |
|---|---|---|
| 15 | 批量操作封装为独立函数供 REPL 一键调用 | 有多个同类 API |

---

### 22.3 `/upy-gen-main` 从 0 生成测试文件

**生成原则**：分析驱动文件所有公共 API，按芯片类型功能维度（基础状态查询、核心数据采集、参数配置、模式切换、校准补偿）全量覆盖，正常/边界/异常三类参数场景均需覆盖。

**必须包含**

| # | 内容 | 规范来源 |
|---|---|---|
| 1 | 文件头 7 行注释；`@Author` 从驱动文件 `__author__` 字段读取并沿用，若无则提示用户填写，不得使用占位符 | 十·10.3 |
| 2 | 6 个分区标注注释，顺序正确 | 十·10.4 |
| 3 | 初始化配置区：`time.sleep(3)` + `print("FreakStudio: ...")` + 硬件对象实例化 | 十·10.2 |
| 3a | I2C 设备扫描 + ID 验证：① `i2c.scan()` 为空则 `raise RuntimeError("No I2C device found")`；② 遍历列表找目标地址，未找到则 `raise RuntimeError("Device not found at expected address")`；③ 读取芯片 ID 寄存器与期望值比对，打印 "Device found"/"Device not found"；④ ID 寄存器地址和期望值声明为全局变量区 `UPPER_CASE` 常量；⑤ 扫描所需额外 `import` 放导入区，不得在初始化配置区内 `import` | 十·10.2 |
| 4 | 所有公共 API 的调用代码（低频保留自动执行，高频/模式切换注释调用） | 十·10.1 |
| 5 | 主程序区 `try/except KeyboardInterrupt/OSError/Exception/finally` + 资源清理（`close()`/`deinit()`、`del`、退出提示） | 十·10.5 |
| 6 | `raise`/`print` 全英文；行内注释中文，**注释必须写在代码行上方（独立注释行），禁止行尾 `#` 注释** | 五·规则3、十六 |

---

### 22.4 `/upy-gen-readme` 从 0 生成 README

**生成原则**：扫描用户指定目录下所有 `.py` 文件（必须重新读取，不得使用缓存），综合驱动文件和 `main.py` 分析后生成。

**P0 — 全部必须生成**

| # | 章节 | 内容要求 | 规范来源 |
|---|---|---|---|
| 1 | 标题 | `# [名称] MicroPython 驱动` | 十一·11.2 |
| 2 | 目录 | 所有章节的锚点链接 | 十一·11.1 |
| 3 | 简介/描述 | 驱动作用、主要功能、适用场景 | 十一·11.2 |
| 4 | 主要特性 | 列表列出功能亮点 | 十一·11.3 |
| 5 | 硬件要求 | 推荐硬件表格 + 引脚说明表格；引脚配置从 `main.py` 的 `I2C()`/`SPI()`/`UART()`/`Pin()` 实例化语句提取实际引脚号 | 十一·11.4 |
| 6 | 软件环境 | 固件版本、驱动版本、依赖库 | 十一·11.1 |
| 7 | 文件结构 | 文件树 | 十一·11.5 |
| 8 | 文件说明 | 按文件逐个解释用途 | 十一·11.5 |
| 9 | 快速开始 | 分步说明 + 代码示例；**快速开始代码示例直接复制 `main.py` 完整内容，不截取、不改写、不自行编造** | 十一·11.6 |
| 10 | 注意事项 | 工作条件、使用限制、兼容性；I2C 地址从 `main.py` 全局变量区的地址常量提取 | 十一·11.1 |
| 11 | 版本记录 | 表格：版本号、日期、作者、修改说明 | 十一·11.1 |
| 12 | 联系方式 | 邮箱或 GitHub | 十一·11.1 |
| 13 | 许可协议 | MIT License 完整说明 | 十一·11.7 |

**输出格式要求**：输出前自检，确认所有代码块均有配对的开闭 ` ``` ` 标记，不得遗漏任何一个。

**P2 — 可选**

| # | 章节 | 适用场景 |
|---|---|---|
| 14 | 设计思路 | 有复杂实现逻辑值得说明 |

---

### 22.5 `/upy-gen-pkg` 从 0 生成 package.json

**P0 — 必须生成**

| # | 生成项 | 规范来源 |
|---|---|---|
| 1 | `name`：小写字母+下划线，与目录名一致 | 十四·14.2 |
| 2 | `urls`：扫描目录下所有 `.py` 文件（排除 `main.py`），每个文件生成一条映射；多文件驱动包含所有驱动文件 | 十四·14.2 |
| 3 | `version`：默认 `"1.0.0"` | 十四·14.2 |
| 4 | `_comments`：固定中文说明对象 | 十四·14.2 |
| 5 | `description`：从驱动文件 `@Description` 或 docstring 提取，英文 | 十四·14.2 |
| 6 | `chips`：默认 `"all"` | 十四·14.2 |
| 7 | `fw`：默认 `"all"` | 十四·14.2 |
| 8 | `author`/`license`：参考他人代码与原仓库一致，原创用 FreakStudio/MIT | 十四·14.5 |

**deps 依赖生成三步优先级**

| 步骤 | 判断 | 处理方式 |
|---|---|---|
| 1 | MicroPython 内置模块（`machine`、`time`、`sys` 等） | 不写入 deps |
| 2 | micropython-lib 标准库（`collections`、`os` 等） | 用 mip 标准格式写入 |
| 3 | 其他第三方依赖 | 查询 `https://upypi.net/api/search?q={依赖名}`；**查询失败（网络限制）时提示用户在浏览器访问该 URL 并将 JSON 结果粘贴回来，收到结果后继续处理；用户无法访问则使用 `github:` 占位格式并标注 ⚠️ 需手动确认**；无结果同样用 `github:` 格式并标注 ⚠️ | 十四·14.4 |

---

### 22.6 `/upy-norm-pkg` 驱动包全流程规范化

**定位**：已有验证过的驱动文件，对整个驱动包目录执行全套规范化流程的 Orchestrator Skill。

**执行流程**

| 步骤 | 操作 | 条件 |
|---|---|---|
| 0 | 扫描目录，分类驱动文件与 `main.py`；多驱动文件时列出并询问用户确认范围 | 必须 |
| 1 | 对每个驱动文件依次执行 `/upy-norm-driver`，每个文件完成后暂停确认 | 必须 |
| 2 | 执行 `/upy-norm-main`（有 `main.py`）或 `/upy-gen-main`（无 `main.py`） | 必须 |
| 3 | 执行 `/upy-gen-readme` | 必须 |
| 4 | 执行 `/upy-gen-pkg` | 必须 |
| 5 | 执行 `/upy-pack-driver` | 必须 |

**关键规则**

- 每步完成后显示 `[步骤 X/5 — skill名称: 文件名 完成]`，暂停等待用户确认再继续
- 用户回复"修改"或"重做"时，重新执行当前步骤，不影响已完成步骤
- 多驱动文件时，`gen-readme`/`gen-pkg`/`pack-driver` 基于目录中第一个驱动文件执行

---

### 22.7 `/upy-opt-driver` 驱动性能优化

**定位**：已规范化的驱动文件，按 GraftSense 性能优化指南改写，聚焦**执行速度**提升。

**优化优先级**

| 优先级 | 项目 | 典型提速 | 说明 |
|---|---|---|---|
| P0 | 预分配缓冲区 | 消除 GC 抖动 | `_BUFn` 全局复用，`readinto()` 替代 `read()` |
| P0 | `memoryview` 切片 | 零拷贝 | 切片 > 32 字节时用 `memoryview`，避免副本创建 |
| P0 | 缓存对象引用 | 5–20% | 循环 > 100 次时，`self.xxx` 缓存到局部变量 |
| P0 | `const()` 常量 | 零开销 | 模块级常量用 `const()` 包裹，编译时替换 |
| P1 | 手动 GC 控制 | 可控延迟 | 批量操作前 `gc.collect()`，避免中途随机触发 |
| P1 | `@native` 装饰器 | ~2 倍 | 大量字节码执行，无生成器/关键字参数 |
| P1 | `@viper` 装饰器 | ~58 倍（整数） | 整数运算为主，无浮点/默认参数/生成器 |
| P1 | 整数替代浮点 | ~57% | 无 FPU 芯片（RP2040/ESP8266）循环内浮点改整数 |
| P2 | `viper ptr8/ptr16/ptr32` | ~23 倍 | 大循环遍历 `bytearray`，指针转换放循环外 |
| P2 | SIO 寄存器直写 | ~48% | RP2040 专属，高频 GPIO 翻转（> 1000 次/秒） |
| P2 | `array` 替代 `list` | 连续内存 | 大量同类型数值存储 |

**关键约束**

- `@viper` 改写必须在 docstring Notes 中标注整数溢出风险和位宽限制
- `@native` 改写必须在 docstring Notes 中标注限制（无生成器、无关键字参数）
- SIO 寄存器操作必须标注"RP2040 专属，其他平台不可用"
- 支持单文件模式和多文件模式（目录扫描 → 逐文件处理 → 暂停确认）

---

### 22.8 `/upy-slim-driver` 驱动内存占用优化

**定位**：已规范化的驱动文件，按 GraftSense 内存最小化指南改写，聚焦**RAM 占用**降低。

**优化优先级**

| 优先级 | 项目 | 典型节省 | 说明 |
|---|---|---|---|
| P0 | 预分配缓冲区 | 消除峰值堆分配 | 与 `upy-opt-driver` P0#1 重叠，不重复执行 |
| P0 | 私有 `_CONST` | ~40 字节/常量 | 模块内部常量用 `_CONST`，不写入全局字典 |
| P0 | 避免循环字符串 `+` | 消除临时对象 | 用 `.join()` + 生成器或 `.format()` |
| P0 | `bytes`/`bytearray` 替代 `list` | ~90%（寄存器表） | 同类型数值容器，100 个地址节省 ~700 字节 |
| P1 | `gc.collect()` 前置 | 降低随机性 | 批量操作前手动触发，避免中途打断 |
| P1 | `gc.disable()`/`gc.enable()` | 防止 GC 中途打断 | 时序敏感帧传输，必须 `try/finally` 包裹 |
| P1 | `struct.pack_into()` | 消除临时 bytes | 复用预分配缓冲区，零堆分配 |
| P2 | `__slots__` | 50–200 字节/实例 | 固定属性集合，禁用 `__dict__` |
| P2 | 生成器替代列表 | 峰值 RAM O(N)→O(1) | 大列表（> 50 元素）流式处理 |
| P2 | `micropython.mem_info()` | 诊断用 | 用户明确要求时添加，标注 `# [调试]` |

**关键约束**

- `_CONST` 改写仅适用于模块内部常量；外部引用的公共常量保留原名
- `gc.disable()` 区间必须短且有界，禁止包含可能阻塞的 I/O
- 与 `upy-opt-driver` 的 P0#1（预分配缓冲区）重叠，不重复执行
- 支持单文件模式和多文件模式（目录扫描 → 逐文件处理 → 暂停确认）

**与 `upy-opt-driver` 的关系**

| 维度 | `upy-opt-driver`（性能） | `upy-slim-driver`（内存） |
|---|---|---|
| 目标 | 执行速度（时间复杂度） | RAM 占用（空间复杂度） |
| 重叠项 | P0#1 预分配缓冲区 | P0#1 预分配缓冲区 |
| 重叠处理 | 从"消除 GC 抖动"角度改写 | 从"降低峰值 RAM"角度改写，若已执行则跳过 |
| 互补性 | `@viper`/`@native`/`ptr` 提速 | `_CONST`/`__slots__`/生成器降内存 |
