# EWM550-7G9T10SP UWB模组MicroPython驱动
# -*- coding: utf-8 -*-
# @Time    : 2026/3/2
# @Author  : Derived
# @File    : ewm550.py
# @Description : EWM550-7G9T10SP 超宽带UWB测距定位模组驱动，支持AT指令配置、测距、透传模式
# @License : MIT
# @Platform : MicroPython v1.23.0

__version__ = "0.1.0"
__author__ = "Derived"
__license__ = "MIT"
__platform__ = "MicroPython v1.23"

import time

class EWM550:
    """
    EWM550-7G9T10SP UWB测距定位模组驱动类，基于UART接口实现AT指令配置、测距模式、透传模式
    支持基站/标签/透传三种角色切换，信道/波特率/功率/测距参数配置，以及数据透传、测距数据解析

    Attributes:
        _uart (UART): MicroPython UART实例，与模组通信的串口
        rx_timeout_ms (int): 串口接收超时时间，单位ms
        role (int): 模块当前角色，对应Role常量
        ch (int): 工作信道，5/9
        baud (int): 串口波特率，对应Baud常量
        power (int): 发射功率档位，0-3
        responder_num (int): 从机（标签）数量，1-5
        src_addr (str): 源地址，4位十六进制字符串(0000-FFFF)
        dst_addr (str): 目标地址，20位十六进制字符串
        intv (int): 测距数据打印间隙，30-2000ms
        version (str): 模组固件版本号
        sleep_mode (int): 休眠模式，0=掉电模式，1=周期休眠模式

    Constants:
        Role: 角色常量 (TAG=0, BASE=1, TRANSMODE=2)
        Baud: 波特率常量，对应AT指令的数字映射
        CHANNEL: 信道常量 (CH5=5, CH9=9)
        POWER: 功率档位常量 (P0-P3，P3为最大功率)
        SLEEP: 休眠模式常量 (POWER_DOWN=0, CYCLE_SLEEP=1)
    """
    # 模块角色常量
    Role = {"TAG": 0, "BASE": 1, "TRANSMODE": 2}
    # 波特率常量，键为AT指令参数，值为实际波特率
    Baud = {
        0: 9600, 1: 19200, 2: 38400, 3: 57600, 4: 115200,
        5: 230400, 6: 460800, 7: 921600, 8: 1000000, 9: 2000000
    }
    # 工作信道常量
    CHANNEL = {"CH5": 5, "CH9": 9}
    # 功率档位常量
    POWER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    # 休眠模式常量
    SLEEP = {"POWER_DOWN": 0, "CYCLE_SLEEP": 1}

    def __init__(self, uart, rx_timeout_ms=600):
        """
        初始化EWM550驱动实例，绑定UART接口并初始化参数
        Args:
            uart: 已初始化的MicroPython UART对象，需支持write/any/read方法
                  模组默认波特率921600 8N1，建议初始化UART时匹配
            rx_timeout_ms (int): 串口接收超时时间，默认600ms
        """
        self._uart = uart
        self.rx_timeout_ms = rx_timeout_ms
        # 初始化模块参数
        self.role = None
        self.ch = None
        self.baud = None
        self.power = None
        self.responder_num = None
        self.src_addr = None
        self.dst_addr = None
        self.intv = None
        self.version = None
        self.sleep_mode = None

    def _send_cmd(self, cmd: bytes) -> tuple[bool, str | None]:
        """
        底层串口发送指令，添加微小延时保证模块响应
        Args:
            cmd (bytes): 要发送的AT指令字节流
        Returns:
            (bool, str|None): 成功返回(True, None)，失败返回(False, 错误信息)
        """
        try:
            # 发送指令前清空接收缓冲，避免干扰响应解析
            self._uart.read()
            self._uart.write(cmd)
            # 30ms延时，保证模块接收并响应
            time.sleep_ms(30)
            return True, None
        except Exception as e:
            return False, f"send error: {str(e)}"

    def _recv_resp(self) -> tuple[bool, str | None]:
        """
        底层串口接收响应，自动解码为UTF-8字符串并去除首尾空白
        Returns:
            (bool, str|None): 成功返回(True, 响应字符串)，超时/失败返回(False, 错误信息)
        """
        try:
            # 50ms延时，保证模块接收并响应
            time.sleep_ms(50)
            if self._uart.any():
                resp = self._uart.read()
                if resp is None:
                    return False, "recv none"
                return True, resp.decode("utf-8").strip()
            return False, "no data"
        except Exception as e:
            return False, f"recv error: {str(e)}"

    def enter_at_mode(self) -> tuple[bool, str | None]:
        """
        进入AT配置模式，发送+++，进入后测距打印暂停
        Returns:
            (bool, str|None): 成功返回(True, "AT_MODE")，失败返回(False, 错误信息)
        """
        ok, err = self._send_cmd(b"+++")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "AT_MODE":
            return True, resp
        return False, f"enter AT mode failed: {resp if resp else 'no response'}"

    def exit_at_mode(self) -> tuple[bool, str | None]:
        """e
        退出AT配置模式，发送AT+EXIT，退出后恢复测距打印
        Returns:
            (bool, str|None): 成功返回(True, "exit success")，失败返回(False, 错误信息)
        """
        ok, err = self._send_cmd(b"AT+EXIT")
        if not ok:
            return False, err
        # 退出AT模式无返回值，直接判定成功
        return True, "exit success"

    def check(self) -> tuple[bool, str | None]:
        """
        检测模块通信是否正常（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        """
        ok, err = self._send_cmd(b"AT")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            return True, resp
        return False, f"module unresponsive: {resp if resp else 'no response'}"

    def restore_factory_settings(self) -> tuple[bool, str | None]:
        """
        恢复出厂设置（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        """
        ok, err = self._send_cmd(b"AT+RESTORE")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            return True, resp
        return False, f"restore failed: {resp if resp else 'no response'}"

    def reset_module(self) -> tuple[bool, str | None]:
        """
        模块复位，所有AT配置参数生效（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        """
        ok, err = self._send_cmd(b"AT+RESET")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            time.sleep(0.1)  # 复位后短暂延时
            return True, resp
        return False, f"reset failed: {resp if resp else 'no response'}"

    def get_version(self) -> tuple[bool, str | None]:
        """
        查询模组固件版本号（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 版本号)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性version，版本号示例：7530-0-11
        """
        ok, err = self._send_cmd(b"AT+VERSION")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("VERSION:"):
            self.version = resp.split(":", 1)[1].strip()
            return True, self.version
        return False, f"get version failed: {resp if resp else 'no response'}"

    def set_role(self, role: int) -> tuple[bool, str | None]:
        """
        设置模块角色（需先进入AT模式）
        Args:
            role (int): 角色值，对应Role常量 (TAG=0, BASE=1, TRANSMODE=2)
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性role
        """
        if role not in self.Role.values():
            return False, f"invalid role, must be {self.Role.values()}"
        ok, err = self._send_cmd(f"AT+ROLE={role}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.role = role
            return True, resp
        return False, f"set role failed: {resp if resp else 'no response'}"

    def get_role(self) -> tuple[bool, str | None]:
        """
        查询模块当前角色（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 角色值)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性role
        """
        ok, err = self._send_cmd(b"AT+ROLE=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("ROLE:"):
            self.role = int(resp.split(":", 1)[1].strip())
            return True, str(self.role)
        return False, f"get role failed: {resp if resp else 'no response'}"

    def set_channel(self, ch: int) -> tuple[bool, str | None]:
        """
        设置工作信道（需先进入AT模式）
        Args:
            ch (int): 信道值，对应CHANNEL常量 (CH5=5, CH9=9)
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性ch，模组默认CH9(7737.2~8237.2MHz)
        """
        if ch not in self.CHANNEL.values():
            return False, f"invalid channel, must be {self.CHANNEL.values()}"
        ok, err = self._send_cmd(f"AT+CH={ch}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.ch = ch
            return True, resp
        return False, f"set channel failed: {resp if resp else 'no response'}"

    def get_channel(self) -> tuple[bool, str | None]:
        """
        查询当前工作信道（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 信道值)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性ch
        """
        ok, err = self._send_cmd(b"AT+CH=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("CH:"):
            self.ch = int(resp.split(":", 1)[1].strip())
            return True, str(self.ch)
        return False, f"get channel failed: {resp if resp else 'no response'}"

    def set_baud(self, baud_param: int) -> tuple[bool, str | None]:
        """
        设置串口波特率（需先进入AT模式）
        Args:
            baud_param (int): 波特率参数，对应Baud常量的键(0-9)
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            1. 成功后更新实例属性baud为实际波特率
            2. 波特率修改后，需同步调整外部UART的波特率，否则通信中断
            3. 模组默认波特率参数7，对应921600
        """
        if baud_param not in self.Baud.keys():
            return False, f"invalid baud param, must be {self.Baud.keys()}"
        ok, err = self._send_cmd(f"AT+BAUD={baud_param}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.baud = self.Baud[baud_param]
            return True, resp
        return False, f"set baud failed: {resp if resp else 'no response'}"

    def get_baud(self) -> tuple[bool, str | None]:
        """
        查询当前串口波特率（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 波特率参数)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性baud为实际波特率
        """
        ok, err = self._send_cmd(b"AT+BAUD=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("BAUD:"):
            baud_param = int(resp.split(":", 1)[1].strip())
            self.baud = self.Baud[baud_param]
            return True, str(baud_param)
        return False, f"get baud failed: {resp if resp else 'no response'}"

    def set_power(self, power: int) -> tuple[bool, str | None]:
        """
        设置发射功率档位（需先进入AT模式）
        Args:
            power (int): 功率档位，对应POWER常量(0-3)，3为最大功率
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性power，模组默认最大功率档位3
        """
        if power not in self.POWER.values():
            return False, f"invalid power, must be {self.POWER.values()}"
        ok, err = self._send_cmd(f"AT+POWER={power}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.power = power
            return True, resp
        return False, f"set power failed: {resp if resp else 'no response'}"

    def get_power(self) -> tuple[bool, str | None]:
        """
        查询当前发射功率档位（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 功率档位)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性power
        """
        ok, err = self._send_cmd(b"AT+POWER=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("POWER:"):
            self.power = int(resp.split(":", 1)[1].strip().strip("<>"))
            return True, str(self.power)
        return False, f"get power failed: {resp if resp else 'no response'}"

    def set_responder_num(self, num: int) -> tuple[bool, str | None]:
        """
        设置从机（标签）数量（需先进入AT模式，仅基站模式有效）
        Args:
            num (int): 标签数量，取值1-5，模组默认5
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            1. 成功后更新实例属性responder_num
            2. 透传模式下该指令失效
        """
        if not 1 <= num <= 5:
            return False, "invalid responder num, must be 1-5"
        ok, err = self._send_cmd(f"AT+RESPONDER_NUM={num}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.responder_num = num
            return True, resp
        return False, f"set responder num failed: {resp if resp else 'no response'}"

    def get_responder_num(self) -> tuple[bool, str | None]:
        """
        查询当前从机（标签）数量（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 标签数量)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性responder_num
        """
        ok, err = self._send_cmd(b"AT+RESPONDER_NUM=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("RESPONDER_NUM:"):
            self.responder_num = int(resp.split(":", 1)[1].strip())
            return True, str(self.responder_num)
        return False, f"get responder num failed: {resp if resp else 'no response'}"

    def set_src_addr(self, addr: str) -> tuple[bool, str | None]:
        """
        设置源地址（需先进入AT模式）
        Args:
            addr (str): 4位十六进制字符串，取值0000-FFFF，大小写均可
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            1. 成功后更新实例属性src_addr（统一转为大写）
            2. 源地址为模块自身地址，需与目标地址匹配实现测距/透传
        """
        addr = addr.strip().upper()
        if len(addr) != 4 or not all(c in "0123456789ABCDEF" for c in addr):
            return False, "invalid src addr, must be 4 hex chars (0000-FFFF)"
        ok, err = self._send_cmd(f"AT+SRCADDR={addr}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.src_addr = addr
            return True, resp
        return False, f"set src addr failed: {resp if resp else 'no response'}"

    def get_src_addr(self) -> tuple[bool, str | None]:
        """
        查询当前源地址（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 4位十六进制源地址)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性src_addr
        """
        ok, err = self._send_cmd(b"AT+SRCADDR=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("SRC_ADDR:"):
            self.src_addr = resp.split(":", 1)[1].strip()
            return True, self.src_addr
        return False, f"get src addr failed: {resp if resp else 'no response'}"

    def set_dst_addr(self, addr: str) -> tuple[bool, str | None]:
        """
        设置目标地址（需先进入AT模式）
        Args:
            addr (str): 20位十六进制字符串，取值00000000000000000000-FFFFFFFFFFFFFFFFFFFF
                        大小写均可，测距/透传时仅前N*4位有效（N为标签数量）
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            1. 成功后更新实例属性dst_addr（统一转为大写）
            2. 基站模式：前4*N位为N个标签的源地址，超出部分无效
            3. 标签模式：仅前4位为基站源地址，其余无效
            4. 透传模式：仅前4位有效，为目标模块源地址
        """
        addr = addr.strip().upper()
        if len(addr) != 20 or not all(c in "0123456789ABCDEF" for c in addr):
            return False, "invalid dst addr, must be 20 hex chars"
        ok, err = self._send_cmd(f"AT+DSTADDR={addr}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.dst_addr = addr
            return True, resp
        return False, f"set dst addr failed: {resp if resp else 'no response'}"

    def get_dst_addr(self) -> tuple[bool, str | None]:
        """
        查询当前目标地址（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 20位十六进制目标地址)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性dst_addr
        """
        ok, err = self._send_cmd(b"AT+DSTADDR=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("DST_ADDR:"):
            self.dst_addr = resp.split(":", 1)[1].strip()
            return True, self.dst_addr
        return False, f"get dst addr failed: {resp if resp else 'no response'}"

    def set_print_interval(self, intv: int) -> tuple[bool, str | None]:
        """
        设置测距数据打印间隙（需先进入AT模式）
        Args:
            intv (int): 打印间隙，单位ms，取值30-2000，一对多测距建议≥100ms
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            1. 成功后更新实例属性intv
            2. 模组默认打印间隙500ms
        """
        if not 30 <= intv <= 2000:
            return False, "invalid intv, must be 30-2000ms"
        ok, err = self._send_cmd(f"AT+INTV={intv}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.intv = intv
            return True, resp
        return False, f"set intv failed: {resp if resp else 'no response'}"

    def get_print_interval(self) -> tuple[bool, str | None]:
        """
        查询当前测距数据打印间隙（需先进入AT模式）
        Returns:
            (bool, str|None): 成功返回(True, 打印间隙ms)，失败返回(False, 错误信息)
        Notes:
            成功后更新实例属性intv
        """
        ok, err = self._send_cmd(b"AT+INTV=?")
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp.startswith("INTV:"):
            self.intv = int(resp.split(":", 1)[1].strip())
            return True, str(self.intv)
        return False, f"get intv failed: {resp if resp else 'no response'}"

    def enter_sleep_mode(self, sleep_mode: int) -> tuple[bool, str | None]:
        """
        设置休眠模式（需先进入AT模式）
        Args:
            sleep_mode (int): 休眠模式，对应SLEEP常量(0=掉电模式,1=周期休眠模式)
        Returns:
            (bool, str|None): 成功返回(True, "+OK")，失败返回(False, 错误信息)
        Notes:
            1. 成功后更新实例属性sleep_mode
            2. 掉电模式：UWB停止所有工作，需拉低WKP引脚唤醒
            3. 周期休眠模式：低功耗工作，串口不接收数据
        """
        if sleep_mode not in self.SLEEP.values():
            return False, f"invalid sleep mode, must be {self.SLEEP.values()}"
        ok, err = self._send_cmd(f"AT+SLEEP={sleep_mode}".encode())
        if not ok:
            return False, err
        ok, resp = self._recv_resp()
        if ok and resp == "+OK":
            self.sleep_mode = sleep_mode
            return True, resp
        return False, f"set sleep failed: {resp if resp else 'no response'}"

    def parse_ranging_data(self, data: bytes) -> dict | None:
        """
        解析测距数据，支持基站端和标签端数据格式
        Args:
            data (bytes): 从串口接收的测距数据字节流
        Returns:
            dict|None: 解析成功返回字典，失败返回None
            基站端字典示例: {"type": "base", "tag_idx": 0, "tag_addr": "1111", "distance": 10, "snr": 20, "sleep": False}
            标签端字典示例: {"type": "tag", "base_addr": "0000", "distance": 10}
        """
        try:
            data_str = data.decode("utf-8").strip()
            # 基站端数据格式：P0,AA00,10cm,20dB / LP1,2222,20cm,20dB（L表示休眠）
            if "," in data_str and ("cm" in data_str and "dB" in data_str):
                parts = data_str.split(",")
                if len(parts) != 4:
                    return None
                # 解析休眠标识
                sleep_flag = parts[0].startswith("L")
                tag_idx = int(parts[0].lstrip("LP")) if sleep_flag else int(parts[0].lstrip("P"))
                return {
                    "type": "base",
                    "tag_idx": tag_idx,
                    "tag_addr": parts[1].strip(),
                    "distance": int(parts[2].replace("cm", "").strip()),
                    "snr": int(parts[3].replace("dB", "").strip()),
                    "sleep": sleep_flag
                }
            # 标签端数据格式：P,1111,10cm
            elif data_str.startswith("P,") and "cm" in data_str:
                parts = data_str.split(",")
                if len(parts) != 3:
                    return None
                return {
                    "type": "tag",
                    "base_addr": parts[1].strip(),
                    "distance": int(parts[2].replace("cm", "").strip())
                }
            return None
        except Exception:
            return None