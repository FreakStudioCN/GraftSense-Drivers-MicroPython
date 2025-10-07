# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/8/26 下午10:12
# @Author  : 缪贵成
# @File    : acquire.py
# @Description : 用于嗅探 回放
# @License : CC BY-NC 4.0

__version__ = "0.1.0"
__author__ = "缪贵成"
__license__ = "CC BY-NC 4.0"
__platform__ = "MicroPython v1.23"

# ======================================== 导入相关模块 =========================================

from machine import Pin, freq
from sys import platform
import time
from utime import sleep_ms, ticks_diff
from . import IR_RX

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================

class IR_GET(IR_RX):
    """
    该类继承自 IR_RX，用于获取原始红外脉冲序列，并尝试识别常见协议类型。

    Attributes:
        display (bool): 是否打印接收到的脉冲信息及可能的协议。
        data (list|None): 捕获到的脉冲时间序列，单位微秒。若尚未接收到则为 None。

    Methods:
        __init__(pin, nedges=100, twait=100, display=True) -> None:
            初始化 IR_GET 对象，设置引脚、捕获参数和显示选项。
        decode(_) -> None:
            解码捕获的脉冲数据，尝试识别协议并存储原始脉冲序列。
        acquire() -> list:
            阻塞等待接收到脉冲序列并返回。

    Notes:
        本类主要用于调试或协议分析，不直接解析为命令或地址。
        当 display=True 时，解码过程中会通过串口打印信息。

    ==========================================

    IR_GET extends IR_RX, used to capture raw IR pulse sequences and attempt to identify known protocols.

    Attributes:
        display (bool): Whether to print captured pulses and possible protocol type.
        data (list|None): Captured pulse sequence in microseconds, or None if not yet available.

    Methods:
        __init__(pin, nedges=100, twait=100, display=True) -> None:
            Initialize IR_GET object, configure pin, capture parameters, and display option.
        decode(_) -> None:
            Decode captured pulse sequence, attempt to identify protocol, store raw data.
        acquire() -> list:
            Block until pulse sequence is received and return it.

    Notes:
        This class is mainly for debugging or protocol inspection, not direct command decoding.
        If display=True, decoding process prints info via serial output.
    """

    def __init__(self, pin: Pin, nedges: int = 100, twait: int = 100, display: bool = True) -> None:
        """
        初始化 IR_GET 对象。
        Args:
            pin (Pin): 用于接收红外信号的引脚。
            nedges (int): 最大捕获边沿数，默认 100。
            twait (int): 超时时间，单位毫秒，默认 100。
            display (bool): 是否打印脉冲和协议信息，默认 True。

        Notes:
            调用父类 IR_RX 初始化捕获逻辑。
            display=True 时将打印脉冲和协议识别结果。

        ==========================================

        Initialize IR_GET object.

        Args:
            pin (Pin): Input pin for IR signal.
            nedges (int): Max number of edges to capture. Default 100.
            twait (int): Timeout in milliseconds. Default 100.
            display (bool): Whether to print pulses and protocol info. Default True.

        Notes:
            Calls parent IR_RX to initialize capture logic.
            If display=True, pulses and protocol detection are printed.
        """
        self.display = display
        super().__init__(pin, nedges, twait, lambda *_ : None)
        self.data = None

    def decode(self, _) -> None:
        """
        解码捕获到的红外脉冲序列，并尝试识别协议。

        Args:
            _ : 占位参数，由定时器回调传入，不使用。

        Notes:
            成功捕获后将脉冲序列存储到 self.data。
            若 display=True，则打印脉冲详情和识别结果。
            该方法由定时器回调自动触发。

        ==========================================

        Decode captured IR pulse sequence and attempt to identify protocol.

        Args:
            _ : Placeholder argument from timer callback, unused.

        Notes:
            On success, pulse sequence is stored in self.data.
            If display=True, prints pulse details and protocol detection.
            Method is triggered automatically by timer callback.
        """
        def near(v, target):
            return target * 0.8 < v < target * 1.2
        lb = self.edge - 1
        if lb < 3:
            return  # Noise
        burst = []
        for x in range(lb):
            dt = ticks_diff(self._times[x + 1], self._times[x])
            if x > 0 and dt > 10000:  # Reached gap between repeats
                break
            burst.append(dt)
        lb = len(burst)
        duration = ticks_diff(self._times[lb - 1], self._times[0])

        if self.display:
            for x, e in enumerate(burst):
                print('{:03d} {:5d}'.format(x, e))
            print()
            ok = False
            if near(burst[0], 9000) and lb == 67:
                print('NEC')
                ok = True

            if not ok and near(burst[0], 2400) and near(burst[1], 600):
                try:
                    nbits = {25:12, 31:15, 41:20}[lb]
                except KeyError:
                    pass
                else:
                    ok = True
                    print('Sony {}bit'.format(nbits))

            if not ok and near(burst[0], 889):
                if near(duration, 24892) and near(max(burst), 1778):
                    print('Philps RC-5')
                    ok = True

            if not ok and near(burst[0], 2666) and near(burst[1], 889):
                if near(duration, 22205) and near(burst[1], 889) and near(burst[2], 444):
                    print('Philips RC-6 mode 0')
                    ok = True

            if not ok and near(burst[0], 2000) and near(burst[1], 1000):
                if near(duration, 19000):
                    print('Microsoft MCE edition protocol.')
                    print('Protocol start {} {} Burst length {} duration {}'.format(burst[0], burst[1], lb, duration))
                    ok = True

            if not ok and near(burst[0], 4500) and near(burst[1], 4500) and lb == 67:
                print('Samsung')
                ok = True

            if not ok and near(burst[0], 3500) and near(burst[1], 1680):
                print('Unsupported protocol. Panasonic?')
                ok = True

            if not ok:
                print('Unknown protocol start {} {} Burst length {} duration {}'.format(burst[0], burst[1], lb, duration))

            print()
        self.data = burst
        self.do_callback(0, 0, 0)

    def acquire(self) -> list:
        """
        阻塞等待，直到接收到红外脉冲数据并返回。

        Returns:
            list: 捕获到的红外脉冲时间序列（微秒）。

        Notes:
            该方法会阻塞主线程，直到有数据为止。
            调用后自动关闭引脚中断和定时器。

        ==========================================

        Block until IR pulse data is received, then return it.


        Returns:
            list: Captured IR pulse sequence (in microseconds).

        Notes:
            This method blocks main thread until data is available.
            Automatically closes pin IRQ and timer after capture.
        """
        while self.data is None:
            sleep_ms(5)
        self.close()
        return self.data


# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
def test() -> list:
    """
    测试函数，根据平台选择合适的引脚并启动 IR_GET 捕获。

    Returns:
        list: 捕获到的红外脉冲序列。

    Notes:
        函数会阻塞直到接收到红外信号。
        输出结果会打印在终端上。

    ==========================================

    Test function, configure platform-specific pin and start IR_GET capture.

    Returns:
        list: Captured IR pulse sequence.

    Notes:
        Function blocks until IR signal is received.
        Captured data is printed to console.
    """
    time.sleep(3)
    print("Freak Studio: acquire test")
    if platform == 'pyboard':
        pin = Pin('X3', Pin.IN)
    elif platform == 'esp8266':
        freq(160000000)
        pin = Pin(13, Pin.IN)
    elif platform == 'esp32' or platform == 'esp32_LoBo':
        pin = Pin(23, Pin.IN)
    elif platform == 'rp2':
        pin = Pin(16, Pin.IN)
    irg = IR_GET(pin)
    print('Waiting for IR data...')
    return irg.acquire()