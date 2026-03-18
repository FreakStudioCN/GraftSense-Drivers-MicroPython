# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午8:30
# @Author  : basanovase
# @File    : calling.py
# @Description : SIM7600模块通话功能类 实现拨打电话、挂断、接听、查询通话状态、设置通话音量等功能 参考自：https://github.com/basanovase/sim7600
# @License : MIT
__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Calling:
    """
    SIM7600模块通话功能类
    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command方法用于发送AT指令

    Methods:
        __init__(sim7600): 初始化通话功能类
        make_call(number): 拨打指定电话号码
        hang_up(): 挂断当前通话
        answer_call(): 接听来电
        call_status(): 查询当前通话状态
        set_call_volume(level): 设置通话音量

    Notes:
        所有AT指令通信依赖sim7600核心对象的send_command方法，需确保该方法能正确发送指令并返回响应

    ==========================================
    SIM7600 Module Calling Function Class
    Attributes:
        sim7600 (object): SIM7600 module core object, must contain send_command method for sending AT commands

    Methods:
        __init__(sim7600): Initialize calling function class
        make_call(number): Make a call to the specified phone number
        hang_up(): Hang up the current call
        answer_call(): Answer an incoming call
        call_status(): Query current call status
        set_call_volume(level): Set call volume level

    Notes:
        All AT command communication depends on the send_command method of the sim7600 core object, ensure this method can send commands correctly and return responses
    """

    def __init__(self, sim7600: object) -> None:
        """
        初始化通话功能类
        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command方法

        Raises:
            TypeError: 当sim7600参数为None时触发
            AttributeError: 当sim7600对象无send_command方法时触发

        Notes:
            依赖SIM7600核心对象的send_command方法进行AT指令通信

        ==========================================
        Initialize calling function class
        Args:
            sim7600 (object): SIM7600 module core object, must implement send_command method

        Raises:
            TypeError: Triggered when sim7600 parameter is None
            AttributeError: Triggered when sim7600 object has no send_command method

        Notes:
            Depends on the send_command method of the SIM7600 core object for AT command communication
        """
        # 检查sim7600参数是否为None
        if sim7600 is None:
            raise TypeError("sim7600 parameter cannot be None")
        # 检查sim7600对象是否包含send_command方法
        if not hasattr(sim7600, "send_command") or not callable(getattr(sim7600, "send_command")):
            raise AttributeError("sim7600 object must implement send_command method")
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def make_call(self, number: str) -> bytes:
        """
        拨打指定电话号码
        Args:
            number (str): 要拨打的电话号码（支持固话/手机号）

        Raises:
            TypeError: 当number参数非字符串类型时触发
            ValueError: 当number参数为空字符串时触发

        Notes:
            使用ATD指令进行拨号，号码末尾必须添加分号;表示语音通话

        ==========================================
        Make a call to the specified phone number
        Args:
            number (str): Phone number to call (supports landline/mobile number)

        Raises:
            TypeError: Triggered when number parameter is not string type
            ValueError: Triggered when number parameter is empty string

        Notes:
            Use ATD command for dialing, number must end with semicolon ; to indicate voice call
        """
        # 检查number参数类型和有效性
        if not isinstance(number, str):
            raise TypeError("number parameter must be string type")
        if len(number.strip()) == 0:
            raise ValueError("number parameter cannot be empty string")
        # 发送拨号指令并返回响应
        return self.sim7600.send_command(f"ATD{number};")

    def hang_up(self) -> bytes:
        """
        挂断当前通话
        Args:
            无

        Raises:
            无

        Notes:
            使用ATH指令挂断当前所有通话，适用于主动挂断或拒接来电

        ==========================================
        Hang up the current call
        Args:
            None

        Raises:
            None

        Notes:
            Use ATH command to hang up all current calls, suitable for active hang up or rejecting incoming calls
        """
        # 发送挂断通话指令并返回响应
        return self.sim7600.send_command("ATH")

    def answer_call(self) -> bytes:
        """
        接听来电
        Args:
            无

        Raises:
            无

        Notes:
            使用ATA指令接听当前振铃的来电，需在检测到来电后及时调用

        ==========================================
        Answer an incoming call
        Args:
            None

        Raises:
            None

        Notes:
            Use ATA command to answer the currently ringing incoming call, need to call in time after detecting incoming call
        """
        # 发送接听来电指令并返回响应
        return self.sim7600.send_command("ATA")

    def call_status(self) -> bytes:
        """
        查询当前通话状态
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CLCC指令查询当前通话列表及状态，返回数据包含通话方向、状态、号码等信息

        ==========================================
        Query current call status
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CLCC command to query current call list and status, return data includes call direction, status, number and other information
        """
        # 发送查询通话状态指令并返回响应
        return self.sim7600.send_command("AT+CLCC")

    def set_call_volume(self, level: int) -> bytes:
        """
        设置通话音量
        Args:
            level (int): 音量等级（通常0-10，不同模块范围可能略有差异）

        Raises:
            TypeError: 当level参数非整数类型时触发
            ValueError: 当level参数超出0-10范围时触发

        Notes:
            使用AT+CLVL指令设置通话音量，等级越高音量越大，建议设置范围1-8

        ==========================================
        Set call volume level
        Args:
            level (int): Volume level (usually 0-10, range may vary slightly for different modules)

        Raises:
            TypeError: Triggered when level parameter is not integer type
            ValueError: Triggered when level parameter is out of 0-10 range

        Notes:
            Use AT+CLVL command to set call volume, higher level means louder volume, recommended range 1-8
        """
        # 检查level参数类型和范围
        if not isinstance(level, int):
            raise TypeError("level parameter must be integer type")
        if level < 0 or level > 10:
            raise ValueError("level parameter must be in range 0-10")
        # 发送设置通话音量指令并返回响应
        return self.sim7600.send_command(f"AT+CLVL={level}")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
