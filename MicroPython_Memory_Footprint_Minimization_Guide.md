# 如何最小化 MicroPython 占用内存

# 一、前置概念

MicroPython 的核心应用场景是**微控制器（如树莓派 Pico、ESP32、ESP8266）**，这类设备的硬件资源与电脑 / 服务器存在数量级的差距 —— 通常 RAM（运行内存）只有几十 KB 到几百 KB，Flash（存储内存）也仅几 MB。而 Python 代码本身具有动态性，运行时会占用一定的内存资源，因此在微控制器上使用 MicroPython 时，内存优化是保证程序稳定运行的关键。本文将详细介绍 MicroPython 内存优化的方法，其中会对新手不易理解的专有名词进行标注解释，同时为核心知识点提供可在 REPL（MicroPython 交互式命令行）中运行的测试代码，帮助你边学边验证。

在学习具体优化方法前，先理解以下核心专有名词，能让后续内容更易理解：

---

# 二、优化方法

## 2.1 基本概念

在学习具体优化方法前，先理解以下核心专有名词，能让后续内容更易理解：

- **RAM（随机存取存储器）**：又称运行内存，是微控制器用于临时存储运行中的代码、数据的区域，特点是读写速度快，但断电后数据丢失，且容量极小（树莓派 Pico 的 RAM 为 264KB）。
- **Flash（闪存）**：又称存储内存，是微控制器用于永久存储固件、用户代码、数据的区域，特点是断电后数据不丢失，容量比 RAM 大，但读写速度较慢（树莓派 Pico 的 Flash 为 2MB）。
- **字节码**：MicroPython 不会直接执行人类编写的源码（.py 文件），而是先将源码编译为一种介于源码和机器码之间的中间代码（即字节码），再由 MicroPython 解释器执行。字节码的体积更小，执行效率更高。
- **固件**：烧录到微控制器 Flash 中的底层软件，包含 MicroPython 解释器、硬件驱动等核心功能，是 MicroPython 运行的基础。
- **REPL**：即 Read-Eval-Print Loop（读取 - 执行 - 打印循环），是 MicroPython 的交互式命令行工具（如 Thonny 的 Shell 面板、串口工具的交互窗口），可以逐行输入代码并立即执行，是新手调试、测试代码的必备工具。
- **SPI 总线**：一种串行外设接口（Serial Peripheral Interface），是微控制器与外部设备（如 SD 卡、传感器）通信的常用协议，具有接线简单、传输速度快的特点。

---

## 2.2 安装 SD 卡

支持 MicroPython 的开发板可以通过插入 SD 卡的方式扩展内存，首先需要将卡格式化为 **FAT/FAT32 格式（一种通用的文件系统格式，被绝大多数设备支持，也是 MicroPython 识别 SD 卡的必要格式）**。通常使用 SPI 总线 挂在 SD 卡，插卡后 MicroPython 会从 SD 卡启动，如果 SD 卡上有 boot.py 和 main.py，在启动时也会自动执行。

我们也可以从内部 flash 启动而又使用 SD 卡保存数据，这时需要在 SD 卡根目录中设置一个 SKIPSD 文件，当系统启动时检查到 SD 上存在这个文件，就会忽略 SD 卡，仍然从内部 Flash 启动。

关于 MicroPython 在 SD 卡上的使用，可以看下面的教程：

[08 SPI 串行外设接口-文档教程初稿](https://f1829ryac0m.feishu.cn/docx/G4P7dNfYso36YLxVlCQc6V4snUc)

在树莓派 pico 上使用 SD 卡可以参考教程：（待补充）

---

## 2.3 使用 frozen 模块和 frozen 字节码

实际开发中我们往往有多个 .py 文件存放不同的代码，main.py 文件运行主要的业务流程，main.py 通过 import 语句引用其他 .py 文件 / 模块 / 包完成整个工作（例如其他传感器的类）。main.py 文件和其他文件往往都处于开发板文件系统的根目录。

从文件系统上的 Python 文件加载模块和包来存储和运行代码有一些很大的限制，这些 Python 代码必须由 MicroPython 的解释器加载和处理，该过程需要耗费时间和内存，甚至有的情况下这些代码文件太大，无法加载到 Flash 内存并由 MicroPython 的解释器处理。Frozen 模块（冻结模块）和 Frozen 字节码（冻结字节码）可以将 Python 代码编译为 native 代码 / 字节码并将其和固件存储，这样做可以压缩内存。一旦代码被冻结，MicroPython 就可以快速加载和解释它，而无需太多的内存和处理时间。

### 2.3.1 Python 字节码

MicroPython 代码先被编译为字节码后，再由解释器来执行字节码，MicroPython 的字节码是一种类似汇编指令的中间语言，一个 MicroPython 语句会对应若干字节码指令，解释器顺序执行字节码指令，从而完成程序执行。

代码被预编译为字节码，避免了在加载时编译 MicroPython 源代码的需要。字节码可以直接从 Flash 执行，而不需要复制到 RAM 中。同样，任何常量对象（如字符串、元组等）也从 ROM 加载。这可以使得更多的内存可用于应用程序。在没有文件系统的设备上，这是加载 Python 代码的唯一方式。

### 2.3.2 生成冻结模块和字节码的步骤

一个生成冻结模块和字节码的步骤通常如下：

1. **准备 MicroPython 源码**：从 GitHub 克隆 MicroPython 仓库，确保本地有完整的编译环境（如 `arm-none-eabi-gcc`）。
2. **将模块放入 `ports/<平台>/modules/` 目录**：例如 `ports/rp2/modules/`，将需要冻结的 `.py` 文件放在此目录。
3. **编译固件**：执行 `make` 命令重新编译固件，编译过程会自动将该目录下的 `.py` 文件编译为冻结字节码并嵌入固件。
4. **烧录固件到开发板**：将编译产生的 `.uf2` 或 `.bin` 固件烧录到设备。
5. **在代码中正常 import**：冻结后的模块可像普通模块一样用 `import` 语句加载，无需额外操作。

### 2.3.3 MicroPython 的 frozen 的主要特点

MicroPython 的 frozen 的主要特点是：

- **存储位置**：冻结模块存储在 Flash（ROM）而非 RAM，不占用宝贵的运行内存。
- **加载速度快**：无需在运行时编译，直接由解释器执行，启动速度更快。
- **节省 RAM**：字节码和常量对象直接从 Flash 运行，不需要将其复制到 RAM 中。
- **适合无文件系统设备**：在没有文件系统的设备上，这是加载 Python 代码的唯一方式。
- **编译时确定**：冻结模块在编译固件时确定，运行时不可动态修改。

使用冻结模块和冻结字节码可以参考教程：（待补充）

---

## 2.4 使用 .mpy 文件

将 python 模块预编译为字节码（也称为 .mpy 文件（MicroPython 的预编译字节码文件格式，区别于标准 Python 的 .pyc 文件）），然后将其复制到开发板上。**这样做的优点是可以跳过开发板上的预编译阶段，从而避免在此过程中没有 RAM 资源。不幸的是，这种方法仍然需要开发板将模块加载到 RAM 中。**

将 python 模块转换为 .c 文件，该文件被编译到固件本身中。具有上述方法的优点 + 具有从闪存运行模块而不是将其加载到 RAM 中的优点。

.mpy 文件生成与使用步骤可以参考：[如何加快 MicroPython 的运行速度](https://f1829ryac0m.feishu.cn/docx/BVTZdXCMCobRbFxuM8jcNCEMndc)

---

## 2.5 使用 const 常量

### 2.5.1 MicroPython 命名空间和作用域

MicroPython 中所有加载到 RAM 的模块都会放在 `sys.modules`，`sys.modules` 是一个全局字典，从 python 程序启动就加载到了内存，用于保存当前已导入（加载）的所有模块名和模块对象。在 MicroPython 的模块查找中，它起到缓存作用，避免了模块的重复加载。

程序在导入某个模块时，会首先查找 `sys.modules` 中是否包含此模块名，若存在，则只需将模块的名字加入到当前模块的 `Local` 命名空间中；若不存在，则需要从 `sys.path` 目录中按照模块名称查找模块文件，找到后将模块加载到内存，并加入到 `sys.modules` 字典，最后将模块的名字加入当前模块的 `Local` 命名空间中。

接下来，我们在终端的 `REPL` 中进行测试：

```python
import sys

# sys.modules显示当前已导入 (加载) 的所有模块名和模块对象
print("Initial modules:")
print(list(sys.modules.keys()))

# 定义全局变量
global_var = "I am a global variable"

# enclosing_var 闭包外层变量
# local_var 函数inner_function内部局部变量
# len 是内置函数
# 尝试修改全局变量global_var （不使用global会创建局部变量）
# 闭包外层无法访问内部局部变量
def scope_demo():
    enclosing_var = "I am an enclosing variable (outer of closure)"
    
    def inner_function():
        local_var = "I am a local variable"
        
        print("Local variable:", local_var)
        print("Enclosing variable:", enclosing_var)
        print("Global variable:", global_var)
        print("Built-in function example:", len("test"))
        
        try:
            global_var = "Trying to modify"
        except:
            pass
    
    inner_function()
    
    try:
        print(local_var)
    except:
        print("Cannot access local variable")

# 使用global修改全局变量
def modify_global():
    global global_var
    global_var = "Modified global variable"
    print("Inside function:", global_var)

# 多层嵌套中的nonlocal使用
# 内部middle()函数和inner()函数中修改嵌套作用域中的变量outer_var
def nonlocal_demo():
    outer_var = "Outer layer"
    
    def middle():
        nonlocal outer_var
        outer_var = "Modified by middle layer"
        
        def inner():
            nonlocal outer_var
            outer_var = "Modified by inner layer"
        
        inner()
        print("In middle:", outer_var)
    
    middle()
    print("In nonlocal_demo:", outer_var)

# 作用域演示
print("\n=== Scope Demonstration ===")
scope_demo()
print("Access in global scope:", global_var)

# 修改全局变量
print("\n=== Modify Global Variable ===")
modify_global()
print("In global scope:", global_var)

# nonlocal演示
print("\n=== nonlocal Demonstration ===")
nonlocal_demo()

# 尝试访问内置作用域
import builtins
print("Built-in module:", builtins)
```

终端运行，输出如下：

**图1：REPL 输入 scope_demo 函数定义过程**

```
(base) PS G:\test_microMLP> mpremote
Connected to MicroPython at COM65
Use Ctrl-] or Ctrl-x to exit this shell

>>> import sys
>>> print("Initial modules:")
Initial modules:
>>> print(list(sys.modules.keys()))
['rp2']
>>> global_var = "I am a global variable"
>>> def scope_demo():
...     enclosing_var = "I am an enclosing variable (outer of closure)"
...
...     def inner_function():
...         local_var = "I am a local variable"
...
...         print("Local variable:", local_var)
...         print("Enclosing variable:", enclosing_var)
...         print("Global variable:", global_var)
...         print("Built-in function example:", len("test"))
...
...         try:
...             global_var = "Trying to modify"
...         except:
...             pass
...
...     inner_function()
...
...     try:
...         print(local_var)
...     except:
...         print("Cannot access local variable")
...
>>> scope_demo()
```

**图2：scope_demo 执行结果（局部变量访问异常）**

```
>>> scope_demo()
Local variable: I am a local variable
Enclosing variable: I am an enclosing variable (outer of closure)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<stdin>", line 17, in scope_demo
  File "<stdin>", line 9, in inner_function
NameError: local variable referenced before assignment
```

> **注意**：在 `inner_function` 内部，当 `try` 块中出现 `global_var = "Trying to modify"` 赋值语句时，Python 编译器会认为 `global_var` 是一个局部变量，因此在 `print("Global variable:", global_var)` 处抛出 `NameError: local variable referenced before assignment`，因为局部变量在赋值前被引用了。

**图3：modify_global 函数定义及执行**

```
>>> def modify_global():
...     global global_var
...     global_var = "Modified global variable"
...     print("Inside function:", global_var)
...
>>> modify_global()
```

**图4：nonlocal_demo 执行结果**

```
>>> def nonlocal_demo():
...     outer_var = "Outer layer"
...
...     def middle():
...         nonlocal outer_var
...         outer_var = "Modified by middle layer"
...
...         def inner():
...             nonlocal outer_var
...             outer_var = "Modified by inner layer"
...
...         inner()
...         print("In middle:", outer_var)
...
...     middle()
...     print("In nonlocal_demo:", outer_var)
...
>>> nonlocal_demo()
In middle: Modified by inner layer
In nonlocal_demo: Modified by inner layer
```

**图5：内置模块访问**

```
>>> import builtins
>>> print("Built-in module:", builtins)
Built-in module: <module 'builtins'>
>>>
```

> **LEGB 规则总结**：MicroPython 中变量查找顺序为 Local（局部）→ Enclosing（闭包外层）→ Global（全局）→ Built-in（内置），即 LEGB 规则。`global` 关键字用于在函数内声明访问全局变量，`nonlocal` 关键字用于在嵌套函数中声明访问外层（非全局）变量。

---

### 2.5.2 const 常量的定义与优化原理

常量是指在程序执行期间不会发生变化的值，一般用于存储不可更改的数据，比如数学常数、配置信息等。在单片机中常量会保存在 ROM/Flash 闪存中，可以节省 RAM 空间。

MicroPython 中的关键字 `const` 用于声明表达式是常量，以便编译器对其进行优化，在将常量分配给变量的两种情况下，编译器将避免通过替换常量的文字值来编写对常量名称的查找。这可以节省字节码，从而节省 RAM。

**不过需要注意的是，使用关键字 `const` 时候，需要使用 mpy-cross 工具编译为 mpy 文件才能发挥其作用。**

```python
from micropython import const
# 垃圾回收模块，用于查看内存使用情况
import gc

# 第一步：查看初始内存使用情况
# 强制垃圾回收，释放无用内存
gc.collect()
initial_free = gc.mem_free()
print(f"Initial free RAM: {initial_free} bytes")

# 第二步：定义const常量
# 公开常量（模块外能访问，仅占极少量RAM）
CONST_X = const(123)
CONST_Y = const(2 * 123 + 1)
# 私有常量（以下划线开头，模块外不能访问，完全不占用RAM）
_COLS = const(0x10)
ROWS = const(33)

# 第三步：使用常量
a = ROWS
b = _COLS
print(f"CONST_X: {CONST_X}, CONST_Y: {CONST_Y}")
print(f"a: {a}, b: {b}")

# 第四步：查看定义常量后的内存使用情况
gc.collect()
after_free = gc.mem_free()
print(f"Free RAM after defining constants: {after_free} bytes")
print(f"RAM change: {after_free - initial_free} bytes (positive means memory freed)")

# 补充：对比普通变量与const常量的区别
# 普通变量，存储在RAM中
normal_var = 123  
gc.collect()
after_normal = gc.mem_free()
print(f"Free RAM after defining normal variable: {after_normal} bytes")
print(f"Normal variable uses {after_free - after_normal} more bytes than const")
```

`ROWS` 值将占用至少两个机器字，全局字典中的键和值各一个。字典中的存在是必要的，因为另一个模块可能会导入或使用它。可以通过在名称前面添加下划线来保存此 RAM，如 `_COLS` 所示：此符号在模块外部不可见，因此不会占用 RAM。

终端运行结果如下：

**图6：const 常量测试输出**

```
Windows PowerShell
版权所有 (C) Microsoft Corporation。保留所有权利。

尝试新的跨平台 PowerShell https://aka.ms/pscore6

加载个人及系统配置文件用了 570 毫秒。
(base) PS G:\test_microMLP> mpremote
Connected to MicroPython at COM65
Use Ctrl-] or Ctrl-x to exit this shell

>>> from micropython import const
>>> import gc
>>> gc.collect()
>>> initial_free = gc.mem_free()
>>> print(f"Initial free RAM: {initial_free} bytes")
Initial free RAM: 228416 bytes
>>> CONST_X = const(123)
>>> CONST_Y = const(2 * 123 + 1)
>>> _COLS = const(0x10)
>>> ROWS = const(33)
>>> a = ROWS
>>> b = _COLS
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name '_COLS' isn't defined
>>> print(f"CONST_X: {CONST_X}, CONST_Y: {CONST_Y}")
CONST_X: 123, CONST_Y: 247
>>> print(f"a: {a}, b: {b}")
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'b' isn't defined
>>> gc.collect()
>>> after_free = gc.mem_free()
>>> print(f"Free RAM after defining constants: {after_free} bytes")
Free RAM after defining constants: 228176 bytes
>>> print(f"RAM change: {after_free - initial_free} bytes (positive means memory freed)")
RAM change: -240 bytes (positive means memory freed)
>>> normal_var = 123
>>> gc.collect()
>>> after_normal = gc.mem_free()
>>> print(f"Free RAM after defining normal variable: {after_normal} bytes")
Free RAM after defining normal variable: 228000 bytes
>>> print(f"Normal variable uses {after_free - after_normal} more bytes than const")
Normal variable uses 176 more bytes than const
>>>
```

> **关键观察**：
> - `_COLS` 以下划线开头，是私有常量，在 REPL 中直接访问 `b = _COLS` 会报 `NameError`，因为它不会出现在全局命名空间中。
> - 普通变量 `normal_var = 123` 比 `const` 常量多占用 176 字节 RAM，验证了 `const` 的内存优化效果。
> - `CONST_Y = const(2 * 123 + 1)` 正确输出 247，说明 `const()` 支持编译时整数表达式。

`const()` 的参数必须是任何在编译时计算结果为整数的值。

```python
from micropython import const

ROWS = const(33)
# 下面用法报错
COLS = const(0x10+ROWS)
# 正确用法
COLS = const(0x10+33)
```

终端输出如下：

**图7：const 错误用法示例**

```
Windows PowerShell
版权所有 (C) Microsoft Corporation。保留所有权利。

尝试新的跨平台 PowerShell https://aka.ms/pscore6

加载个人及系统配置文件用了 808 毫秒。
(base) PS G:\test_microMLP> mpremote
Connected to MicroPython at COM65
Use Ctrl-] or Ctrl-x to exit this shell

>>> from micropython import const
>>> ROWS = const(33)
>>> COLS = const(0x10+ROWS)
Traceback (most recent call last):
  File "<stdin>", line 1
SyntaxError: not a constant
>>> COLS = const(0x10+33)
>>>
```

> `const(0x10+ROWS)` 报 `SyntaxError: not a constant`，因为 `ROWS` 是一个符号名，在当前 REPL 上下文中不能在编译时求值。正确做法是将字面值直接写入：`const(0x10+33)`。

---

## 2.6 减少不必要的对象创建

在 MicroPython 中，**对象（如字符串、列表、字典、字节数组、数值容器等）的创建会占用 RAM 资源。由于微控制器的 RAM 容量极小，频繁创建和销毁对象不仅会直接消耗内存，还会导致内存碎片化**（即 RAM 中出现大量小的空闲内存块，无法被大对象使用），最终引发内存不足的问题。

需要注意的是，标准 Python 中的 `sys.getsizeof()` 函数在 MicroPython 中大部分平台不支持（这是 MicroPython 的特性，为了精简固件），因此我们可以通过 `struct` 模块将变量 / 数据打包为字节流，再通过 `len()` 函数获取字节流的长度，以此来测试数据占用的字节大小；同时结合 `gc` 模块（垃圾回收）查看 RAM 的实际使用变化，完成优化前后的对比。

### 2.6.1 字符串操作优化（避免临时字符串对象）

MicroPython 中的字符串是不可变对象，使用 `+` 拼接字符串时，每一次 `+` 都会创建一个临时字符串对象（比如 `"a"+"b"+"c"` 会先创建 `"ab"`，再创建 `"abc"`，共 2 个临时对象），这些临时对象会占用额外的 RAM，且会被垃圾回收器频繁清理，影响性能。

优化思路：

```python
# 静态字符串拼接（编译时合并，无临时对象）
static_str = "MicroPython" "Memory" "Opt"
print("Static string:", static_str)

# 动态字符串（推荐format，减少临时对象）
temp = 25.5
press = 101325
dynamic_str = "Temp: {:.2f}, Press: {:d}".format(temp, press)
print("Dynamic string:", dynamic_str)
```

### 2.6.2 硬件操作中的缓冲区复用（UART/SPI/I2C 场景）

在 MicroPython 的硬件操作中（如 SPI 读取传感器数据、UART 接收数据），频繁创建新的字节缓冲区（`bytearray`/`bytes`）会占用大量 RAM。例如，每次读取传感器都创建 `buf = bytearray(10)`，循环 100 次就会创建 100 个缓冲区对象。

我们可以提前分配一个缓冲区，在循环 / 多次操作中复用，仅创建一次对象，彻底避免临时缓冲区的创建。

下面我们预分配串口接收缓冲区，循环中复用，避免重复创建 `bytearray`。

```python
from machine import UART, Pin

# 初始化UART
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
# 预分配缓冲区（仅创建1次）
uart_buf = bytearray(16)

# 循环接收（复用缓冲区）
for _ in range(5):
    uart.readinto(uart_buf)
    print("UART data:", uart_buf)
```

下面，我们预分配 SPI 读写缓冲区，复用减少内存开销。

```python
from machine import SPI, Pin

# 初始化SPI
spi = SPI(0, baudrate=1000000, sck=Pin(2), mosi=Pin(3), miso=Pin(4))
# 预分配缓冲区
spi_buf = bytearray(8)

# 循环读写（复用缓冲区）
for _ in range(5):
    spi.readinto(spi_buf)
    print("SPI data:", spi_buf)
```

### 2.6.3 数值存储优化（用 struct/bytearray 代替列表）

在 MicroPython 中，列表存储数值（如 `[1, 2, 3, 255]`）会占用较多 RAM，因为列表中的每个整数对象都有额外的内存开销（比如一个 `int` 类型在 MicroPython 中占 4 字节，而列表本身还有指针开销）。

优化思路：

```python
# 1. str vs bytes（内存占用一致，ASCII场景）
# String (ASCII)
s = 'the quick brown fox'  
# Bytes (1 byte per char)
b = b'the quick brown fox' 
print("String:", s)
print("Bytes:", b)

# 2. 字符串与字节的转换（注意：转换会创建新对象）
# str -> bytes
s_to_b = s.encode()  
# bytes -> str
b_to_s = b.decode()  
print("Str->Bytes:", s_to_b)
print("Bytes->Str:", b_to_s)

# 3. bytes支持字符串方法（如lstrip）
foo = b'  empty whitespace'
foo_stripped = foo.lstrip()
print("Stripped bytes:", foo_stripped)
```

终端运行，输出如下：

**图8：bytes 与 str 操作测试输出**

```
版权所有 (C) Microsoft Corporation。保留所有权利。

尝试新的跨平台 PowerShell https://aka.ms/pscore6

加载个人及系统配置文件用了 685 毫秒。
(base) PS G:\test_microMLP> mpremote
Connected to MicroPython at COM65
Use Ctrl-] or Ctrl-x to exit this shell

>>> s = 'the quick brown fox'
>>> b = b'the quick brown fox'
>>> print("String:", s)
String: the quick brown fox
>>> print("Bytes:", b)
Bytes: b'the quick brown fox'
>>> s_to_b = s.encode()
>>> b_to_s = b.decode()
>>> print("Str->Bytes:", s_to_b)
Str->Bytes: b'the quick brown fox'
>>> print("Bytes->Str:", b_to_s)
Bytes->Str: the quick brown fox
>>> foo = b'  empty whitespace'
>>> foo_stripped = foo.lstrip()
>>> print("Stripped bytes:", foo_stripped)
Stripped bytes: b'empty whitespace'
>>>
```

### 2.6.4 避免循环中的临时容器创建

在循环中频繁创建临时容器（如 `for _ in range(100): temp = [1,2,3]`）会创建大量临时对象，占用 RAM。优化思路是将临时容器移到循环外，复用对象，或使用生成器 / 迭代器代替临时列表。

```python
import gc
import struct

# 初始化垃圾回收，建立测试基线
gc.collect()
ram_init = gc.mem_free()

# 定义循环次数（模拟多次迭代场景）
loop_times = 100

# ---------------------- 低效实现：循环内创建临时列表 ----------------------
# 循环内每次创建新的列表容器，产生大量临时对象
gc.collect()
ram_slow_before = gc.mem_free()
total_slow = 0

# 每次循环创建新列表[1,2,3,4,5]
# struct测试列表数据的字节大小（打包为5个整数，用'i'格式）
for _ in range(loop_times):
    temp_list = [1, 2, 3, 4, 5]
    total_slow += sum(temp_list)
    
    size_slow = len(struct.pack("5i", *temp_list))
# 记录低效实现后的RAM
ram_slow_after = gc.mem_free()

# ---------------------- 高效实现1：循环外创建列表，复用容器 ----------------------
# 列表仅创建一次，循环内复用
gc.collect()
ram_fast1_before = gc.mem_free()
total_fast1 = 0

# 临时列表移到循环外（仅创建1次）
# struct测试复用列表的字节大小（与低效实现一致）
temp_list_reuse = [1, 2, 3, 4, 5]
for _ in range(loop_times):
    total_fast1 += sum(temp_list_reuse)
    
    size_fast1 = len(struct.pack("5i", *temp_list_reuse))
# 记录高效实现1后的RAM
ram_fast1_after = gc.mem_free()

# ---------------------- 高效实现2：使用生成器，替代临时列表 ----------------------
# 定义生成器函数（仅创建一次，循环内复用迭代器）
# 直接yield元素，避免元组创建
def num_generator():
    yield 1
    yield 2
    yield 3
    yield 4
    yield 5
    
# 生成器不创建完整列表，仅迭代生成元素，内存开销最低
gc.collect()
ram_fast2_before = gc.mem_free()
total_fast2 = 0

# 生成器表达式（无临时列表对象）
# struct测试生成器数据的字节大小（打包为5个整数）
for _ in range(loop_times):
    total_fast2 += sum(num_generator())
    size_fast2 = len(struct.pack("5i", 1, 2, 3, 4, 5))
# 记录高效实现2后的RAM
ram_fast2_after = gc.mem_free()

# 输出测试结果（无中文）
print("Slow total:", total_slow)
print("Slow RAM change:", ram_slow_before - ram_slow_after)
print("Slow data size:", size_slow)

print("Fast1 total:", total_fast1)
print("Fast1 RAM change:", ram_fast1_before - ram_fast1_after)
print("Fast1 data size:", size_fast1)

print("Fast2 total:", total_fast2)
print("Fast2 RAM change:", ram_fast2_before - ram_fast2_after)
print("Fast2 data size:", size_fast2)
```

终端运行结果如下：

**图9：循环临时容器测试输出**

```
...     yield 2
...     yield 3
...     yield 4
...     yield 5
...
>>> gc.collect()
>>> ram_fast2_before = gc.mem_free()
>>> total_fast2 = 0
>>> for _ in range(loop_times):
...     total_fast2 += sum(num_generator())
...     size_fast2 = len(struct.pack("5i", 1, 2, 3, 4, 5))
...
>>> ram_fast2_after = gc.mem_free()
>>> print("Slow total:", total_slow)
Slow total: 1500
>>> print("Slow RAM change:", ram_slow_before - ram_slow_after)
Slow RAM change: 10528
>>> print("Slow data size:", size_slow)
Slow data size: 20
>>>
>>> print("Fast1 total:", total_fast1)
Fast1 total: 1500
>>> print("Fast1 RAM change:", ram_fast1_before - ram_fast1_after)
Fast1 RAM change: 5888
>>> print("Fast1 data size:", size_fast1)
Fast1 data size: 20
>>>
>>> print("Fast2 total:", total_fast2)
Fast2 total: 1500
>>> print("Fast2 RAM change:", ram_fast2_before - ram_fast2_after)
Fast2 RAM change: 8720
>>> print("Fast2 data size:", size_fast2)
Fast2 data size: 20
>>>
```

> **结果分析**：
>
> | 实现方式 | RAM 变化（字节）| 说明 |
> |---|---|---|
> | 循环内创建临时列表（低效）| 10528 | 100次循环创建100个列表对象，RAM消耗最大 |
> | 循环外复用列表（高效1）| 5888 | 仅创建一次列表，内存开销最小 |
> | 使用生成器（高效2）| 8720 | 每次调用创建生成器对象，开销介于两者之间 |
>
> 在小数据量（5 个固定数）重复 100 次的场景下，列表复用确实比生成器更省内存；当需要处理大量数据或流式数据时，生成器避免了一次性加载所有数据。

### 2.6.5 避免运行时编译器执行（`eval`/`exec`）

`eval()`/`exec()` 会在运行时调用 MicroPython 编译器，创建大量临时对象，消耗大量 RAM；直接计算或使用 `json` 序列化替代，可减少内存开销。

```python
import gc
import struct
import json

# ---------------------- 低效：使用eval ----------------------
gc.collect()
ram_eval_before = gc.mem_free()
# 避免使用eval，此处仅作对比
res_eval = eval("1 + 2 * 3 + 4 / 2")
ram_eval_after = gc.mem_free()

# ---------------------- 高效：直接计算 ----------------------
gc.collect()
ram_calc_before = gc.mem_free()
res_calc = 1 + 2 * 3 + 4 / 2
ram_calc_after = gc.mem_free()

# ---------------------- 高效：ujson序列化 ----------------------
gc.collect()
ram_json_before = gc.mem_free()
# 序列化
data = {"temp": 25.5, "press": 101325}
json_data = json.dumps(data)
# 反序列化
size_json = len(struct.pack(f"{len(json_data.encode())}s", json_data.encode()))
data_loaded = json.loads(json_data)
ram_json_after = gc.mem_free()

# 输出测试结果
print("Eval RAM change:", ram_eval_before - ram_eval_after)
print("Calc RAM change:", ram_calc_before - ram_calc_after)
print("JSON size:", size_json)
print("JSON RAM change:", ram_json_before - ram_json_after)
```

终端运行结果如下：

**图10：eval vs 直接计算 vs json 内存对比**

```
>>> import gc
>>> import struct
>>> import json
>>> gc.collect()
>>> ram_eval_before = gc.mem_free()
>>> res_eval = eval("1 + 2 * 3 + 4 / 2")
>>> ram_eval_after = gc.mem_free()
>>> gc.collect()
>>> ram_calc_before = gc.mem_free()
>>> res_calc = 1 + 2 * 3 + 4 / 2
>>> ram_calc_after = gc.mem_free()
>>> gc.collect()
>>> ram_json_before = gc.mem_free()
>>> data = {"temp": 25.5, "press": 101325}
>>> json_data = json.dumps(data)
>>> size_json = len(struct.pack(f"{len(json_data.encode())}s", json_data.encode()))
>>> data_loaded = json.loads(json_data)
>>> ram_json_after = gc.mem_free()
>>> print("Eval RAM change:", ram_eval_before - ram_eval_after)
Eval RAM change: 592
>>> print("Calc RAM change:", ram_calc_before - ram_calc_after)
Calc RAM change: 384
>>> print("JSON size:", size_json)
JSON size: 31
>>> print("JSON RAM change:", ram_json_before - ram_json_after)
JSON RAM change: 1488
>>>
```

> **结果分析**：
>
> | 操作方式 | RAM 变化（字节）| 说明 |
> |---|---|---|
> | `eval()` 动态解析 | 592 | 调用编译器，产生大量临时对象 |
> | 直接计算 | 384 | 无编译开销，内存消耗最低 |
> | `json.dumps()/loads()` | 1488 | 序列化字符串和字典，产生更多临时对象 |
>
> 我们可以看到，动态解析（`eval()`）和 JSON 处理会创建大量隐藏的临时对象，这正是微控制器上内存碎片化的典型表现——表面简单的操作背后隐藏着指数级的内存消耗。

### 2.6.6 在闪存中存储字符串（`qstr` 机制）

MicroPython 的 `qstr` 量化字符串机制会将重复的字符串存储在闪存中，而非 RAM，减少 RAM 占用，我们可以通过 `micropython.qstr_info()` 查看字符串存储状态，用 `struct` 测试字符串字节大小，用 `gc` 查看 RAM 变化。

```python
import gc
import struct
import micropython

# 初始化垃圾回收
gc.collect()
ram_init = gc.mem_free()

# 定义测试字符串（会被qstr机制处理）
s1 = "MicroPython"
# 重复字符串，复用闪存中的qstr
s2 = "MicroPython"  

# struct测试字符串字节大小
size_s = len(struct.pack(f"{len(s1.encode())}s", s1.encode()))

# 打印qstr信息（1表示详细输出）
micropython.qstr_info(1)

# 记录RAM
ram_after = gc.mem_free()

# 输出测试结果
print("String size:", size_s)
print("RAM free:", ram_after)
```

终端输出结果如下：

**图11：qstr 字符串存储机制测试**

```
Windows PowerShell
版权所有 (C) Microsoft Corporation。保留所有权利。

尝试新的跨平台 PowerShell https://aka.ms/pscore6

加载个人及系统配置文件用了 675 毫秒。
(base) PS G:\test_microMLP> mpremote
Connected to MicroPython at COM65
Use Ctrl-] or Ctrl-x to exit this shell

>>> import gc
>>> import struct
>>> import micropython
>>> gc.collect()
>>> ram_init = gc.mem_free()
>>> s1 = "MicroPython"
>>> s2 = "MicroPython"
>>> size_s = len(struct.pack(f"{len(s1.encode())}s", s1.encode()))
>>> micropython.qstr_info(1)
qstr pool: n_pool=1, n_qstr=5, n_str_data_bytes=26, n_total_bytes=170
Q(ram_init)
Q(s1)
Q(s2)
Q(size_s)
Q({}s)
>>> ram_after = gc.mem_free()
>>> print("String size:", size_s)
String size: 11
>>> print("RAM free:", ram_after)
RAM free: 227152
>>>
```

我们可以看到，`s1` 和 `s2` 两个字符串内容相同，都是 `"MicroPython"`，MicroPython 的 qstr 机制会重用相同字符串，实际上 `s1` 和 `s2` 指向同一个内存中的字符串对象，同时节省了重复存储相同字符串的内存。

`qstr` 信息分析如下：

```
>>> micropython.qstr_info(1)
qstr pool: n_pool=1, n_qstr=5, n_str_data_bytes=26, n_total_bytes=170
Q(ram_init)
Q(s1)
Q(s2)
Q(size_s)
Q({}s)
```

关键信息解析：

| 字段 | 值 | 含义 |
|---|---|---|
| `n_pool` | 1 | qstr 池数量，当前有 1 个 qstr 池 |
| `n_qstr` | 5 | 当前 RAM 中的 qstr 数量（变量名本身，非字符串内容）|
| `n_str_data_bytes` | 26 | 变量名字符串数据总字节数（`ram_init`+`s1`+`s2`+`size_s`+`{}s` 的字节数之和）|
| `n_total_bytes` | 170 | qstr 池占用的总字节数（含元数据、对齐等）|

> **注意**：`"MicroPython"` 这个字符串没有在列出的 qstr 中，是因为 MicroPython 将它作为只读数据存储在 Flash 中，而不是 RAM 中。列出的 `Q(s1)`、`Q(s2)` 是变量名 `s1`、`s2` 本身被内化为 qstr，而不是字符串值 `"MicroPython"`。

---

## 2.7 堆与垃圾回收机制

堆是一块动态分配的内存区域，用于存储程序运行时创建的对象实例和动态数据结构（比如 Python 中的列表、字典、自定义类的实例）：

当你执行 `lst = [1,2,3]` 时，Python 会：

1. 在**堆**中分配一块内存区域，用于存储列表对象 `[1,2,3]`
2. 在**栈**中创建变量 `lst`，作为指向该堆内存区域的引用（指针）

堆中的对象如果没有任何引用指向它（即程序无法再访问到该对象），这个对象就成为「垃圾」：例如执行 `lst = None` 后，原本堆中的 `[1,2,3]` 对象就失去了引用，变成垃圾。

MicroPython 中 GC 垃圾回收可以自动识别并清理堆中的垃圾对象，释放占用的内存，避免内存泄漏（内存被无用对象一直占用，导致程序可用内存越来越少，最终崩溃）。

垃圾回收的触发方式包括以下两种：

1. **自动触发**：由 MicroPython 运行时在分配内存时自动检测并触发（通过 `gc.enable()` 启用，默认开启）。可通过 `gc.threshold(n)` 设置累计分配阈值，达到阈值后自动触发一次 GC。
2. **手动触发**：通过调用 `gc.collect()` 手动触发垃圾回收，适合在执行大内存操作前主动释放内存。

MicroPython 的 `gc` 模块常用核心方法如下：

| 方法 | 说明 |
|---|---|
| `gc.collect()` | 手动触发垃圾回收，清理所有不可达对象 |
| `gc.mem_free()` | 返回当前空闲堆内存字节数 |
| `gc.mem_alloc()` | 返回当前已分配堆内存字节数 |
| `gc.enable()` | 启用自动垃圾回收 |
| `gc.disable()` | 禁用自动垃圾回收（用于手动控制 GC 时机）|
| `gc.isenabled()` | 查询自动 GC 是否开启，返回 True/False |
| `gc.threshold(n)` | 设置 GC 触发阈值（字节），累计分配达到 n 字节后自动 GC；无参数调用则返回当前阈值；传 -1 禁用阈值 |

下面是我们的测试代码：

```python
# 导入gc模块，用于操作垃圾回收（mpy版）
import gc

# 1. 查看自动GC是否开启（部分mpy版本支持）
print(gc.isenabled())

# 2. 禁用自动GC，方便手动控制测试过程
gc.disable()
print(gc.isenabled())

# 3. 查看初始的空闲堆内存和已分配堆内存（mpy专属方法）
print(f"Free heap: {gc.mem_free()} bytes")
print(f"Allocated heap: {gc.mem_alloc()} bytes")

# 4. 演示gc.threshold()方法：设置并查询GC分配阈值（mpy专属方法）
# 设置阈值为1024字节，累计分配1024字节后触发GC（提前回收减少碎片）
gc.threshold(1024)
# 无参数时查询当前阈值
current_threshold = gc.threshold()  
print(f"Current GC threshold: {current_threshold} bytes")

# 5. 创建普通对象，占用堆内存（变量是栈中的引用，指向堆对象）
# 创建更大的列表，内存变化更明显
obj1 = [1, 2, 3, 4, 5]  
obj2 = {"name": "test", "age": 18}
print("Objects created")

# 6. 查看创建对象后的内存变化
print(f"Free heap after create: {gc.mem_free()} bytes")
print(f"Allocated heap after create: {gc.mem_alloc()} bytes")

# 7. 切断引用，让对象成为垃圾（堆中对象无引用指向）
obj1 = None
obj2 = None
print("References cut, objects become garbage")

# 8. 查看切断引用后的内存（未GC，内存未释放）
print(f"Free heap before collect: {gc.mem_free()} bytes")
print(f"Allocated heap before collect: {gc.mem_alloc()} bytes")

# 9. 手动触发GC，清理垃圾对象
# mpy中部分版本无返回值，故移除接收变量
gc.collect()  
print("Garbage collection executed")

# 10. 查看GC后的内存变化（垃圾被清理，空闲内存增加）
print(f"Free heap after collect: {gc.mem_free()} bytes")
print(f"Allocated heap after collect: {gc.mem_alloc()} bytes")

# 11. 演示循环引用的垃圾回收（引用计数法无法处理，需gc.collect()）
a = []
b = []
# a引用b, b引用a，形成循环引用
a.append(b)  
b.append(a) 
print("Circular reference objects created")

# 12. 查看创建循环引用对象后的内存
print(f"Free heap after circular ref: {gc.mem_free()} bytes")
print(f"Allocated heap after circular ref: {gc.mem_alloc()} bytes")

# 13. 切断外部引用，此时a和b互相引用，引用计数不为0
a = None
b = None
print("External references cut (circular ref remains)")

# 14. 手动触发GC，清理循环引用的垃圾
gc.collect()
print("Garbage collection for circular ref executed")

# 15. 查看清理循环引用后的内存
print(f"Free heap after circular collect: {gc.mem_free()} bytes")
print(f"Allocated heap after circular collect: {gc.mem_alloc()} bytes")

# 16. 恢复自动GC，并重置阈值为默认（-1表示禁用阈值）
gc.threshold(-1)
print(f"Reset GC threshold: {gc.threshold()}")
gc.enable()
print(gc.isenabled())
```

运行终端，输出如下：

**图12：GC 测试输出（第一部分）**

```
尝试新的跨平台 PowerShell https://aka.ms/pscore6

加载个人及系统配置文件用了 810 毫秒。
(base) PS G:\test_microMLP> mpremote
Connected to MicroPython at COM65
Use Ctrl-] or Ctrl-x to exit this shell

>>> import gc
>>> print(gc.isenabled())
True
>>> gc.disable()
>>> print(gc.isenabled())
False
>>> print(f"Free heap: {gc.mem_free()} bytes")
Free heap: 227040 bytes
>>> print(f"Allocated heap: {gc.mem_alloc()} bytes")
Allocated heap: 6368 bytes
>>> gc.threshold(1024)
>>> current_threshold = gc.threshold()
>>> print(f"Current GC threshold: {current_threshold} bytes")
Current GC threshold: 1024 bytes
>>> obj1 = [1, 2, 3, 4, 5]
>>> obj2 = {"name": "test", "age": 18}
>>> print("Objects created")
Objects created
>>> print(f"Free heap after create: {gc.mem_free()} bytes")
Free heap after create: 224832 bytes
>>> print(f"Allocated heap after create: {gc.mem_alloc()} bytes")
Allocated heap after create: 8608 bytes
>>> obj1 = None
>>> obj2 = None
>>> print("References cut, objects become garbage")
References cut, objects become garbage
>>> print(f"Free heap before collect: {gc.mem_free()} bytes")
Free heap before collect: 223472 bytes
>>> print(f"Allocated heap before collect: {gc.mem_alloc()} bytes")
Allocated heap before collect: 9968 bytes
>>> gc.collect()
>>> print("Garbage collection executed")
Garbage collection executed
```

**图13：GC 测试输出（第二部分）**

```
Allocated heap before collect: 9968 bytes
>>> gc.collect()
>>> print("Garbage collection executed")
Garbage collection executed
>>> print(f"Free heap after collect: {gc.mem_free()} bytes")
Free heap after collect: 227696 bytes
>>> print(f"Allocated heap after collect: {gc.mem_alloc()} bytes")
Allocated heap after collect: 5744 bytes
>>> a = []
>>> b = []
>>> a.append(b)
>>> b.append(a)
>>> print("Circular reference objects created")
Circular reference objects created
>>> print(f"Free heap after circular ref: {gc.mem_free()} bytes")
Free heap after circular ref: 225904 bytes
>>> print(f"Allocated heap after circular ref: {gc.mem_alloc()} bytes")
Allocated heap after circular ref: 7552 bytes
>>> a = None
>>> b = None
>>> print("External references cut (circular ref remains)")
External references cut (circular ref remains)
>>> gc.collect()
>>> print("Garbage collection for circular ref executed")
Garbage collection for circular ref executed
>>> print(f"Free heap after circular collect: {gc.mem_free()} bytes")
Free heap after circular collect: 227664 bytes
>>> print(f"Allocated heap after circular collect: {gc.mem_alloc()} bytes")
Allocated heap after circular collect: 5792 bytes
>>> gc.threshold(-1)
>>> print(f"Reset GC threshold: {gc.threshold()}")
Reset GC threshold: -1
>>> gc.enable()
>>> print(gc.isenabled())
True
>>>
```

整体流程如下图所示：

**图14：GC 整体流程图**

```
[初始化GC状态]
  GC已启用
  空闲内存: 227040B
  已分配内存: 6368B
  总内存: ~233KB
       ↓
[禁用自动GC]
       ↓
[设置GC阈值=1024B]
       ↓
[创建对象obj1, obj2]
  obj1 = [1,2,3,4,5]
  obj2 = {"name":"test","age":18}
  空闲↓2208B → 224832B
  已分配↑2240B → 8608B
       ↓
[切断对象引用]
  obj1 = None
  obj2 = None
  对象成为垃圾
  空闲↓1360B → 223472B
  已分配↑1360B → 9968B
       ↓
[执行手动GC]
  垃圾回收执行
  空闲↑4224B → 227696B
  已分配↓4224B → 5744B
  释放内存: 4224B
       ↓
[创建循环引用]
  a = [], b = []
  a.append(b), b.append(a)
  创建循环引用
  空闲↓1792B → 225904B
  已分配↑1808B → 7552B
       ↓
[切断外部引用]
  a = None, b = None
  循环引用孤岛形成
       ↓
[执行GC回收循环引用]
  标记-清除算法工作
  空闲↑1760B → 227664B
  已分配↓1760B → 5792B
  释放内存: 1760B
       ↓
[重置GC配置]
  GC阈值 = -1 (自动管理)
  重新启用GC
```

内存变化如下表所示：

| 操作阶段 | 空闲堆内存（B）| 已分配堆内存（B）| 说明 |
|---|---|---|---|
| 初始化 | 227040 | 6368 | 总计 ~233KB |
| 创建 obj1, obj2 | 224832 | 8608 | 空闲减少 2208B |
| 切断引用（未 GC） | 223472 | 9968 | 垃圾未回收，内存反而继续消耗 |
| 手动 GC 后 | 227696 | 5744 | 释放 4224B，内存恢复 |
| 创建循环引用 | 225904 | 7552 | 空闲减少 1792B |
| 切断外部引用（未 GC）| 225904 | 7552 | 孤岛未回收，内存无变化 |
| GC 回收循环引用 | 227664 | 5792 | 标记-清除算法释放 1760B |

我们也可以使用 `micropython.mem_info(1)` 方法查看堆利用率表：

**图15：`micropython.mem_info(1)` 输出**

```
>>> import micropython
>>> micropython.mem_info(1)
stack: 516 out of 7936
GC: total: 233024, used: 7168, free: 225856
 No. of 1-blocks: 96, 2-blocks: 26, max blk sz: 64, max free sz: 14075
GC memory layout; from 200071c0:
00000000: h=MLhhhhDhhh===DhhhDBDBh===BSB=hh====B=BBBBBBBB=BhB=BBBSB=BBhB=Bh
00000400: ===DB=h============h=========================BBBBh==h=hh=========h=======
00000800: ==========h======================================================================
00000c00: ==========h======================================================================
00001000: ==========h====ShShSBhh=h==hhh=Sh=Sh=hh===h====h===hhhh=Bhh=Sh==
00001400: =h=h==h==Bhhh=======h========hSh====h==h==hh=Shhhhhhh=hh==Bhh=h=h
00001800: hh=h===hh===Bh=hhh=hhh==Bh=hhhhhh==B....h=h..h====h====.h....h=h
00001c00: ==.h.................h===..h..hh.B...h.......................
        (219 lines all free)
00038c00: ..............................
```

这是 MicroPython 的内存信息详细输出，用于查看栈和堆的整体状态，是分析内存的基础：

```yaml
stack: 516 out of 7936
GC: total: 233024, used: 7168, free: 225856
 No. of 1-blocks: 96, 2-blocks: 26, max blk sz: 64, max free sz: 14075
...（内存布局省略）
```

- **stack: 516 out of 7936**：栈内存已使用 516 字节，总大小 7936 字节。栈内存用于存储局部变量、函数调用上下文，这里栈使用量很小，处于安全状态。
- **GC: total: 233024, used: 7168, free: 225856**：堆内存的核心统计（单位：字节）：
  - `total`：堆内存总大小（233024 字节）。
  - `used`：当前已分配的堆内存（7168 字节），即程序中对象占用的堆空间。
  - `free`：当前空闲的堆内存（225856 字节），可用于分配新对象。
- **块信息（1-blocks/2-blocks 等）**：MicroPython 的堆内存以「块」为单位分配，这里显示了不同大小块的数量、最大块大小、最大空闲块大小，反映了堆的碎片化程度。
  - `No. of 1-blocks: 96`：大小为 1 块的已分配块有 96 个。
  - `2-blocks: 26`：大小为 2 块的已分配块有 26 个。
  - `max blk sz: 64`：已分配块中最大的块大小为 64 块。
  - `max free sz: 14075`：最大连续空闲块大小为 14075 块。
- **内存布局**：以字符形式展示堆内存的使用状态：
  - `h` 表示已用块（head of an allocation）
  - `=` 表示空闲块
  - `D`/`B`/`S`/`M`/`L` 是特殊标记（分别代表字典、字节数组、字符串、module 等对象类型）
  - `219 lines all free` 表示大部分堆内存都是空闲的，整体内存健康。

---

# 参考资料

- [MicroPython 官方文档 - 参考手册](https://docs.micropython.org/en/latest/reference/index.html)
- [08 SPI 串行外设接口-文档教程初稿](https://f1829ryac0m.feishu.cn/docx/G4P7dNfYso36YLxVlCQc6V4snUc)
- [如何加快 MicroPython 的运行速度](https://f1829ryac0m.feishu.cn/docx/BVTZdXCMCobRbFxuM8jcNCEMndc)
