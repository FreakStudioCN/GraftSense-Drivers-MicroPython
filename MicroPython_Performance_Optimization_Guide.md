# 如何加快 MicroPython 的运行速度

# 一、优化步骤

我们可以把 MicroPython 的代码优化过程比作"给自行车提速的步骤"**：先找到自行车跑得慢的核心原因（比如轮胎没气、链条卡顿），再从简单的调整开始（充气、上油），最后再考虑更换高端零件（轻量化车架、碳纤维轮组）。MicroPython 的代码优化也遵循**"从简单到复杂、从软件到硬件"的顺序，这样能以最低的成本获得最大的性能提升，避免一开始就陷入复杂的底层优化而浪费时间。

在开始优化前，先搞懂几个核心基础概念：

开发高性能代码的过程包括以下应按所列顺序执行的阶段：

1. **识别最慢的代码**：用计时工具找到真正的性能瓶颈，而不是凭感觉优化
2. **内存与对象优化**：减少堆分配、避免动态对象创建，降低 GC 触发频率
3. **代码执行效率优化**：使用 `const()`、预编译字节码、native/viper 代码发射器
4. **运算与硬件优化**：整数替代浮点、直接操作寄存器、使用 DMA

# 二、优化方法

## 2.1 识别最慢的代码

在识别最慢的代码部分，我们通常可以通过明智地使用定时来建立 ticks 的中记录的功能组 `utime`。代码执行时间可以 ms（毫秒）、us（微秒）或 CPU 周期来衡量。

以下代码允许通过添加 `@timed_function` 装饰器对任何函数或方法进行计时：

```python
import time

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func
```

这里，我们使用 mpremote 工具连接树莓派 Pico，将上面的代码复制到 REPL 中，按回车执行（此时装饰器已定义完成）：

```
Windows PowerShell
版权所有 (C) Microsoft Corporation。保留所有权利。

尝试新的跨平台 PowerShell https://aka.ms/pscore6

(base) PS D:\lee\windows terminal\terminal-1.17.11461.0> mpremote
Connected to MicroPython at COM65
Use Ctrl-] or Ctrl-x to exit this shell

>>> import time
>>>
>>> def timed_function(f, *args, **kwargs):
...         myname = str(f).split(' ')[1]
...         def new_func(*args, **kwargs):
...                 t = time.ticks_us()
...                 result = f(*args, **kwargs)
...                 delta = time.ticks_diff(time.ticks_us(), t)
...                 print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
...                 return result
...         return new_func
...
>>>
```

接着，定义一个测试函数（模拟耗时操作）：

```python
# 用@timed_function装饰器修饰测试函数
@timed_function
def slow_function():
    for i in range(10000):
        pass
    return "Done"
```

我们将其粘贴到 REPL 中：

```
>>> @timed_function
... def slow_function():
...         for i in range(10000):
...                 pass
...         return "Done"
...
>>>
```

接着调用函数，查看计时结果：

```python
slow_function()
```

输出了函数执行的耗时结果：

```
>>> slow_function()
Function slow_function Time =  35.915ms
'Done'
>>>
```

## 2.2 性能优化的具体措施

### 2.2.1 MicroPython 的性能瓶颈与核心基础概念

#### 2.2.1.1 核心基础概念

##### 2.2.1.1.1 变量与常量

首先我们需要明白变量与常量之间的区别，这是编程的基础，二者之间核心区别在于何时确定值：

| 特性 | 变量（Variable） | 常量（Constant） |
|------|-----------------|-----------------|
| 值确定时机 | 运行时动态赋值 | 编译时/定义时固定 |
| 访问方式 | 运行时字典查找（有开销） | 编译时直接替换为数值（无开销） |
| 内存分配 | 可能触发堆分配 | 不触发堆分配 |
| MicroPython 用法 | 普通变量赋值 | `from micropython import const; X = const(值)` |
| 适用场景 | 需要在运行中改变的值 | 寄存器地址、最大计数、引脚掩码等固定值 |

##### 2.2.1.1.2 内存三分区

嵌入式微控制器（如 RP2040）的内存资源极少（比如只有 264KB RAM），而 MicroPython 的对象存储直接依赖内存分区，**堆的分配和回收是最大的性能瓶颈**。我们用 "仓库管理" 的比喻来理解三个分区：

| 分区 | 比喻 | 存储内容 | 分配方式 | 性能影响 |
|------|------|---------|---------|---------|
| **栈（Stack）** | 工作台（有限空间，用完即走） | 局部变量、函数调用帧、返回地址 | 自动分配/释放（LIFO） | 极快，无 GC 开销 |
| **堆（Heap）** | 仓库（大空间，需登记领取） | 所有 Python 对象（列表、字典、字节数组等） | 动态分配，GC 回收 | 分配慢，GC 触发耗时 |
| **静态区（BSS/Data）** | 固定货架（启动时放好，不移动） | 全局变量、模块级常量、固件代码 | 程序启动时分配，不释放 | 访问快，无运行时开销 |

对于嵌入式开发中的内存管理来说，往往面临下面几个难点：

- **堆内存碎片化**：频繁分配/释放小对象后，空闲内存变得不连续，无法分配大块内存
- **GC 随机触发**：垃圾回收在任意时刻触发，导致性能关键代码段出现不可预测的延迟（数毫秒级）
- **内存不足崩溃**：堆空间耗尽时，`MemoryError` 会在运行时抛出，导致程序崩溃
- **栈溢出**：递归过深或局部变量过多时，栈空间耗尽，导致硬件异常

##### 2.2.1.1.3 引用与拷贝

所谓引用，相当于对象的 **"门牌号"**（比喻：电脑里的快捷方式），变量存储的不是数据本身，而是数据在内存中的地址。操作引用不会复制数据，开销极小。

```python
# 在堆上创建字节数组对象，a存储的是对象的地址（门牌号）
a = bytearray(10)  
# b是a的引用，指向同一个对象，无新分配
b = a  
# 操作b会改变a的内容，因为是同一个对象
b[0] = 1  
# 输出：1
print(a[0])
```

在终端中，运行结果如下：

```
>>> a = bytearray(10)
>>> b = a
>>> b[0] = 1
>>> print(a[0])
1
>>>
```

那么对于拷贝（这里指的是深拷贝，关于浅拷贝和深拷贝区别，这里不做过多解释）来说，它会复制整个数据，在堆上创建新对象，存储新的数据集，开销极大（尤其是大数据）：

```python
# 大字节数组（堆上10KB）
a = bytearray(10000)  
# 切片操作，创建新的字节数组（堆上~2KB），属于深拷贝
b = a[30:2000]
```

执行后，`b` 是一个全新的 `bytearray` 对象，包含 `a[30:2000]` 的完整数据副本，打印 `b` 可看到 1970 个 `\x00` 字节：

```
>>> a = bytearray(10000)
>>> b = a[30:2000]
>>> b
bytearray(b'\x00\x00\x00\x00...\x00\x00\x00\x00')
```

为了避免拷贝大字节数组时产生过大的堆分配问题，我们可以使用 memoryview 内存视图，它是 MicroPython 提供的浅引用工具，本质是对缓冲区对象（字节数组、数组、bytes 等）的 "只读 / 可写门牌号"，切片时不会复制数据，仅传递地址，完全避免堆分配。

```python
# 大字节数组
a = bytearray(10000)  
# 创建内存视图（仅分配小对象，几十字节）
mv = memoryview(a)    
# 切片内存视图，无新分配，仅传递地址
b = mv[30:2000]       
# 操作b会改变a的内容，因为是同一个数据
b[0] = 1           
print(a[30])
```

运行结果如下：

```
>>> a = bytearray(10000)
>>> mv = memoryview(a)
>>> b = mv[30:2000]
>>> b[0] = 1
>>> print(a[0])
0
>>> print(a[30])
1
>>>
```

> **注意**：memoryview 仅支持缓冲区协议对象（字节数组、array、bytes），不支持列表（列表存储的是对象引用，不是连续数据）。

在掌握以上基础后，再理解这些嵌入式 MicroPython 的进阶概念：

| 进阶概念 | 说明 | 性能影响 |
|---------|------|---------|
| **GC（垃圾收集）** | 自动回收堆上不再被引用的对象，释放内存 | 每次 GC 耗时 1～数十 ms，触发时机不可预测 |
| **字节码解释执行** | MicroPython 将 `.py` 编译为字节码后逐条解释执行 | 比 C 原生代码慢 10～100 倍 |
| **native/viper 发射器** | 将函数直接编译为 ARM 机器码，跳过字节码解释 | native 约快 2 倍，viper 整数运算快数十倍 |
| **DMA（直接内存访问）** | 脱离 CPU 干预，自主完成内存与外设之间的数据传输 | CPU 从数据搬运中解放，专注计算 |

#### 2.2.1.2 MicroPython 的性能瓶颈

MicroPython 的性能瓶颈主要来自三个核心方面：**堆内存分配与垃圾收集（GC）的开销**、**Python 字节码的解释执行开销**、**低效的运算 / 硬件操作方式**。

因此，我们可以从下面几个方面进行优化：

| 优化层次 | 主要手段 | 预期收益 |
|---------|---------|---------|
| **内存与对象优化** | 预分配、固定大小、memoryview、缓存引用、手动 GC | 消除 GC 随机停顿，稳定性显著提升 |
| **代码执行效率优化** | `const()`、mpy-cross 预编译、native/viper 装饰器 | 整数运算提速数十倍，加载速度更快 |
| **运算与硬件优化** | 整数替代浮点、直接操作寄存器（mem32）、DMA | 硬件操作延迟降至极限，CPU 资源最大化利用 |

### 2.2.2 内存与对象优化

这类优化的核心是"尽量避免在运行时动态创建对象、减少堆分配，从而降低 GC 的触发频率和耗时"，是嵌入式 MicroPython 性能优化的首要步骤。

#### 2.2.2.1 预分配内存与固定对象大小

对象只创建一次（如在类的构造函数中实例化），不允许其大小动态增长（如列表 `append`、字典新增键值对）。尤其是缓冲区（如串口通信的缓冲区），要预分配并复用。

我们可以使用 `readinto()` 代替 `read()`（`read()` 会每次分配新缓冲区，`readinto()` 将数据读入已有的缓冲区）。

以串口缓冲区为例：

```python
from machine import UART, Pin

# 1. 预分配缓冲区（只创建一次，避免动态分配）
buf = bytearray(64)  # 预分配64字节的缓冲区

# 初始化UART
uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# 2. 使用readinto()读入预分配的缓冲区（无新分配）
while True:
    if uart.any():
        # 数据读入buf，返回读取的字节数
        n = uart.readinto(buf)  
        # 对比：uart.read(64) 会每次创建新的字节对象，触发堆分配
        print("recv data:", buf[:n])
```

#### 2.2.2.2 使用数组替代列表 + memoryview 避免数据拷贝

列表存储的是对象引用，内存不连续，且动态增长会触发堆分配；`array` 模块（或 `bytearray`）存储连续的基本类型数据，预分配后性能更高；同时切片操作（如 `ba[30:2000]`）会创建数据副本，触发堆分配；使用 `memoryview` 可直接传递内存指针，无拷贝开销。

```python
import array
import time

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

# 1. 用array替代列表（存储整数，连续内存）
# 预分配1000个int型元素的数组
arr = array.array('i', [0]*1000)  
# 2. 用memoryview避免切片拷贝
# 大字节数组
ba = bytearray(10000)  

# 直接切片：会创建副本，触发~2K的堆分配
@timed_function
def func(data):
    pass
    
# 测试切片拷贝（耗时且占内存）
func(ba[30:2000])

# 使用memoryview：只分配小对象，无数据拷贝
mv = memoryview(ba)
# 传递的是内存指针，无分配
func(mv[30:2000])
```

终端输出如下：

```
>>> func(ba[30:2000])
Function func Time =  0.095ms
>>> mv = memoryview(ba)
>>> func(mv[30:2000])
Function func Time =  0.079ms
>>>
```

可以看到，使用 `memoryview` 切片比直接切片略快，更重要的是**避免了堆分配**（大数据场景下优势更显著）。

#### 2.2.2.3 缓存对象引用

将频繁访问的对象（如 `self.ba`、`obj_display.framebuffer`）缓存到局部变量中，避免每次访问都进行属性查找（属性查找会涉及字典操作，耗时且可能触发分配）。

```python
import time

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

class Foo:
    def __init__(self):
        self.ba = bytearray(100)  
    @timed_function
    def bar(self):
        ba_ref = self.ba          # 缓存引用到局部变量
        for i in range(100):
            ba_ref[i] = i % 256
            
class Foo_compare:
    def __init__(self):
        self.ba = bytearray(100)  
    @timed_function
    def bar(self):
        for i in range(100):
            self.ba[i] = i % 256  # 每次循环都进行属性查找
            
# 测试
f = Foo()
f.bar()

f_c = Foo_compare()
f_c.bar()
```

点击运行，终端输出如下：

```
>>> f = Foo()
>>> f.bar()
Function bar Time =  1.039ms
>>> f_c = Foo()
>>> f_c.bar()
Function bar Time =  0.999ms
```

> 缓存引用在大循环量（如 10000+ 次）和嵌套属性（如 `self.obj.buf`）场景下优化效果更为显著。

#### 2.2.2.4 手动控制垃圾收集

定期调用 `gc.collect()` 手动触发 GC，避免 GC 在性能关键的代码段中随机触发（手动 GC 可控制时机，且频繁小 GC 的耗时远小于单次大 GC）。

```python
import gc
import time

# 启用GC（默认启用，可手动关闭/开启）
gc.enable()
# 性能关键循环前，手动触发GC
# 提前清理内存，耗时约1ms
gc.collect()  

# 性能关键代码段
start = time.ticks_us()
for i in range(10000):
    pass
end = time.ticks_us()

print(f"耗时：{time.ticks_diff(end, start)/1000}ms")
# 定期在非关键段触发GC
# gc.collect()
```

### 2.2.3 代码执行效率优化

这类优化是在内存优化的基础上，进一步提升代码的执行速度，从字节码层面到机器码层面优化。

#### 2.2.3.1 使用 const() 声明常量

`const()` 将标识符替换为数值（编译时完成），避免运行时的字典查找，尤其是在循环中使用的常量，优化效果显著。

```python
from micropython import const
import time

# 声明常量（编译时替换为数值）
MAX_COUNT = const(100000)
# 二进制常量也支持
PIN_BIT = const(1 << 2)

MAX_COUNT_NOT_USE_CONST = 100000

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

@timed_function
def use_const():
    total = 0
    for i in range(MAX_COUNT):
        total += i
    return total

# 对比：不用const()，每次访问都会查字典，耗时更长
@timed_function
def no_const():
    global MAX_COUNT_NOT_USE_CONST
    total = 0
    for i in range(MAX_COUNT_NOT_USE_CONST):
        total += i
    return total

result1 = use_const()
result2 = no_const()
```

终端中运行结果如下：

```
>>> result1 = use_const()
Function use_const Time = 1120.690ms
>>> result2 = no_const()
Function no_const Time = 1120.892ms
```

> **说明**：二者运行时间相差无几，这是因为在 REPL 中，代码是解释执行的，而 `const` 的真正优势在**预编译的字节码**中才明显。将代码保存为 `.py` 文件并以 `import` 方式执行时，`const()` 的优化效果会更显著。

#### 2.2.3.2 mpy-cross 编译字节码

在电脑上用 `mpy-cross` 将 `.py` 脚本预编译为 `.mpy` 字节码，再上传到设备。

**安装 mpy-cross**：

```
(base) PS D:\lee\windows terminal\terminal-1.17.11461.0> pip install mpy-cross
Looking in indexes: https://pypi.tuna.tsinghua.edu.cn/simple
Collecting mpy-cross
  Downloading https://pypi.tuna.tsinghua.edu.cn/packages/.../mpy_cross-1.27.0.post2-py2.py3-none-win_amd64.whl (1.2 MB)
  | 1.2 MB  1.1 MB/s
Installing collected packages: mpy-cross
Successfully installed mpy-cross-1.27.0.post2
```

**编译 `.py` 为 `.mpy`**：

```
(base) PS G:\test_microMLP> mpy-cross main.py
(base) PS G:\test_microMLP> mpy-cross microMLP.py
```

编译完成后，可以看到目录中同时存在 `.py` 和 `.mpy` 文件，`.mpy` 文件更小：

| 文件名 | 类型 | 大小 |
|--------|------|------|
| main.mpy | MPY 文件 | 1 KB |
| main.py | Python 源文件 | 2 KB |
| microMLP.mpy | MPY 文件 | 10 KB |
| microMLP.py | Python 源文件 | 32 KB |

**上传到设备**，使用 `mpremote` 工具：

```
(base) PS G:\test_microMLP> mpremote fs cp main.mpy :main.mpy
cp main.mpy :main.mpy
Up to date: main.mpy
(base) PS G:\test_microMLP> mpremote fs ls
ls :
    5876 AbstractBlockDevInterface.py
     572 LICENSE
    8192 README.md
   25420 ads1115.py
   11720 bh_1750.py
   14474 dbt22.py
     800 main.mpy
    1401 main.py
    9154 sd_block_dev.py
   17702 sdcard.py
```

`.mpy` 文件比 `.py` 文件体积更小（microMLP.py 32KB → microMLP.mpy 10KB），启动时跳过编译阶段，加载更快。

#### 2.2.3.3 使用代码发射器

当 MicroPython 编译代码时，它会单独处理每个函数（类是函数，lambda 和列表推导式也是函数）。函数从解析阶段出来，然后进入编译器，编译器将 Python 函数传递 3 次：

目前，代码发射器有四种：

| 发射器 | 说明 | 速度 | 兼容性 |
|--------|------|------|--------|
| **字节码发射器（默认）** | 生成字节码，解释执行 | 基准速度 | 完全兼容 Python |
| **native 发射器** | 生成 ARM-Thumb 机器码，直接执行 | 约 2 倍提速 | 有限制（见下文） |
| **viper 发射器** | 生成优化机器码，专注整数/指针运算 | 整数运算提速数十倍 | 不完全兼容，需类型标注 |
| **内联汇编发射器** | 直接嵌入汇编指令，极致性能 | 最快 | 需要汇编知识，移植性差 |

##### 2.2.3.3.1 native 代码发射器

native 代码发射器获取每个字节代码并将其转换为等效的 ARM-Thumb 机器代码。此类函数使用普通的 C 堆栈来存储局部变量并直接调用 C 运行时函数。

native 代码发射器通过函数装饰器调用：

```python
@micropython.native
def foo(self, arg):
    buf = self.linebuf  # Cached object
    # code
```

native 代码发射器的当前实现存在某些限制：

- 不支持生成器（generator）
- 不支持关键字参数传递
- 编译后代码体积增大（比字节码更占 Flash 空间）

**提高性能（大约是字节码的两倍）的代价是编译代码大小的增加。**

##### 2.2.3.3.2 Viper 代码发射器

上面讨论的优化涉及符合标准的 Python 代码。Viper 代码发射器不完全兼容。它支持特殊的 Viper 本地数据类型以追求性能。整数处理是不合规的，因为它使用机器字：32 位硬件上的算术以 2\*\*32 为模执行。

Viper 代码发射器会为每个字节代码发出 ARM-Thumb 机器代码，并进一步优化某些内容，例如整数运算。对于两个整数的相加，viper 发射器不调用 C 运行时函数 `rt_binary_op`，而是发出机器指令 `adds` 来直接将两个数字相加。这比调用 `rt_binary_op` 快得多。它是使用装饰器调用的：

```python
@micropython.viper
def foo(self, arg: int) -> int:
    # code
```

Viper 支持它自己的一组类型：`int`（有符号整数）、`uint`（无符号整数）、`ptr`（通用指针）、`ptr8`（字节指针）、`ptr16`（16 位指针）、`ptr32`（32 位指针）。

| 类型 | 说明 | 使用场景 |
|------|------|---------|
| `int` | 有符号机器字整数（32 位） | 普通整数运算，2^32 取模 |
| `uint` | 无符号机器字整数（32 位） | 位操作、地址计算 |
| `ptr8` | 指向字节（uint8）的指针 | 访问 bytearray、bytes 等 |
| `ptr16` | 指向 16 位整数的指针 | 访问 array('H') 等 |
| `ptr32` | 指向 32 位整数的指针 | 直接访问寄存器地址 |

**测试大计算量整数累加**：

```python
import time
import micropython

def timed_function(name):
    def decorator(f):
        def new_func(*args, **kwargs):
            t = time.ticks_us()
            result = f(*args, **kwargs)
            delta = time.ticks_diff(time.ticks_us(), t)
            print('Function {} Time = {:6.3f}ms'.format(name, delta/1000))
            return result
        return new_func
    return decorator
    
# 普通Python函数：100万次累加
@timed_function('normal_add_loop')
def normal_add_loop(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * 2 + 5
    return total

# Viper优化函数：相同计算量
@timed_function('viper_add_loop')
@micropython.viper
def viper_add_loop(n: int) -> int:
    total = 0
    for i in range(n):
        total += i * 2 + 5
    return total

# 调用测试（100万次运算）
normal_add_loop(1000000)
viper_add_loop(1000000)
```

两个函数执行完全相同的 100 万次整数运算（`i*2+5` 累加），但 `normal_add_loop` 是纯解释执行，`viper_add_loop` 是机器码直接执行，终端运行结果如下：

```
>>> normal_add_loop(1000000)
Function normal_add_loop Time = 17221.732ms
1000004000000
>>> viper_add_loop(1000000)
Function viper_add_loop Time = 296.095ms
-723379968
```

> **结果分析**：
> - `normal_add_loop` 耗时 **17221.732ms**（约 17.2 秒）
> - `viper_add_loop` 耗时 **296.095ms**（约 0.3 秒）
> - Viper 版本**快了约 58 倍**！
> - 注意：`viper_add_loop` 的返回值为 `-723379968`，这是因为 Viper 使用 32 位机器字整数，100 万次累加超出了 32 位整数范围（2^31 ≈ 21 亿），发生了溢出截断。

**Viper 有两个关键限制**：

1. **不支持默认参数**：Viper 函数的参数必须显式传递，不支持默认值。

```python
import micropython

# 正确示例（无默认参数，100万次运算，计时）
@micropython.viper
def viper_no_default(a: int) -> int:
    total = 0
    for i in range(a):
        total += i
    return total

# 调用测试
viper_no_default(1000000)
```

如果定义带默认参数的 Viper 函数并调用时不传参，会报错：

```
>>> viper_default()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: function takes 1 positional arguments but 0 were given
>>> viper_default(10)
45
```

（Viper 编译器将默认参数信息丢弃，导致函数签名变为"需要 1 个参数"）

2. **浮点运算无优化**：Viper 对浮点运算没有提速效果。

```python
import micropython

# 普通函数：10万次浮点乘法累加
@timed_function('normal_float_calc')
def normal_float_calc(n: int) -> float:
    total = 0.0
    for i in range(n):
        total += float(i) * 3.14159
    return total

# Viper函数：相同的10万次浮点运算（无优化）
@timed_function('viper_float_calc')
@micropython.viper
def viper_float_calc(n: int):
    total = 0.0
    for i in range(n):
        total += float(i) * 3.14159
    return total

# 调用测试（计时结果几乎一致）
normal_float_calc(100000)
viper_float_calc(100000)
```

运行结果如下：

```
>>> normal_float_calc(100000)
Function normal_float_calc Time = 2887.723ms
1.570779e+10
>>> viper_float_calc(100000)
Function viper_float_calc Time = 2458.806ms
1.570779e+10
>>> normal_float_calc(100000)
Function normal_float_calc Time = 2887.671ms
1.570779e+10
>>> viper_float_calc(100000)
Function viper_float_calc Time = 2458.804ms
1.570779e+10
```

> Viper 的浮点耗时（2458ms）与普通函数（2887ms）差距极小，约提速 15%，远不如整数运算的 58 倍提速，说明 **Viper 不适合浮点密集型计算**。

**Viper 指针类型（ptr8/ptr16/ptr32）用于直接访问连续内存**：

Viper 的指针类型用于直接访问连续内存（如 `bytearray`），无边界检查，支持下标单个访问（不支持切片）。关键优化技巧是：**将对象转为指针的操作放在函数开头**（而非循环内），因为转换操作耗时几微秒，大循环中会被放大。

指针的优势在大数组遍历场景下尤为明显，远快于普通 Python 的数组访问。

```python
import micropython

# 准备1万长度的bytearray（大数组）
ba = bytearray(10000)
for i in range(10000):
    ba[i] = i % 256

# 普通函数：遍历bytearray，累加值
@timed_function('normal_bytearray_access')
def normal_bytearray_access(ba: bytearray) -> int:
    total = 0
    for i in range(10000):
        total += ba[i]
    return total

# Viper函数：ptr8指针访问，累加值（转换放在开头）
@timed_function('viper_ptr8_access')
@micropython.viper
def viper_ptr8_access(ba) -> int:
    buf = ptr8(ba)
    total = 0
    for i in range(10000):
        total += buf[i]
    return total

# 调用测试（指针访问速度远超普通访问）
normal_bytearray_access(ba)
viper_ptr8_access(ba)
```

终端输出结果如下：

```
>>> normal_bytearray_access(ba)
Function normal_bytearray_access Time = 71.562ms
1273080
>>> viper_ptr8_access(ba)
Function viper_ptr8_access Time =  3.142ms
1273080
```

> **结果分析**：
> - `normal_bytearray_access` 耗时 **71.562ms**
> - `viper_ptr8_access` 耗时 **3.142ms**
> - Viper ptr8 版本**快了约 23 倍**！
> - 普通函数的 `ba[i]` 需经过 Python 的边界检查、对象属性查找等步骤；Viper 的 `buf[i]` 是直接计算内存地址并访问字节，无任何额外开销。

**对比指针转换位置的影响（循环内 vs 函数开头）**：

```python
import micropython

# 准备1万长度的bytearray（大数组）
ba = bytearray(10000)
for i in range(10000):
    ba[i] = i % 256

# Viper函数：循环内重复转换ptr8（低效）
@timed_function('viper_bad_convert')
@micropython.viper
def viper_bad_convert(ba) -> int:
    total = 0
    for i in range(10000):
        buf = ptr8(ba)    # 每次循环都转换，耗时累积
        total += buf[i]
    return total

# Viper函数：开头一次性转换ptr8（高效）
@timed_function('viper_good_convert')
@micropython.viper
def viper_good_convert(ba) -> int:
    buf = ptr8(ba)        # 只转换一次
    total = 0
    for i in range(10000):
        total += buf[i]
    return total
    
# 调用测试
viper_bad_convert(ba)
viper_good_convert(ba)
```

运行结果如下：

```
>>> viper_bad_convert(ba)
Function viper_bad_convert Time = 16.371ms
1273080
>>> viper_good_convert(ba)
Function viper_good_convert Time =  3.130ms
1273080
```

> **结果分析**：
> - `viper_bad_convert`（循环内转换）耗时 **16.371ms**
> - `viper_good_convert`（开头一次转换）耗时 **3.130ms**
> - 差距约 **5 倍**！在 10000 次循环中，每次都执行 `ptr8(ba)` 的类型转换（每次耗时几微秒，累计耗时显著）；仅在开头执行一次转换，避免了重复开销。

Viper 的整数是机器字级别，32 位硬件上算术运算以 2^32 为模执行（溢出后会截断），这是为性能牺牲兼容性的体现，大计算量下这种特性会更明显。

### 2.2.4 运算与硬件优化

#### 2.2.4.1 用整数运算替代浮点数运算

无 FPU（浮点协处理器）的芯片执行浮点运算极慢，性能关键部分用整数运算，非关键部分再转换为浮点数。

```python
from machine import ADC, Pin
import array

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

# 1. 纯整数运算：预分配数组+ADC读数（无浮点）
# 预分配100个int型元素的数组（连续内存，无动态分配）
# 纯整数运算：读取16位整数ADC值
@timed_function
def adc_read_integer():
    adc_data = array.array('i', [0]*100)
    adc = ADC(Pin(26))
    
    for i in range(100):
        adc_data[i] = adc.read_u16()
    return adc_data

# 2. 包含浮点运算：整数读数+浮点转换（电压计算）
# 第一步：整数读数（和上面一致）
# 第二步：浮点运算转换为电压（读数/65535*3.3）
@timed_function
def adc_read_float():
    adc_data = array.array('i', [0]*100)
    adc = ADC(Pin(26))
  
    for i in range(100):
        adc_data[i] = adc.read_u16()
    
    voltage_data = [x/65535*3.3 for x in adc_data]
    return voltage_data
    
# 执行测试，对比耗时
print("=== ADC读数性能对比 ===")
integer_data = adc_read_integer()
float_data = adc_read_float()

# 打印前5个电压值（验证功能）
print("\n前5个电压值：", float_data[:5])
```

终端运行结果：

```
=== ADC ===
>>> integer_data = adc_read_integer()
Function adc_read_integer Time =  2.428ms
>>> float_data = adc_read_float()
Function adc_read_float Time =  3.816ms
>>> print("\n5", float_data[:5])
5 [0.7333165, 0.7373449, 0.7397619, 0.7429847, 0.7462073]
```

> **结果分析**：
> - `adc_read_integer`（纯整数）耗时 **2.428ms**
> - `adc_read_float`（含浮点转换）耗时 **3.816ms**
> - 浮点版本比整数版本慢约 **57%**，差异在 ADC 采集数量增大时会进一步放大。
> - **优化建议**：在循环中只做整数 ADC 读数，循环结束后再做一次性浮点转换（如需要），或只在显示输出时转换。

#### 2.2.4.2 直接读写寄存器

绕过 MicroPython 的硬件抽象层，直接读写芯片寄存器，消除方法调用的开销（如 LED 快速闪烁、高频 GPIO 操作）。

```python
from machine import Pin, mem32
import time
from micropython import const

def timed_function(f, *args, **kwargs):
    myname = str(f).split(' ')[1]
    def new_func(*args, **kwargs):
        t = time.ticks_us()
        result = f(*args, **kwargs)
        delta = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta/1000))
        return result
    return new_func

# --------------------------
# 配置SIO寄存器（树莓派Pico专属）
# --------------------------
# SIO模块基地址（RP2040固定）
SIO_BASE = const(0xD0000000)
# 一次性写入所有GPIO输出值
GPIO_OUT     = SIO_BASE + 0x010   
# 原子置位GPIO
GPIO_OUT_SET = SIO_BASE + 0x014
# 原子清零GPIO
GPIO_OUT_CLR = SIO_BASE + 0x018
# 原子翻转GPIO
GPIO_OUT_XOR = SIO_BASE + 0x01C
# 原子设置GPIO为输出模式
GPIO_OE_SET  = SIO_BASE + 0x024
# GPIO25（板载LED）的位掩码（bit25对应GPIO25）
PIN25_MASK = const(1 << 25)

# 初始化：将GPIO25设为输出模式（仅执行一次，原子操作） 
mem32[GPIO_OE_SET] = PIN25_MASK

# 初始化Pin对象（仅执行一次）
led_pin = Pin(25, Pin.OUT)

# 方式1：普通machine.Pin操作GPIO25（硬件抽象层，有开销）
@timed_function
def led_pin_loop(loop_count):
    for _ in range(loop_count):
        led_pin.value(1)
        led_pin.value(0)

# 方式2：SIO寄存器操作GPIO25（无抽象层，极致高效）
@timed_function
def led_sio_set_clr_loop(loop_count):
    set_reg = GPIO_OUT_SET   # 缓存寄存器地址到局部变量
    clr_reg = GPIO_OUT_CLR
    mask = PIN25_MASK
    for _ in range(loop_count):
        mem32[set_reg] = mask
        mem32[clr_reg] = mask

# 测试运行速度（1000次翻转）
loop_count = 1000

led_pin_loop(loop_count)
led_sio_set_clr_loop(loop_count)
```

运行结果如下：

REPL 定义代码（可见 SIO 寄存器地址配置）：

```
>>> from machine import Pin, mem32
>>> import time
>>> from micropython import const
>>>
>>> SIO_BASE = const(0xD0000000)
>>> GPIO_OUT = SIO_BASE + 0x010
>>> GPIO_OUT_SET = SIO_BASE + 0x014
>>> GPIO_OUT_CLR = SIO_BASE + 0x018
>>> GPIO_OUT_XOR = SIO_BASE + 0x01C
>>> GPIO_OE_SET = SIO_BASE + 0x024
>>> PIN25_MASK = const(1 << 25)
>>> mem32[GPIO_OE_SET] = PIN25_MASK
>>> led_pin = Pin(25, Pin.OUT)
>>> @timed_function
... def led_pin_loop(loop_count):
...         for _ in range(loop_count):
...                 led_pin.value(1)
...                 led_pin.value(0)
```

计时测试结果：

```
>>> loop_count = 1000
>>> led_pin_loop(loop_count)
Function led_pin_loop Time = 16.274ms
>>> led_sio_set_clr_loop(loop_count)
Function led_sio_set_clr_loop Time = 10.968ms
```

> **结果分析**：
> - `led_pin_loop`（machine.Pin 方式）耗时 **16.274ms**
> - `led_sio_set_clr_loop`（SIO 寄存器方式）耗时 **10.968ms**
> - 寄存器方式**快约 48%**（1.5 倍）
> - 在 SIO 循环函数中，将 `GPIO_OUT_SET`、`GPIO_OUT_CLR`、`PIN25_MASK` 缓存到局部变量，减少全局变量查找的开销，让 SIO 的性能优势更突出。
> - **进一步优化**：结合 `@micropython.viper` 装饰器 + `ptr32` 指针直接写寄存器，可将 GPIO 翻转速度提升到数 MHz 级别。

#### 2.2.4.3 DMA 相关操作

在运算与硬件数据交互的场景中（如批量 ADC 数据采集、高频 GPIO 信号输出、传感器数据流读取），CPU 往往需要花费大量时间执行**数据传输操作**（如从外设寄存器读取数据到内存、将运算结果写入 GPIO 寄存器），挤占了运算所需的资源。RP2040 的 DMA（Direct Memory Access，直接内存访问）控制器可脱离 CPU 干预，自主完成内存与外设 / 寄存器之间的批量数据传输，其核心优化价值在于：**将 CPU 从繁琐的数据传输任务中解放出来，使其专注于核心运算逻辑**。

从开发与性能层面来看，MicroPython 对 RP2040 DMA 的支持较为基础，仅能实现简单的批量数据传输；而 C 语言（Pico SDK）可充分配置 DMA 的传输模式、触发条件与数据处理规则，结合直接寄存器操作，能实现运算与硬件数据交互的无缝优化，是高吞吐量、低延迟场景的最优选择。

# 三、优化实验

## 3.1 LCD 屏幕的优化

关于这个可以查看：

[08 SPI 串行外设接口-文档教程初稿](https://f1829ryac0m.feishu.cn/wiki/Qzagwgz3diFggSkR6rnc8oyunCe)

## 3.2 DMA 相关优化

关于这个可以查看：

[19 DMA 直接内存访问-文档教程初稿](https://f1829ryac0m.feishu.cn/docx/OkDhdXUngoCUfKxDMcqc4BZJneh)

# 四、优化效果汇总

| 优化手段 | 测试场景 | 优化前耗时 | 优化后耗时 | 提速倍数 |
|---------|---------|-----------|-----------|---------|
| `@micropython.viper`（整数运算） | 100 万次 `i*2+5` 累加 | 17221.732ms | 296.095ms | **~58 倍** |
| `viper ptr8` 指针访问 | 1 万次 bytearray 遍历 | 71.562ms | 3.142ms | **~23 倍** |
| `ptr8` 转换移到循环外 | 1 万次指针访问 | 16.371ms（坏）| 3.130ms（好）| **~5 倍** |
| `memoryview` 替代切片 | 传递 bytearray 切片 | 0.095ms | 0.079ms | ~20% |
| 缓存对象引用 | 100 次属性访问写入 | 0.999ms | 1.039ms（示例）| 约持平（大循环效果更显著） |
| `const()` 常量 | 10 万次循环访问常量 | 1120.892ms | 1120.690ms | REPL 下约持平（预编译下更显著）|
| 整数替代浮点（ADC） | 100 次 ADC 采集 | 3.816ms（含浮点转换）| 2.428ms（纯整数）| **~57%** |
| SIO 寄存器替代 `machine.Pin` | 1000 次 GPIO 翻转 | 16.274ms | 10.968ms | **~48%** |

# 参考资料

- [MicroPython 官方性能优化文档](https://docs.micropython.org/en/latest/reference/speed_python.html)
- [MicroPython viper 代码发射器说明](https://docs.micropython.org/en/latest/reference/speed_python.html#the-viper-code-emitter)
- [RP2040 Datasheet - SIO 模块](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
