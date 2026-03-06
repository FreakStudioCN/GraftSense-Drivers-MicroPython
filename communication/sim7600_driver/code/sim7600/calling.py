# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午8:30
# @Author  : alankrantas
# @File    : calling.py
# @Description : SIM7600模块通话功能类 实现拨打电话、挂断、接听、查询通话状态、设置通话音量等功能
# @License : MIT
# @Platform: MicroPython v1.23.0

__version__ = "1.0.0"
__author__ = "alankrantas"
__license__ = "MIT"
__platform__ = "Raspberry Pi Pico / MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================


# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class Calling:
    """
    SIM7600模块通话功能类
    SIM7600 Module Calling Function Class

    封装SIM7600模块的语音通话相关功能，包括拨打电话、挂断通话、接听来电、查询通话状态、设置通话音量等
    Encapsulates voice call-related functions of SIM7600 module, including making calls, hanging up, answering calls, querying call status, setting call volume, etc.

    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command方法用于发送AT指令
                          SIM7600 module core object, must contain send_command method for sending AT commands

    Methods:
        __init__(sim7600): 初始化通话功能类
                           Initialize calling function class
        make_call(number): 拨打指定电话号码
                           Make a call to the specified phone number
        hang_up(): 挂断当前通话
                   Hang up the current call
        answer_call(): 接听来电
                       Answer an incoming call
        call_status(): 查询当前通话状态
                       Query current call status
        set_call_volume(level): 设置通话音量
                                Set call volume level
    """

    def __init__(self, sim7600):
        """
        初始化通话功能类
        Initialize calling function class

        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command方法
                              SIM7600 module core object, must implement send_command method

        Returns:
            None

        Notes:
            依赖SIM7600核心对象的send_command方法进行AT指令通信
            Depends on the send_command method of the SIM7600 core object for AT command communication
        """
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def make_call(self, number):
        """
        拨打指定电话号码
        Make a call to the specified phone number

        Args:
            number (str): 要拨打的电话号码（支持固话/手机号）
                          Phone number to call (supports landline/mobile number)

        Returns:
            bytes: 拨号指令的响应数据
                   Response data of dial command

        Notes:
            使用ATD指令进行拨号，号码末尾必须添加分号;表示语音通话
            Use ATD command for dialing, number must end with semicolon ; to indicate voice call
        """
        # 发送拨号指令并返回响应
        return self.sim7600.send_command(f"ATD{number};")

    def hang_up(self):
        """
        挂断当前通话
        Hang up the current call

        Args:
            None

        Returns:
            bytes: 挂断指令的响应数据
                   Response data of hang up command

        Notes:
            使用ATH指令挂断当前所有通话，适用于主动挂断或拒接来电
            Use ATH command to hang up all current calls, suitable for active hang up or rejecting incoming calls
        """
        # 发送挂断通话指令并返回响应
        return self.sim7600.send_command("ATH")

    def answer_call(self):
        """
        接听来电
        Answer an incoming call

        Args:
            None

        Returns:
            bytes: 接听指令的响应数据
                   Response data of answer command

        Notes:
            使用ATA指令接听当前振铃的来电，需在检测到来电后及时调用
            Use ATA command to answer the currently ringing incoming call, need to call in time after detecting incoming call
        """
        # 发送接听来电指令并返回响应
        return self.sim7600.send_command("ATA")

    def call_status(self):
        """
        查询当前通话状态
        Query current call status

        Args:
            None

        Returns:
            bytes: 包含通话状态信息的响应数据
                   Response data containing call status information

        Notes:
            使用AT+CLCC指令查询当前通话列表及状态，返回数据包含通话方向、状态、号码等信息
            Use AT+CLCC command to query current call list and status, return data includes call direction, status, number and other information
        """
        # 发送查询通话状态指令并返回响应
        return self.sim7600.send_command("AT+CLCC")

    def set_call_volume(self, level):
        """
        设置通话音量
        Set call volume level

        Args:
            level (int): 音量等级（通常0-10，不同模块范围可能略有差异）
                         Volume level (usually 0-10, range may vary slightly for different modules)

        Returns:
            bytes: 设置音量指令的响应数据
                   Response data of set volume command

        Notes:
            使用AT+CLVL指令设置通话音量，等级越高音量越大，建议设置范围1-8
            Use AT+CLVL command to set call volume, higher level means louder volume, recommended range 1-8
        """
        # 发送设置通话音量指令并返回响应
        return self.sim7600.send_command(f"AT+CLVL={level}")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
