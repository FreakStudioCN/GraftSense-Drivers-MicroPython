# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/11/4 下午5:35   
# @Author  : 李清水            
# @File    : R60AFD1.py       
# @Description : R60AFD1雷达设备业务处理类相关代码
# @License : CC BY-NC 4.0

# ======================================== 导入相关模块 =========================================

from machine import Timer
import time
import micropython

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

def format_time():
    """
    格式化当前时间为 [YYYY-MM-DD HH:MM:SS.sss] 格式。

    Args:
        无

    Returns:
        str: 格式化后的时间字符串。

    Note:
        - 使用本地时间 time.localtime() 获取时间信息。
        - 毫秒部分通过 time.ticks_ms() % 1000 获取。
        - 返回格式示例: "[2025-11-04 17:35:30.123]"

    ==========================================

    Format current time to [YYYY-MM-DD HH:MM:SS.sss] format.

    Args:
        None

    Returns:
        str: Formatted time string.

    Note:
        - Uses local time via time.localtime().
        - Milliseconds part obtained via time.ticks_ms() % 1000.
        - Example return format: "[2025-11-04 17:35:30.123]"
    """
    t = time.localtime()
    ms = time.ticks_ms() % 1000
    return f"[{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}.{ms:03d}]"

# 计时装饰器，用于计算函数运行时间
def timed_function(f: callable, *args: tuple, **kwargs: dict) -> callable:
    """
    计时装饰器，用于计算并打印函数/方法运行时间。

    Args:
        f (callable): 需要计时的函数/方法。
        args (tuple): 传递给函数/方法的位置参数。
        kwargs (dict): 传递给函数/方法的关键字参数。

    Returns:
        callable: 包装后的计时函数。

    Note:
        - 通过 time.ticks_us() 获取高精度时间戳。
        - 计算函数执行前后的时间差，转换为毫秒输出。
        - 函数名通过字符串分割提取，可能不适用于所有情况。

    ==========================================

    Timing decorator for calculating and printing function/method execution time.

    Args:
        f (callable): Function/method to be timed.
        args (tuple): Positional arguments passed to the function/method.
        kwargs (dict): Keyword arguments passed to the function/method.

    Returns:
        callable: Wrapped timing function.

    Note:
        - Uses time.ticks_us() for high precision timing.
        - Calculates time difference before and after function execution, converts to milliseconds.
        - Function name extracted via string splitting, may not work in all cases.
    """
    myname = str(f).split(' ')[1]

    def new_func(*args: tuple, **kwargs: dict) -> any:
        t: int = time.ticks_us()
        result = f(*args, **kwargs)
        delta: int = time.ticks_diff(time.ticks_us(), t)
        print('Function {} Time = {:6.3f}ms'.format(myname, delta / 1000))
        return result

    return new_func

# ======================================== 自定义类 ============================================

# 自定义异常类
class DeviceInitializationError(Exception):
    """
    设备初始化错误异常类。

    当R60AFD1设备初始化过程中发生严重错误时抛出。

    ==========================================

    Device initialization error exception class.

    Raised when critical errors occur during R60AFD1 device initialization.
    """
    pass

class R60AFD1:

    # 是否启用调试
    DEBUG_ENABLED = False

    # R60AFD1雷达设备业务处理类中各种状态值和配置选项的常量
    # 运动信息状态（来自协议表）
    MOTION_NONE, MOTION_STATIC, MOTION_ACTIVE = (0x00, 0x01, 0x02)

    # 雷达故障状态
    FAULT_NONE,FAULT_HW_ERROR, FAULT_FW_ERROR = (0x00,0x01,0x02)

    # 跌倒检测状态
    FALL_NONE, FALL_DETECTED = (0x00, 0x01)

    # 静止驻留状态
    STATIC_STAY_NONE, STATIC_STAY_DETECTED = (0x00, 0x01)

    # 人体存在状态
    HUMAN_ABSENT, HUMAN_PRESENT = (0x00, 0x01)

    # 跌倒灵敏度档位（0-3，0为最低，3为最高）
    FALL_SENSITIVITY_LEVEL_0, FALL_SENSITIVITY_LEVEL_1, FALL_SENSITIVITY_LEVEL_2, FALL_SENSITIVITY_LEVEL_3 = (
    0x00, 0x01, 0x02, 0x03)

    # 安装方式（暂未在协议中明确定义，根据控制字0x06推测）
    INSTALL_ANGLE_SET, INSTALL_HEIGHT_SET = (0x01, 0x02)

    # 轨迹点上报开关
    TRACK_SWITCH_OFF, TRACK_SWITCH_ON = (0x00, 0x01)

    # 高度占比开关
    HEIGHT_RATIO_SWITCH_OFF, HEIGHT_RATIO_SWITCH_ON = (0x00, 0x01)

    # 最大能量值上报开关
    ENERGY_REPORT_OFF, ENERGY_REPORT_ON = (0x00, 0x01)

    # R60AFD1雷达设备指令类型常量
    # 基础指令信息查询和设置类型
    TYPE_QUERY_HEARTBEAT = 0  # 查询心跳/设备状态
    TYPE_MODULE_RESET = 1  # 模块复位/重启设备
    TYPE_QUERY_PRODUCT_MODEL = 2  # 查询产品型号
    TYPE_QUERY_PRODUCT_ID = 3  # 查询产品ID/序列号
    TYPE_QUERY_HARDWARE_MODEL = 4  # 查询硬件版本/型号
    TYPE_QUERY_FIRMWARE_VERSION = 5  # 查询固件版本号
    TYPE_QUERY_INIT_COMPLETE = 6  # 查询初始化完成状态
    TYPE_QUERY_SCENE_INFO = 9  # 查询场景信息

    # 安装参数设置与查询
    TYPE_SET_INSTALL_ANGLE = 10  # 设置安装角度
    TYPE_QUERY_INSTALL_ANGLE = 11  # 查询安装角度
    TYPE_SET_INSTALL_HEIGHT = 12  # 设置安装高度
    TYPE_QUERY_INSTALL_HEIGHT = 13  # 查询安装高度
    TYPE_AUTO_HEIGHT_MEASURE = 14  # 自动高度测量

    # 人体存在功能
    TYPE_CONTROL_HUMAN_PRESENCE_ON = 15  # 开启人体存在检测
    TYPE_CONTROL_HUMAN_PRESENCE_OFF = 16  # 关闭人体存在检测
    TYPE_QUERY_HUMAN_PRESENCE_SWITCH = 17  # 查询人体存在检测开关状态
    TYPE_QUERY_HUMAN_EXISTENCE_INFO = 18  # 查询人体存在信息
    TYPE_QUERY_HUMAN_MOTION_INFO = 19  # 查询人体运动信息
    TYPE_QUERY_BODY_MOTION_PARAM = 20  # 查询身体运动参数
    TYPE_QUERY_HEIGHT_RATIO = 21  # 查询高度占比/分布
    TYPE_QUERY_TRACK_POINT = 22  # 查询跟踪点信息
    TYPE_QUERY_TRACK_FREQUENCY = 23  # 查询跟踪频率
    TYPE_CONTROL_TRACK_SWITCH = 24  # 控制跟踪开关
    TYPE_QUERY_TRACK_SWITCH = 25  # 查询跟踪开关状态

    # 参数设置（静坐/运动距离、无人时间、阈值等）
    TYPE_SET_STATIC_DISTANCE = 26  # 设置静坐/静态距离阈值
    TYPE_QUERY_STATIC_DISTANCE = 27  # 查询静坐/静态距离阈值
    TYPE_SET_MOTION_DISTANCE = 28  # 设置运动距离阈值
    TYPE_QUERY_MOTION_DISTANCE = 29  # 查询运动距离阈值
    TYPE_SET_NO_PERSON_TIME = 30  # 设置无人时间阈值
    TYPE_QUERY_NO_PERSON_TIME = 31  # 查询无人时间阈值
    TYPE_SET_PRESENCE_THRESHOLD = 32  # 设置存在检测阈值
    TYPE_QUERY_PRESENCE_THRESHOLD = 33  # 查询存在检测阈值
    TYPE_CONTROL_ENERGY_REPORT_ON = 34  # 开启能量报告
    TYPE_CONTROL_ENERGY_REPORT_OFF = 35  # 关闭能量报告
    TYPE_QUERY_ENERGY_REPORT_SWITCH = 36  # 查询能量报告开关状态
    TYPE_QUERY_MAX_ENERGY = 37  # 查询最大能量值

    # 跌倒检测功能
    TYPE_CONTROL_FALL_DETECTION_ON = 38  # 开启跌倒检测
    TYPE_CONTROL_FALL_DETECTION_OFF = 39  # 关闭跌倒检测
    TYPE_QUERY_FALL_DETECTION_SWITCH = 40  # 查询跌倒检测开关状态
    TYPE_QUERY_FALL_STATUS = 41  # 查询跌倒状态
    TYPE_SET_FALL_DURATION = 42  # 设置跌倒持续时间
    TYPE_QUERY_FALL_DURATION = 43  # 查询跌倒持续时间
    TYPE_SET_STATIC_STAY_DURATION = 44  # 设置静态停留持续时间
    TYPE_QUERY_STATIC_STAY_DURATION = 45  # 查询静态停留持续时间
    TYPE_CONTROL_STATIC_STAY_ON = 46  # 开启静态停留检测
    TYPE_CONTROL_STATIC_STAY_OFF = 47  # 关闭静态停留检测
    TYPE_QUERY_STATIC_STAY_SWITCH = 48  # 查询静态停留检测开关状态
    TYPE_QUERY_STATIC_STAY_STATUS = 49  # 查询静态停留状态
    TYPE_SET_HEIGHT_ACCUMULATION_TIME = 50  # 设置高度累计时间
    TYPE_QUERY_HEIGHT_ACCUMULATION_TIME = 51  # 查询高度累计时间
    TYPE_SET_FALL_BREAK_HEIGHT = 52  # 设置跌倒断点高度
    TYPE_QUERY_FALL_BREAK_HEIGHT = 53  # 查询跌倒断点高度
    TYPE_CONTROL_HEIGHT_RATIO_ON = 54  # 开启高度占比检测
    TYPE_CONTROL_HEIGHT_RATIO_OFF = 55  # 关闭高度占比检测
    TYPE_QUERY_HEIGHT_RATIO_SWITCH = 56  # 查询高度占比检测开关状态
    TYPE_QUERY_FALL_SENSITIVITY = 57  # 查询跌倒检测灵敏度
    TYPE_SET_TRACK_FREQUENCY = 58  # 设置跟踪频率
    TYPE_SET_TRACK_SWITCH = 59  # 设置跟踪开关
    TYPE_SET_FALL_SENSITIVITY = 60 # 设置跌倒检测灵敏度

    # 指令映射表 - 将查询、开关、设置类型指令的命令字和控制字的具体值映射到帧参数
    COMMAND_MAP = {
        # 基础指令
        TYPE_QUERY_HEARTBEAT: {
            'control_byte': 0x01,
            'command_byte': 0x01,
            'data': bytes([0x0F])
        },
        TYPE_MODULE_RESET: {
            'control_byte': 0x01,
            'command_byte': 0x02,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_PRODUCT_MODEL: {
            'control_byte': 0x02,
            'command_byte': 0xA1,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_PRODUCT_ID: {
            'control_byte': 0x02,
            'command_byte': 0xA2,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_HARDWARE_MODEL: {
            'control_byte': 0x02,
            'command_byte': 0xA3,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_FIRMWARE_VERSION: {
            'control_byte': 0x02,
            'command_byte': 0xA4,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_INIT_COMPLETE: {
            'control_byte': 0x05,
            'command_byte': 0x81,
            'data': bytes([0x0F])
        },

        TYPE_QUERY_SCENE_INFO: {
            'control_byte': 0x05,
            'command_byte': 0x07,
            'data': bytes([0x0F])
        },

        # 安装参数
        TYPE_SET_INSTALL_ANGLE: {
            'control_byte': 0x06,
            'command_byte': 0x01,
            'data': None  # 动态设置：6字节角度数据
        },
        TYPE_QUERY_INSTALL_ANGLE: {
            'control_byte': 0x06,
            'command_byte': 0x81,
            'data': bytes([0x0F])
        },
        TYPE_SET_INSTALL_HEIGHT: {
            'control_byte': 0x06,
            'command_byte': 0x02,
            'data': None  # 动态设置：2字节高度
        },
        TYPE_QUERY_INSTALL_HEIGHT: {
            'control_byte': 0x06,
            'command_byte': 0x82,
            'data': bytes([0x0F])
        },
        TYPE_AUTO_HEIGHT_MEASURE: {
            'control_byte': 0x83,
            'command_byte': 0x90,
            'data': bytes([0x0F])
        },

        # 人体存在
        TYPE_CONTROL_HUMAN_PRESENCE_ON: {
            'control_byte': 0x80,
            'command_byte': 0x00,
            'data': bytes([0x01])
        },
        TYPE_CONTROL_HUMAN_PRESENCE_OFF: {
            'control_byte': 0x80,
            'command_byte': 0x00,
            'data': bytes([0x00])
        },
        TYPE_QUERY_HUMAN_PRESENCE_SWITCH: {
            'control_byte': 0x80,
            'command_byte': 0x80,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_HUMAN_EXISTENCE_INFO: {
            'control_byte': 0x80,
            'command_byte': 0x81,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_HUMAN_MOTION_INFO: {
            'control_byte': 0x80,
            'command_byte': 0x82,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_BODY_MOTION_PARAM: {
            'control_byte': 0x80,
            'command_byte': 0x83,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_HEIGHT_RATIO: {
            'control_byte': 0x83,
            'command_byte': 0x8E,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_TRACK_POINT: {
            'control_byte': 0x83,
            'command_byte': 0x92,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_TRACK_FREQUENCY: {
            'control_byte': 0x83,
            'command_byte': 0x93,
            'data': bytes([0x0F])
        },
        TYPE_CONTROL_TRACK_SWITCH: {
            # 动态设置：开关值
            'control_byte': 0x83,
            'command_byte': 0x94,
            'data': None
        },
        TYPE_QUERY_TRACK_SWITCH: {
            'control_byte': 0x83,
            'command_byte': 0x94,
            'data': bytes([0x0F])
        },

        # 参数设置
        TYPE_SET_STATIC_DISTANCE: {
            # 动态设置：2字节距离
            'control_byte': 0x80,
            'command_byte': 0x0D,
            'data': None
        },
        TYPE_QUERY_STATIC_DISTANCE: {
            'control_byte': 0x80,
            'command_byte': 0x8D,
            'data': bytes([0x0F])
        },
        TYPE_SET_MOTION_DISTANCE: {
            # 动态设置：2字节距离
            'control_byte': 0x80,
            'command_byte': 0x0E,
            'data': None
        },
        TYPE_QUERY_MOTION_DISTANCE: {
            'control_byte': 0x80,
            'command_byte': 0x8E,
            'data': bytes([0x0F])
        },
        TYPE_SET_NO_PERSON_TIME: {
            # 动态设置：4字节时间
            'control_byte': 0x80,
            'command_byte': 0x12,
            'data': None
        },
        TYPE_QUERY_NO_PERSON_TIME: {
            'control_byte': 0x80,
            'command_byte': 0x92,
            'data': bytes([0x0F])
        },
        TYPE_SET_PRESENCE_THRESHOLD: {
            # 动态设置：4字节阈值
            'control_byte': 0x80,
            'command_byte': 0x11,
            'data': None
        },
        TYPE_QUERY_PRESENCE_THRESHOLD: {
            'control_byte': 0x80,
            'command_byte': 0x91,
            'data': bytes([0x0F])
        },
        TYPE_CONTROL_ENERGY_REPORT_ON: {
            'control_byte': 0x80,
            'command_byte': 0x13,
            'data': bytes([0x01])
        },
        TYPE_CONTROL_ENERGY_REPORT_OFF: {
            'control_byte': 0x80,
            'command_byte': 0x13,
            'data': bytes([0x00])
        },
        TYPE_QUERY_ENERGY_REPORT_SWITCH: {
            'control_byte': 0x80,
            'command_byte': 0x93,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_MAX_ENERGY: {
            'control_byte': 0x80,
            'command_byte': 0x90,
            'data': bytes([0x0F])
        },

        # 跌倒检测
        TYPE_CONTROL_FALL_DETECTION_ON: {
            'control_byte': 0x83,
            'command_byte': 0x00,
            'data': bytes([0x01])
        },
        TYPE_CONTROL_FALL_DETECTION_OFF: {
            'control_byte': 0x83,
            'command_byte': 0x00,
            'data': bytes([0x00])
        },
        TYPE_QUERY_FALL_DETECTION_SWITCH: {
            'control_byte': 0x83,
            'command_byte': 0x80,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_FALL_STATUS: {
            'control_byte': 0x83,
            'command_byte': 0x81,
            'data': bytes([0x0F])
        },
        TYPE_SET_FALL_DURATION: {
            # 动态设置：4字节时长
            'control_byte': 0x83,
            'command_byte': 0x0C,
            'data': None
        },
        TYPE_QUERY_FALL_DURATION: {
            'control_byte': 0x83,
            'command_byte': 0x8C,
            'data': bytes([0x0F])
        },
        TYPE_SET_STATIC_STAY_DURATION: {
            # 动态设置：4字节时长
            'control_byte': 0x83,
            'command_byte': 0x0A,
            'data': None
        },
        TYPE_QUERY_STATIC_STAY_DURATION: {
            'control_byte': 0x83,
            'command_byte': 0x8A,
            'data': bytes([0x0F])
        },
        TYPE_CONTROL_STATIC_STAY_ON: {
            'control_byte': 0x83,
            'command_byte': 0x0B,
            'data': bytes([0x01])
        },
        TYPE_CONTROL_STATIC_STAY_OFF: {
            'control_byte': 0x83,
            'command_byte': 0x0B,
            'data': bytes([0x00])
        },
        TYPE_QUERY_STATIC_STAY_SWITCH: {
            'control_byte': 0x83,
            'command_byte': 0x8B,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_STATIC_STAY_STATUS: {
            'control_byte': 0x83,
            'command_byte': 0x85,
            'data': bytes([0x0F])
        },
        TYPE_SET_HEIGHT_ACCUMULATION_TIME: {
            # 动态设置：4字节时间
            'control_byte': 0x83,
            'command_byte': 0x0F,
            'data': None
        },
        TYPE_QUERY_HEIGHT_ACCUMULATION_TIME: {
            'control_byte': 0x83,
            'command_byte': 0x8F,
            'data': bytes([0x0F])
        },
        TYPE_SET_FALL_BREAK_HEIGHT: {
            # 动态设置：2字节高度
            'control_byte': 0x83,
            'command_byte': 0x11,
            'data': None
        },
        TYPE_QUERY_FALL_BREAK_HEIGHT: {
            'control_byte': 0x83,
            'command_byte': 0x91,
            'data': bytes([0x0F])
        },
        TYPE_CONTROL_HEIGHT_RATIO_ON: {
            'control_byte': 0x83,
            'command_byte': 0x15,
            'data': bytes([0x01])
        },
        TYPE_CONTROL_HEIGHT_RATIO_OFF: {
            'control_byte': 0x83,
            'command_byte': 0x15,
            'data': bytes([0x00])
        },
        TYPE_QUERY_HEIGHT_RATIO_SWITCH: {
            'control_byte': 0x83,
            'command_byte': 0x95,
            'data': bytes([0x0F])
        },
        TYPE_QUERY_FALL_SENSITIVITY: {
            'control_byte': 0x83,
            'command_byte': 0x8D,
            'data': bytes([0x0F])
        },
        TYPE_SET_TRACK_FREQUENCY: {
            # 动态设置：4字节时间
            'control_byte': 0x83,
            'command_byte': 0x13,
            'data': None
        },
        TYPE_SET_TRACK_SWITCH: {
            # 动态设置：开关值
            'control_byte': 0x83,
            'command_byte': 0x14,
            'data': None
        }
        ,
        TYPE_SET_FALL_SENSITIVITY: {
            # 动态设置:灵敏度
            'control_byte': 0x83,
            'command_byte': 0x0D,
            'data': None
        }
    }

    # 查询类型到名称的映射（用于调试输出）
    QUERY_NAME_MAP = {
        TYPE_QUERY_HEARTBEAT: "Heartbeat",
        TYPE_MODULE_RESET: "Module Reset",
        TYPE_QUERY_PRODUCT_MODEL: "Product Model",
        TYPE_QUERY_PRODUCT_ID: "Product ID",
        TYPE_QUERY_HARDWARE_MODEL: "Hardware Model",
        TYPE_QUERY_FIRMWARE_VERSION: "Firmware Version",
        TYPE_QUERY_INIT_COMPLETE: "Init Complete",
        TYPE_QUERY_SCENE_INFO: "Scene Info",

        TYPE_SET_INSTALL_ANGLE: "Set Install Angle",
        TYPE_QUERY_INSTALL_ANGLE: "Query Install Angle",
        TYPE_SET_INSTALL_HEIGHT: "Set Install Height",
        TYPE_QUERY_INSTALL_HEIGHT: "Query Install Height",
        TYPE_AUTO_HEIGHT_MEASURE: "Auto Height Measure",

        TYPE_CONTROL_HUMAN_PRESENCE_ON: "Human Presence ON",
        TYPE_CONTROL_HUMAN_PRESENCE_OFF: "Human Presence OFF",
        TYPE_QUERY_HUMAN_PRESENCE_SWITCH: "Human Presence Switch",
        TYPE_QUERY_HUMAN_EXISTENCE_INFO: "Presence Status",
        TYPE_QUERY_HUMAN_MOTION_INFO: "Human Motion Info",
        TYPE_QUERY_BODY_MOTION_PARAM: "Body Motion Parameter",
        TYPE_QUERY_HEIGHT_RATIO: "Height Ratio",
        TYPE_QUERY_TRACK_POINT: "Track Point",
        TYPE_QUERY_TRACK_FREQUENCY: "Track Frequency",
        TYPE_CONTROL_TRACK_SWITCH: "Control Track Switch",
        TYPE_QUERY_TRACK_SWITCH: "Query Track Switch",

        TYPE_SET_STATIC_DISTANCE: "Set Static Distance",
        TYPE_QUERY_STATIC_DISTANCE: "Query Static Distance",
        TYPE_SET_MOTION_DISTANCE: "Set Motion Distance",
        TYPE_QUERY_MOTION_DISTANCE: "Query Motion Distance",
        TYPE_SET_NO_PERSON_TIME: "Set No Person Time",
        TYPE_QUERY_NO_PERSON_TIME: "Query No Person Time",
        TYPE_SET_PRESENCE_THRESHOLD: "Set Presence Threshold",
        TYPE_QUERY_PRESENCE_THRESHOLD: "Query Presence Threshold",
        TYPE_CONTROL_ENERGY_REPORT_ON: "Energy Report ON",
        TYPE_CONTROL_ENERGY_REPORT_OFF: "Energy Report OFF",
        TYPE_QUERY_ENERGY_REPORT_SWITCH: "Energy Report Switch",
        TYPE_QUERY_MAX_ENERGY: "Query Max Energy",

        TYPE_CONTROL_FALL_DETECTION_ON: "Fall Detection ON",
        TYPE_CONTROL_FALL_DETECTION_OFF: "Fall Detection OFF",
        TYPE_QUERY_FALL_DETECTION_SWITCH: "Fall Detection Switch",
        TYPE_QUERY_FALL_STATUS: "Fall Status",
        TYPE_SET_FALL_DURATION: "Set Fall Duration",
        TYPE_QUERY_FALL_DURATION: "Query Fall Duration",
        TYPE_SET_STATIC_STAY_DURATION: "Set Static Stay Duration",
        TYPE_QUERY_STATIC_STAY_DURATION: "Query Static Stay Duration",
        TYPE_CONTROL_STATIC_STAY_ON: "Static Stay ON",
        TYPE_CONTROL_STATIC_STAY_OFF: "Static Stay OFF",
        TYPE_QUERY_STATIC_STAY_SWITCH: "Static Stay Switch",
        TYPE_QUERY_STATIC_STAY_STATUS: "Static Stay Status",
        TYPE_SET_HEIGHT_ACCUMULATION_TIME: "Set Height Accumulation Time",
        TYPE_QUERY_HEIGHT_ACCUMULATION_TIME: "Query Height Accumulation Time",
        TYPE_SET_FALL_BREAK_HEIGHT: "Set Fall Break Height",
        TYPE_QUERY_FALL_BREAK_HEIGHT: "Query Fall Break Height",
        TYPE_CONTROL_HEIGHT_RATIO_ON: "Height Ratio ON",
        TYPE_CONTROL_HEIGHT_RATIO_OFF: "Height Ratio OFF",
        TYPE_QUERY_HEIGHT_RATIO_SWITCH: "Height Ratio Switch",
        TYPE_QUERY_FALL_SENSITIVITY: "Query Fall Sensitivity",
        TYPE_SET_TRACK_FREQUENCY: "Set Track Frequency",
        TYPE_SET_TRACK_SWITCH: "Set Track Switch",
        TYPE_SET_FALL_SENSITIVITY: "Set Fall Sensitivity"
    }

    def __init__(self, data_processor, presence_enabled=True, track_report_enabled=True,
                 energy_report_enabled=True, height_ratio_enabled=True, fall_detection_enabled=True
                , static_stay_enabled=True,static_distance=30, motion_distance=30
                 , parse_interval=200,max_retries=3, retry_delay=100, init_timeout=5000):
        """
                初始化R60AFD1雷达设备类实例。

                Args:
                    data_processor: 数据处理器对象，用于处理接收到的数据帧
                    presence_enabled (bool): 人体存在检测功能开关
                    track_report_enabled (bool): 轨迹点上报功能开关
                    energy_report_enabled (bool): 能量值上报功能开关
                    height_ratio_enabled (bool): 高度占比上报功能开关
                    fall_detection_enabled (bool): 跌倒检测功能开关
                    static_stay_enabled (bool): 静止驻留检测功能开关
                    parse_interval (int): 数据解析间隔时间（毫秒），默认200ms
                    max_retries (int): 最大重试次数，默认3次
                    retry_delay (int): 重试延迟时间（毫秒），默认100ms
                    init_timeout (int): 初始化超时时间（毫秒），默认5000ms

                Raises:
                    ValueError: 当参数验证失败时抛出异常

                Note:
                    - 初始化时会验证参数的有效性范围
                    - 设置设备的默认状态和参数
                    - 创建内部定时器用于周期性操作

                ==========================================

                Initialize R60AFD1 radar device class instance.

                Args:
                    data_processor: Data processor object for handling received data frames
                    presence_enabled (bool): Human presence detection function switch
                    track_report_enabled (bool): Track point reporting function switch
                    energy_report_enabled (bool): Energy value reporting function switch
                    height_ratio_enabled (bool): Height ratio reporting function switch
                    fall_detection_enabled (bool): Fall detection function switch
                    static_stay_enabled (bool): Static stay detection function switch
                    parse_interval (int): Data parsing interval time (milliseconds), default 200ms
                    max_retries (int): Maximum retry attempts, default 3 times
                    retry_delay (int): Retry delay time (milliseconds), default 100ms
                    init_timeout (int): Initialization timeout time (milliseconds), default 5000ms

                Raises:
                    ValueError: Throws exception when parameter validation fails

                Note:
                    - Validates parameter validity ranges during initialization
                    - Sets device default states and parameters
                    - Creates internal timer for periodic operations
                """
        # 参数验证
        self._validate_init_parameters(
            parse_interval,max_retries, retry_delay, init_timeout
        )

        if parse_interval > 500:
            raise ValueError("parse_interval must be less than 500ms")

        self.data_processor = data_processor
        self.parse_interval = parse_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.init_timeout = init_timeout

        # 添加运行状态标志
        self._is_running = False
        self._initialization_complete = False
        self._configuration_errors = []

        # ============================= 系统级属性 ============================

        # 心跳包监控
        # 最后接收心跳包时间戳(ms)
        self.heartbeat_last_received = 0
        # 心跳超时累计次数
        self.heartbeat_timeout_count = 0
        # 实际心跳间隔统计(ms)
        self.heartbeat_interval = 0

        # 系统状态
        # 初始化完成状态(True/False)
        self.system_initialized = False
        # 初始化完成时间戳(ms)
        self.system_initialized_timestamp = 0
        # 模组复位状态标记
        self.module_reset_flag = False
        # 模组复位时间戳(ms)
        self.module_reset_timestamp = 0
        # 雷达故障状态(0:正常工作)
        self.radar_fault_status = 0
        # 工作时长(秒)
        self.working_duration = 0
        # 场景信息(默认0)
        self.scene_info = 0

        # 产品信息
        # 产品型号(字符串)
        self.product_model = ""
        # 产品ID(字符串)
        self.product_id = ""
        # 硬件型号(字符串)
        self.hardware_model = ""
        # 固件版本(字符串)
        self.firmware_version = ""

        # ============================ 安装配置属性 ==========================

        # 安装角度
        # X轴角度(度)
        self.install_angle_x = 0
        # Y轴角度(度)
        self.install_angle_y = 0
        # Z轴角度(度)
        self.install_angle_z = 0

        # 安装高度
        # 安装高度(cm)
        self.install_height = 0

        # 自动测高结果
        # 自动测量的高度(cm)，可能存在误差
        self.auto_height = 0

        # =========================== 人体存在检测属性 ==========================

        # 基本状态
        # 人体存在功能开关
        self.presence_enabled = presence_enabled
        # 存在状态
        # 0:无人, 1:有人
        self.presence_status = 0
        # 运动状态
        # 0:无, 1:静止, 2:活跃
        self.motion_status = 0

        # 量化数据
        # 体动参数(0-100)
        self.movement_parameter = 0
        # 最大能量值(0-0xffffffff)
        self.max_energy_value = 0
        # 能量值上报开关
        self.energy_report_enabled = energy_report_enabled

        # 高度占比统计
        # 高度占比开关
        self.height_ratio_enabled = height_ratio_enabled
        # 高度总数量
        self.height_total_count = 0
        # 0-0.5m高度占比(%)
        self.height_ratio_0_05 = 0
        # 0.5-1m高度占比(%)
        self.height_ratio_05_1 = 0
        # 1-1.5m高度占比(%)
        self.height_ratio_1_15 = 0
        # 1.5-2m高度占比(%)
        self.height_ratio_15_2 = 0

        # 轨迹点信息
        # 轨迹点上报开关
        self.track_report_enabled = track_report_enabled
        # 轨迹点上报频率(秒)
        self.track_report_frequency = 2
        # X坐标(有符号)
        self.track_position_x = 0
        # Y坐标(有符号)
        self.track_position_y = 0

        # 距离设置
        # 静坐水平距离(cm, 0-300)
        self.static_distance = static_distance
        # 运动水平距离(cm, 0-300)
        self.motion_distance = motion_distance

        # 阈值配置
        # 人体存在判断阈值(0-0xffffffff)
        self.presence_threshold = 0
        # 无人时间设置(秒, 5-1800)
        self.no_person_timeout = 30  # 默认30秒

        # ============================ 跌倒检测属性 ==========================

        # 功能配置
        # 跌倒检测开关
        self.fall_detection_enabled = fall_detection_enabled
        # 跌倒灵敏度档位(0-3)
        self.fall_sensitivity = 3  # 默认最高灵敏度
        # 跌倒时长设置(秒, 5-180)
        self.fall_duration_threshold = 10  # 默认10秒

        # 跌倒状态
        # 0:未跌倒, 1:跌倒
        self.fall_status = 0


        # 静止驻留检测
        # 静止驻留开关
        self.static_stay_enabled = static_stay_enabled
        # 静止驻留时长设置(秒, 60-3600)
        self.static_stay_duration = 300  # 默认5分钟
        # 静止驻留状态
        # 0:无静止驻留, 1:有静止驻留
        self.static_stay_status = 0

        # 高度相关参数
        # 高度累积时间(秒, 0-300)
        self.height_accumulation_time = 0
        # 跌倒打破高度(cm, 0-150)
        self.fall_break_height = 0

        # 查询状态管理
        # 是否有查询在进行中
        self._query_in_progress = False
        # 是否收到查询响应
        self._query_response_received = False
        # 查询结果
        self._query_result = None
        # 当前查询类型
        self._current_query_type = None
        # 默认查询超时时间(ms)
        self._query_timeout = 200

        # 内部使用的定时器
        self._timer = Timer(-1)

        try:
            # 启动定时器
            self._start_timer()

            # 执行完整的初始化流程
            self._complete_initialization()

            self._initialization_complete = True

            if R60AFD1.DEBUG_ENABLED:
                print(f"[Init] R60AFD1 initialized successfully")
                status = self.get_configuration_status()
                print(f"[Init] Configuration errors: {len(status['configuration_errors'])}")
                print(f"[Init] Product: {self.product_model} v{self.firmware_version}")

        except Exception as e:
            # 初始化失败，停止定时器
            self._is_running = False
            if hasattr(self, '_timer'):
                self._timer.deinit()
            raise DeviceInitializationError(f"Device initialization failed: {str(e)}")

    def get_configuration_status(self):
        """
        获取设备配置状态。

        Returns:
            dict: 包含配置状态的字典。

        Note:
            - 返回初始化完成状态、配置错误列表、设备信息和当前设置。
            - 配置错误列表是原始列表的副本，防止外部修改。

        ==========================================

        Get device configuration status.

        Returns:
            dict: Dictionary containing configuration status.

        Note:
            - Returns initialization completion status, configuration errors list, device information and current settings.
            - Configuration errors list is a copy of the original list to prevent外部 modification.
        """
        return {
            'initialization_complete': self._initialization_complete,
            'configuration_errors': self._configuration_errors.copy(),
            'device_info': {
                'product_model': self.product_model,
                'product_id': self.product_id,
                'hardware_model': self.hardware_model,
                'firmware_version': self.firmware_version,
                'system_initialized': self.system_initialized,
                'working_duration': self.working_duration,
                'radar_fault_status': self.radar_fault_status,
                'scene_info': self.scene_info
            },
            'installation_settings': {
                'install_angle_x': self.install_angle_x,
                'install_angle_y': self.install_angle_y,
                'install_angle_z': self.install_angle_z,
                'install_height': self.install_height,
                'auto_height': self.auto_height
            },
            'function_switches': {
                'presence_enabled': self.presence_enabled,
                'energy_report_enabled': self.energy_report_enabled,
                'height_ratio_enabled': self.height_ratio_enabled,
                'track_report_enabled': self.track_report_enabled,
                'fall_detection_enabled': self.fall_detection_enabled,
                'static_stay_enabled': self.static_stay_enabled
            },
            'detection_parameters': {
                'presence_status': self.presence_status,
                'motion_status': self.motion_status,
                'movement_parameter': self.movement_parameter,
                'max_energy_value': self.max_energy_value,
                'height_total_count': self.height_total_count,
                'height_ratio_0_05': self.height_ratio_0_05,
                'height_ratio_05_1': self.height_ratio_05_1,
                'height_ratio_1_15': self.height_ratio_1_15,
                'height_ratio_15_2': self.height_ratio_15_2,
                'track_position_x': self.track_position_x,
                'track_position_y': self.track_position_y,
                'static_distance': self.static_distance,
                'motion_distance': self.motion_distance,
                'presence_threshold': self.presence_threshold,
                'no_person_timeout': self.no_person_timeout,
                'fall_sensitivity': self.fall_sensitivity,
                'fall_status': self.fall_status,
                'fall_duration_threshold': self.fall_duration_threshold,
                'static_stay_status': self.static_stay_status,
                'static_stay_duration': self.static_stay_duration,
                'height_accumulation_time': self.height_accumulation_time,
                'fall_break_height': self.fall_break_height
            },
            'system_timestamps': {
                'heartbeat_last_received': self.heartbeat_last_received,
                'heartbeat_timeout_count': self.heartbeat_timeout_count,
                'heartbeat_interval': self.heartbeat_interval,
                'system_initialized_timestamp': self.system_initialized_timestamp,
                'module_reset_timestamp': self.module_reset_timestamp
            },
            'timing_settings': {
                'track_report_frequency': self.track_report_frequency
            },
            'operational_status': {
                'is_running': self._is_running,
                'query_in_progress': self._query_in_progress,
                'query_response_received': self._query_response_received,
                'parse_interval': self.parse_interval,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'init_timeout': self.init_timeout
            }
        }
    def _validate_init_parameters(self, parse_interval,max_retries, retry_delay, init_timeout):
        """
        验证初始化参数。

        Args:
            parse_interval: 数据解析间隔。
            max_retries: 最大重试次数。
            retry_delay: 重试延迟时间。
            init_timeout: 初始化超时时间。

        Raises:
            ValueError: 参数验证失败。

        Note:
            - 检查各参数是否在有效范围内。
            - 无人计时时长必须是30-180分钟且步长为10分钟。
            - 睡眠截止时长必须是5-120分钟。

        ==========================================

        Validate initialization parameters.

        Args:
            parse_interval: Data parsing interval.
            max_retries: Maximum retry count.
            retry_delay: Retry delay time.
            init_timeout: Initialization timeout.

        Raises:
            ValueError: Parameter validation failed.

        Note:
            - Check if each parameter is within valid range.
            - No person timing duration must be 30-180 minutes in steps of 10 minutes.
            - Sleep cutoff duration must be 5-120 minutes.
        """
        if parse_interval > 500 or parse_interval < 10:
            raise ValueError("parse_interval must be between 10ms and 500ms")

        if max_retries < 0 or max_retries > 10:
            raise ValueError("max_retries must be between 0 and 10")

        if retry_delay < 0 or retry_delay > 1000:
            raise ValueError("retry_delay must be between 0ms and 1000ms")

        if init_timeout < 1000 or init_timeout > 30000:
            raise ValueError("init_timeout must be between 1000ms and 30000ms")
    def _execute_operation(self, operation_type, data=None, timeout=200):
        """
        执行操作（查询或设置）的统一方法。

        Args:
            operation_type: 操作类型常量。
            data: 数据部分，如果为None则使用COMMAND_MAP中的默认数据。
            timeout: 超时时间，单位毫秒。

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
                    - 指令发送成功状态: True-成功发送并收到正确响应, False-发送失败或超时
                    - 实际执行结果: 操作执行的具体结果 (成功时有效)

        Note:
            - 检查是否已有操作在进行中，避免冲突。
            - 临时禁用定时器回调，避免竞争条件。
            - 从指令映射表获取帧参数并构建发送帧。
            - 等待设备响应，超时返回失败。

        ==========================================


        Unified method for executing operations (query or set).

        Args:
            operation_type: Operation type constant.
            data: Data part, if None uses default data from COMMAND_MAP.
            timeout: Timeout in milliseconds.

        Returns:
            tuple: (Command sending success status, actual execution result)
                    - Command sending success status: True-successfully sent and received correct response, False-send failed or timeout
                    - Actual execution result: Specific result of operation execution (valid when successful)

        Note:
            - Check if another operation is in progress to avoid conflicts.
            - Temporarily disable timer callback to avoid race conditions.
            - Get frame parameters from command mapping table and build send frame.
            - Wait for device response, return failure on timeout.
        """
        # 检查是否已有操作在进行中
        if self._query_in_progress:
            if R60AFD1.DEBUG_ENABLED:
                print("[Operation] Another operation in progress, aborting")
            return False, None

        try:
            # 临时禁用定时器回调，避免竞争
            original_running = self._is_running
            self._is_running = False

            # 设置操作状态
            self._query_in_progress = True
            self._query_response_received = False
            self._query_result = None
            self._current_query_type = operation_type

            # 从指令映射表获取帧参数
            if operation_type not in self.COMMAND_MAP:
                if R60AFD1.DEBUG_ENABLED:
                    print(f"[Operation] Unknown operation type: {operation_type}")
                return False, None

            cmd_params = self.COMMAND_MAP[operation_type]

            # 使用传入的数据或默认数据
            data_to_send = data if data is not None else cmd_params['data']

            # 构建并发送帧
            operation_frame = self.data_processor.build_and_send_frame(
                control_byte=cmd_params['control_byte'],
                command_byte=cmd_params['command_byte'],
                data=data_to_send
            )

            if not operation_frame:
                return False, None

            # 调试信息
            if R60AFD1.DEBUG_ENABLED:
                operation_name = self.QUERY_NAME_MAP.get(operation_type, f"Unknown({operation_type})")
                print(f"[Operation] {operation_name} operation sent")
                frame_hex = ' '.join(['{:02X}'.format(b) for b in operation_frame])
                print(f"[Operation] Sent frame: {frame_hex}")

            # 等待设备响应
            start_time = time.ticks_ms()
            while not self._query_response_received:
                # 检查超时
                if time.ticks_diff(time.ticks_ms(), start_time) >= timeout:
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[Operation] {operation_name} operation timeout")
                    return False, None

                # 短暂延迟，避免完全占用CPU
                time.sleep_us(100)

                # 继续处理数据流（确保响应能被解析）
                frames = self.data_processor.read_and_parse()
                for frame in frames:
                    self.update_properties_from_frame(frame)

            # 返回操作执行结果：(指令发送成功状态, 实际执行结果)
            return True, self._query_result

        except Exception as e:
            if R60AFD1.DEBUG_ENABLED:
                operation_name = self.QUERY_NAME_MAP.get(operation_type, f"Unknown({operation_type})")
                print(f"[Operation] {operation_name} operation error: {e}")
            return False, None
        finally:
            # 重置所有操作状态
            self._query_in_progress = False
            self._query_response_received = False
            self._query_result = None
            self._current_query_type = None

            # 安全地恢复定时器状态
            try:
                self._is_running = original_running
            except NameError:
                pass

            if R60AFD1.DEBUG_ENABLED:
                print("[Operation] Operation state reset")

    def _start_timer(self):
        """
        启动定时器。

        Note:
            - 设置定时器为周期性模式，周期为parse_interval毫秒。
            - 定时器回调函数为_timer_callback。
            - 同时设置运行状态标志为True。

        ==========================================

        Start timer.

        Note:
            - Set timer to periodic mode with period of parse_interval milliseconds.
            - Timer callback function is _timer_callback.
            - Also set running status flag to True.
        """
        self._is_running = True
        self._timer.init(period=self.parse_interval, mode=Timer.PERIODIC, callback=self._timer_callback)

    def _timer_callback(self, timer):
        """
        定时器回调函数，定期解析数据帧。

        Args:
            timer: 定时器实例。

        Note:
            - 检查设备是否在运行状态。
            - 调用DataFlowProcessor的解析方法获取数据帧。
            - 使用micropython.schedule安全地异步处理每个帧。

        ==========================================

        Timer callback function, periodically parses data frames.

        Args:
            timer: Timer instance.

        Note:
            - Check if device is in running state.
            - Call DataFlowProcessor's parsing method to get data frames.
            - Use micropython.schedule to safely asynchronously process each frame.
        """
        if not self._is_running:
            return

        # 调用DataFlowProcessor的解析方法
        frames = self.data_processor.read_and_parse()

        # 对每个解析到的帧使用micropython.schedule进行异步处理
        for frame in frames:
            # 使用micropython.schedule安全地调用属性更新方法
            micropython.schedule(self.update_properties_from_frame, frame)
    def _load_device_information(self):
        """
        加载设备基本信息。

        Returns:
            bool: 是否成功加载所有设备信息。

        Note:
            - 依次查询产品型号、产品ID、硬件型号、固件版本。
            - 任何一项查询失败都会记录错误信息。
            - 返回True表示所有信息都成功加载。

        ==========================================

        Load device basic information.

        Returns:
            bool: Whether all device information was successfully loaded.

        Note:
            - Sequentially query product model, product ID, hardware model, firmware version.
            - Any query failure will record error information.
            - Returns True if all information is successfully loaded.
        """
        info_queries = [
            ("Product Model", self.query_product_model),
            ("Product ID", self.query_product_id),
            ("Hardware Model", self.query_hardware_model),
            ("Firmware Version", self.query_firmware_version)
        ]

        all_success = True
        for info_name, query_func in info_queries:
            success = self._execute_with_retry(query_func, f"Load {info_name}")
            if not success:
                all_success = False
                self._configuration_errors.append(f"Failed to load {info_name}")
                if R60AFD1.DEBUG_ENABLED:
                    print(f"[Init] Warning: Failed to load {info_name}")

        return all_success
    def _execute_with_retry(self, operation, operation_name, timeout=200):
        """
        带重试的执行操作。

        Args:
            operation: 要执行的操作函数。
            operation_name: 操作名称（用于调试）。
            timeout: 单次操作超时时间。

        Returns:
            bool: 操作是否成功执行。

        Note:
            - 最多重试max_retries次。
            - 每次重试间隔retry_delay毫秒。
            - 所有重试都失败返回False。

        ==========================================

        Execute operation with retry.

        Args:
            operation: Operation function to execute.
            operation_name: Operation name (for debugging).
            timeout: Single operation timeout.

        Returns:
            bool: Whether operation was successfully executed.

        Note:
            - Maximum retry count: max_retries.
            - Retry interval: retry_delay milliseconds.
            - Returns False if all retries fail.
        """
        for attempt in range(self.max_retries + 1):
            try:
                success, result = operation(timeout=timeout)
                if success:
                    return True

                if attempt < self.max_retries:
                    time.sleep_ms(self.retry_delay)

            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep_ms(self.retry_delay)
                else:
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[Init] {operation_name} failed after {self.max_retries + 1} attempts: {e}")

        return False
    def _wait_for_device_initialization(self, timeout=None):
        """
        等待设备初始化完成。

        Args:
            timeout: 超时时间，单位毫秒。

        Returns:
            bool: 设备是否初始化完成。

        Note:
            - 周期性查询设备初始化状态。
            - 超时时间内未完成初始化则返回False。
            - 默认使用实例的init_timeout作为超时时间。

        ==========================================

        Wait for device initialization completion.

        Args:
            timeout: Timeout in milliseconds.

        Returns:
            bool: Whether device initialization is complete.

        Note:
            - Periodically query device initialization status.
            - Returns False if initialization not completed within timeout.
            - Uses instance's init_timeout as default timeout.
        """
        if timeout is None:
            timeout = self.init_timeout

        start_time = time.ticks_ms()

        while time.ticks_diff(time.ticks_ms(), start_time) < timeout:
            success, init_status = self.query_init_complete(timeout=500)
            if success and init_status:
                if R60AFD1.DEBUG_ENABLED:
                    print("[Init] Device initialization confirmed")
                return True

            # 短暂延迟后重试
            time.sleep_ms(200)

        if R60AFD1.DEBUG_ENABLED:
            print("[Init] Device initialization timeout")
        return False
    def _reset_and_wait_for_initialization(self):
        """
        重置设备并等待初始化完成。

        Returns:
            bool: 重置和初始化是否成功。

        Note:
            - 发送复位指令后等待3秒让设备重启。
            - 然后重新等待初始化完成，使用10秒超时。
            - 返回True表示重置和初始化都成功。

        ==========================================

        Reset device and wait for initialization completion.

        Returns:
            bool: Whether reset and initialization were successful.

        Note:
            - Wait 3 seconds for device restart after sending reset command.
            - Then wait for initialization completion again with 10 second timeout.
            - Returns True if both reset and initialization are successful.
        """
        # 发送复位指令
        reset_success = self._execute_with_retry(
            self.reset_module,
            "Reset Device",
            timeout=1000
        )

        if not reset_success:
            return False

        # 等待3秒让设备重启
        if R60AFD1.DEBUG_ENABLED:
            print("[Init] Waiting 3 seconds for device reset...")
        time.sleep(3)

        # 重新等待初始化完成
        return self._wait_for_device_initialization(timeout=10000)  # 10秒超时
    def _auto_configure_device(self):
        """
        自动配置设备功能。

        Note:
            - 根据初始化参数配置各功能模块。
            - 包括人体存在、心率监测、呼吸监测、睡眠监测等。
            - 每个配置步骤失败都会记录错误信息。

        ==========================================

        Auto-configure device functions.

        Note:
            - Configure each function module based on initialization parameters.
            - Includes human presence, heart rate monitoring, breath monitoring, sleep monitoring, etc.
            - Each configuration step failure records error information.
        """
        configuration_steps = []
        # ============================ 安装参数配置 ============================

        # 设置安装角度（如果有提供）
        if hasattr(self, 'install_angle_x') and hasattr(self, 'install_angle_y') and hasattr(self, 'install_angle_z'):
            if self.install_angle_x != 0 or self.install_angle_y != 0 or self.install_angle_z != 0:
                configuration_steps.append((
                    f"Set install angle (X:{self.install_angle_x}, Y:{self.install_angle_y}, Z:{self.install_angle_z})",
                    lambda: self.set_install_angle(self.install_angle_x, self.install_angle_y, self.install_angle_z)
                ))

        # 设置安装高度（如果有提供）
        if hasattr(self, 'install_height') and self.install_height > 0:
            configuration_steps.append((
                f"Set install height to {self.install_height}cm",
                lambda: self.set_install_height(self.install_height)
            ))

        # 人体存在检测配置
        # 设置人体存在开关
        if self.presence_enabled:
            configuration_steps.append((
                "Enable Human Presence Detection",
                lambda: self.set_presence_switch(True)
            ))

            # 设置静坐水平距离
            if hasattr(self, 'static_distance') and self.static_distance > 0:
                configuration_steps.append((
                    f"Set static distance to {self.static_distance}cm",
                    lambda: self.set_static_distance(self.static_distance)
                ))

            # 设置运动水平距离
            if hasattr(self, 'motion_distance') and self.motion_distance > 0:
                configuration_steps.append((
                    f"Set motion distance to {self.motion_distance}cm",
                    lambda: self.set_motion_distance(self.motion_distance)
                ))

            # 设置无人时间
            if hasattr(self, 'no_person_timeout') and self.no_person_timeout > 0:
                configuration_steps.append((
                    f"Set no-person timeout to {self.no_person_timeout} seconds",
                    lambda: self.set_no_person_time(self.no_person_timeout)
                ))

            # 设置人体存在判断阈值
            if hasattr(self, 'presence_threshold') and self.presence_threshold > 0:
                configuration_steps.append((
                    f"Set presence threshold to {self.presence_threshold}",
                    lambda: self.set_presence_threshold(self.presence_threshold)
                ))

            # 设置能量值上报开关
            if self.energy_report_enabled:
                configuration_steps.append((
                    "Enable energy report",
                    lambda: self.set_energy_report_switch(True)
                ))
            else:
                configuration_steps.append((
                    "Disable energy report",
                    lambda: self.set_energy_report_switch(False)
                ))

            # 设置高度占比开关
            if self.height_ratio_enabled:
                configuration_steps.append((
                    "Enable height ratio reporting",
                    lambda: self.set_height_ratio_switch(True)
                ))
            else:
                configuration_steps.append((
                    "Disable height ratio reporting",
                    lambda: self.set_height_ratio_switch(False)
                ))

            # 设置轨迹点上报开关
            if self.track_report_enabled:
                configuration_steps.append((
                    f"Enable track reporting (frequency: {self.track_report_frequency}s)",
                    lambda: self.set_track_switch(True)
                ))

                # 设置轨迹点上报频率
                if hasattr(self, 'track_report_frequency') and self.track_report_frequency > 0:
                    configuration_steps.append((
                        f"Set track report frequency to {self.track_report_frequency} seconds",
                        lambda: self.set_track_frequency(self.track_report_frequency)
                    ))
            else:
                configuration_steps.append((
                    "Disable track reporting",
                    lambda: self.set_track_switch(False)
                ))

        else:
            configuration_steps.append((
                "Disable Human Presence Detection",
                lambda: self.set_presence_switch(False)
            ))
        # ============================ 跌倒检测配置 ============================

        # 设置跌倒检测开关
        if self.fall_detection_enabled:
            configuration_steps.append((
                "Enable Fall Detection",
                lambda: self.set_fall_detection_switch(True)
            ))

            # 设置跌倒时长
            if hasattr(self, 'fall_duration_threshold') and self.fall_duration_threshold > 0:
                configuration_steps.append((
                    f"Set fall duration threshold to {self.fall_duration_threshold} seconds",
                    lambda: self.set_fall_duration(self.fall_duration_threshold)
                ))

            # 设置跌倒灵敏度
            if hasattr(self, 'fall_sensitivity') and self.fall_sensitivity > 0:
                configuration_steps.append((
                    f"Set fall sensitivity to {self.fall_sensitivity}",
                    lambda: self.set_fall_sensitivity(self.fall_sensitivity)
                ))

            # 设置跌倒打破高度
            if hasattr(self, 'fall_break_height') and self.fall_break_height >= 0:
                configuration_steps.append((
                    f"Set fall break height to {self.fall_break_height}cm",
                    lambda: self.set_fall_break_height(self.fall_break_height)
                ))

            # 设置高度累积时间
            if hasattr(self, 'height_accumulation_time') and self.height_accumulation_time >= 0:
                configuration_steps.append((
                    f"Set height accumulation time to {self.height_accumulation_time} seconds",
                    lambda: self.set_height_accumulation_time(self.height_accumulation_time)
                ))

            # 设置静止驻留开关
            if self.static_stay_enabled:
                configuration_steps.append((
                    "Enable Static Stay Detection",
                    lambda: self.set_static_stay_switch(True)
                ))

                # 设置静止驻留时长
                if hasattr(self, 'static_stay_duration') and self.static_stay_duration > 0:
                    configuration_steps.append((
                        f"Set static stay duration to {self.static_stay_duration} seconds",
                        lambda: self.set_static_stay_duration(self.static_stay_duration)
                    ))
            else:
                configuration_steps.append((
                    "Disable Static Stay Detection",
                    lambda: self.set_static_stay_switch(False)
                ))

        else:
            configuration_steps.append((
                "Disable Fall Detection",
                lambda: self.set_fall_detection_switch(False)
            ))
        # 执行配置步骤
        for step_name, step_function in configuration_steps:
            success = self._execute_with_retry(step_function, step_name)
            if not success:
                self._configuration_errors.append(f"Failed to {step_name}")
                if R60AFD1.DEBUG_ENABLED:
                    print(f"[Init] Warning: {step_name} failed")

    def _verify_critical_configuration(self):
        """
           验证关键配置是否成功。

           Note:
               - 验证设备初始化状态和基本功能状态。
               - 根据启用的功能验证相应模块的开关状态。
               - 验证失败会记录到配置错误列表中。

           ==========================================

           Verify critical configuration success.

           Note:
               - Verify device initialization status and basic function status.
               - Verify switch status of corresponding modules based on enabled functions.
               - Verification failures are recorded in configuration errors list.
           """

        critical_verifications = []

        # 验证设备初始化状态
        critical_verifications.append(("Device Initialization", self.query_init_complete))
        # 根据启用的功能添加验证
        # 人体存在检测
        if self.presence_enabled:
            critical_verifications.append(("Human Presence Detection Switch", self.query_presence_switch))
        # 轨迹点上报
        if self.track_report_enabled:
            critical_verifications.append(("Track Reporting Switch", self.query_track_switch))
        # 能量值上报
        if self.energy_report_enabled:
            critical_verifications.append(("Energy Report Switch", self.query_energy_report_switch))
        # 高度占比上报
        if self.height_ratio_enabled:
            critical_verifications.append(("Height Ratio Reporting Switch", self.query_height_ratio_switch))
        # 静止驻留检测
        if self.static_stay_enabled:
            critical_verifications.append(("Static Stay Detection Switch", self.query_static_stay_switch))
        # 跌倒检测
        if self.fall_detection_enabled:
            critical_verifications.append(("Fall Detection Switch", self.query_fall_detection_switch))

        # 执行验证步骤
        for verify_name, verify_func in critical_verifications:
            success, result = verify_func(timeout=500)
            if not success:
                self._configuration_errors.append(f"Verification failed: {verify_name}")
                if R60AFD1.DEBUG_ENABLED:
                    print(f"[Init] Warning: {verify_name} verification failed")
    def _complete_initialization(self):
        """
        完整的初始化流程。

        Raises:
            DeviceInitializationError: 初始化失败。

        Note:
            - 步骤1: 读取设备基本信息。
            - 步骤2: 检查并等待设备初始化完成。
            - 步骤3: 配置设备功能。
            - 步骤4: 验证关键功能配置。
            - 如果初始化失败，会尝试重启设备。

        ==========================================

        Complete initialization process.

        Raises:
            DeviceInitializationError: Initialization failed.

        Note:
            - Step 1: Read device basic information.
            - Step 2: Check and wait for device initialization completion.
            - Step 3: Configure device functions.
            - Step 4: Verify critical function configuration.
            - If initialization fails, attempts to restart the device.
        """
        start_time = time.ticks_ms()
        # 步骤1: 读取设备基本信息
        device_info_loaded = self._load_device_information()
        if not device_info_loaded:
            raise DeviceInitializationError("Failed to load device information")

        # 步骤2: 检查并等待设备初始化完成
        init_success = self._wait_for_device_initialization()
        if not init_success:
            # 尝试重启设备
            if R60AFD1.DEBUG_ENABLED:
                print("[Init] Device not initialized, attempting reset...")
            reset_success = self._reset_and_wait_for_initialization()
            if not reset_success:
                raise DeviceInitializationError("Device initialization failed even after reset")

        # 步骤3: 配置设备功能
        self._auto_configure_device()

        # 步骤4: 验证关键功能配置
        self._verify_critical_configuration()

        elapsed_time = time.ticks_diff(time.ticks_ms(), start_time)
        if R60AFD1.DEBUG_ENABLED:
            print(f"[Init] Initialization completed in {elapsed_time}ms")
    def _handle_query_response(self, expected_type, response_data, response_name=""):
        """
        统一处理查询响应

        Args:
            expected_type: 期望的查询类型
            response_data: 响应数据
            response_name: 响应名称（用于调试）
        """
        # 情况1：正确时间正确读取
        if (self._query_in_progress and
                self._current_query_type == expected_type and
                not self._query_response_received):

            self._query_result = response_data
            self._query_response_received = True

            if R60AFD1.DEBUG_ENABLED:
                query_name = self.QUERY_NAME_MAP.get(expected_type, f"Unknown({expected_type})")
                print(f"[Query] {query_name} response received: {response_data}")

        # 情况2：当前正在进行其他类型的查询，但收到了本响应
        elif self._query_in_progress and self._current_query_type != expected_type:
            if R60AFD1.DEBUG_ENABLED:
                current_query = self.QUERY_NAME_MAP.get(self._current_query_type,
                                                        f"Unknown({self._current_query_type})")
                print(f"[Query] Unexpected {response_name} response during {current_query} query: {response_data}")

        # 情况3：没有查询在进行，但收到了查询响应
        elif not self._query_in_progress:
            if R60AFD1.DEBUG_ENABLED:
                print(f"[Query] Unsolicited {response_name} response: {response_data}")

    def _parse_height_data(self, data):
        """
        解析高度占比数据
        Args:
            data:

        Returns:

        """
        if data and len(data) >= 6:
            # 第一个字节：高8位
            height_total_high = data[0]
            # 第二个字节：低8位
            height_total_low = data[1]
            height_total = (height_total_high << 8) | height_total_low
            # 第三个字节：0-0.5m高度占比
            ratio_0_05 = data[2]
            # 第四个字节：0.5-1m高度占比
            ratio_05_1 = data[3]
            # 第五个字节：1-1.5m高度占比
            ratio_1_15 = data[4]
            # 第六个字节: 1.5-2m高度占比
            ratio_15_2 = data[5]
            return height_total, ratio_0_05, ratio_05_1, ratio_1_15, ratio_15_2

    def _parse_angle_data(self, data_bytes):
        """
        解析三轴角度数据

        数据格式：
        字节1-2: X轴角度 (16位有符号整数)
        字节3-4: Y轴角度 (16位有符号整数)
        字节5-6: Z轴角度 (16位有符号整数)

        返回: (x_angle, y_angle, z_angle) 元组，单位为度
        """
        if len(data_bytes) != 6:
            return (0, 0, 0)
        x = self._parse_signed_16bit_special(data_bytes[0:2])
        y = self._parse_signed_16bit_special(data_bytes[2:4])
        z = self._parse_signed_16bit_special(data_bytes[4:6])

        return (x, y, z)

    def _parse_signed_16bit_special(self, two_bytes):
        """
        解析有符号16位数据（特殊格式：首位符号位 + 后15位数值位）。

        Args:
            two_bytes: 2字节的字节序列（大端序）。

        Returns:
            int: 有符号16位整数。

        Note:
            - 最高位为符号位，0=正数，1=负数，剩余15位为数值。
            - 组合成16位无符号整数（大端序）。
            - 根据符号位确定正负值。

        ==========================================

        Parse signed 16-bit data (special format: first bit sign bit + remaining 15 bits value).

        Args:
            two_bytes: 2-byte byte sequence (big-endian).

        Returns:
            int: Signed 16-bit integer.

        Note:
            - Highest bit is sign bit, 0=positive, 1=negative, remaining 15 bits are value.
            - Combine into 16-bit unsigned integer (big-endian).
            - Determine positive/negative value based on sign bit.
        """
        if len(two_bytes) != 2:
            return 0

        # 组合成16位无符号整数（大端序）
        unsigned_value = (two_bytes[0] << 8) | two_bytes[1]

        # 提取符号位和数值
        sign_bit = (unsigned_value >> 15) & 0x1  # 最高位为符号位
        magnitude = unsigned_value & 0x7FFF      # 低15位为数值

        # 根据符号位确定正负
        if sign_bit == 1:  # 负数
            return -magnitude
        else:  # 正数
            return magnitude
    def _parse_product_info_data(self, data_bytes):
        """
        解析产品信息数据 (可变长度字符串)。

        Args:
            data_bytes: 产品信息字节数据。

        Returns:
            tuple: (产品信息字符串,)

        Note:
            - 正确处理包含空字节的字符串。
            - 找到第一个空字节的位置，截取有效部分。
            - 优先使用UTF-8解码，失败时尝试ASCII解码。

        ==========================================

        Parse product information data (variable length string).

        Args:
            data_bytes: Product information byte data.

        Returns:
            tuple: (Product information string,)

        Note:
            - Correctly handles strings containing null bytes.
            - Find position of first null byte, extract valid part.
            - Prefer UTF-8 decoding, fall back to ASCII decoding if failed.
        """
        try:
            if R60AFD1.DEBUG_ENABLED:
                print(f"[Parse] Raw product data: {data_bytes}, hex: {data_bytes.hex()}")

            # 找到第一个空字节的位置，截取有效部分
            if b'\x00' in data_bytes:
                # 找到第一个空字节，截取之前的部分
                null_index = data_bytes.index(b'\x00')
                valid_data = data_bytes[:null_index]
                if R60AFD1.DEBUG_ENABLED:
                    print(f"[Parse] After null removal: {valid_data}, hex: {valid_data.hex()}")
            else:
                valid_data = data_bytes

            # 解码为字符串 - 移除关键字参数
            # MicroPython 的 decode 方法不支持 errors='ignore' 关键字参数
            product_info = valid_data.decode('utf-8').strip()
            if R60AFD1.DEBUG_ENABLED:
                print(f"[Parse] Decoded product info: '{product_info}'")

            return (product_info,)
        except Exception as e:
            # 如果解码失败，尝试其他方式
            if R60AFD1.DEBUG_ENABLED:
                print(f"[Parse] Product info parse error: {e}, data: {data_bytes}")

            # 尝试使用 ascii 解码作为备选方案
            try:
                product_info = valid_data.decode('ascii').strip()
                if R60AFD1.DEBUG_ENABLED:
                    print(f"[Parse] ASCII decoded product info: '{product_info}'")
                return (product_info,)
            except:
                return ("",)
    def update_properties_from_frame(self, frame):

        control = frame['control_byte']
        command = frame['command_byte']
        data = frame['data']

        # 心跳包 (0x01)
        if control == 0x01:
            # 心跳包上报
            if command == 0x01:
                self.heartbeat_last_received = time.ticks_ms()
                if R60AFD1.DEBUG_ENABLED:
                    print("[Heartbeat] Received")
            # 模组复位
            elif command == 0x02:
                self.module_reset_flag = True
                self.module_reset_timestamp = time.ticks_ms()
                self._handle_query_response(
                    R60AFD1.TYPE_MODULE_RESET,
                    True,
                    "Module Reset"
                )

        # 产品信息查询
        elif control == 0x02:
            # 产品型号查询
            if command == 0xA1:
                if data:
                    # 解析产品型号
                    product_model = self._parse_product_info_data(data)[0]
                    # 更新产品型号属性
                    self.product_model = product_model
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_PRODUCT_MODEL,
                        product_model,
                        "PRODUCT MODEL"
                    )
            # 产品ID查询
            elif command == 0xA2:
                if data:
                    # 解析产品ID
                    product_id = self._parse_product_info_data(data)[0]
                    # 更新产品ID属性
                    self.product_id = product_id
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_PRODUCT_ID,
                        product_id,
                        "PRODUCT ID"
                    )
            # 硬件型号查询
            elif command == 0xA3:
                if data:
                    # 解析硬件型号
                    hardware_model = self._parse_product_info_data(data)[0]
                    # 更新硬件型号属性
                    self.hardware_model = hardware_model
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_HARDWARE_MODEL,
                        hardware_model,
                        "HARDWARE MODEL"
                    )
            # 固件版本查询
            elif command == 0xA4:
                if data:
                    # 解析固件版本
                    firmware_version = self._parse_product_info_data(data)[0]
                    # 更新固件版本属性
                    self.firmware_version = firmware_version
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_FIRMWARE_VERSION,
                        firmware_version,
                        "FIRMWARE VERSION"
                    )
        # 工作状态查询
        elif control == 0x05:
            # 初始化完成上报
            if command == 0x01:
                if data and len(data) > 0:
                    self.system_initialized = (data[0] == 0x01)
                    self.system_initialized_timestamp = time.ticks_ms()
                    if R60AFD1.DEBUG_ENABLED:
                        status = "completed" if self.system_initialized else "not completed"
                        print(f"[System] Initialization {status}")
            # 雷达故障上传上报
            elif command == 0x02:
                if data and len(data) >= 1:
                    fault_status = data[0]
                    self.radar_fault_status = fault_status
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[Radar] Fault status: {fault_status}")
            # 工作时长上报
            elif command == 0x03:
                if data and len(data) >= 4:
                    working_time = self._parse_signed_16bit_special(data[0:4])
                    self.working_duration = working_time
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[System] Working duration: {working_time} seconds")
            # 初始化是否完成查询
            elif command == 0x81:
                if data and len(data) >= 1:
                    # 01：已完成 00：未完成
                    system_initialized  = data[0] == 0x01
                    self.system_initialized = system_initialized
                    self.system_initialized_timestamp = time.ticks_ms()
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_INIT_COMPLETE,
                        system_initialized,
                        "INIT COMPLETE"
                    )
            elif command == 0x07:
                if data and len(data) >= 1:
                    scene_info = data[0]
                    self.scene_info = scene_info
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[System] Scene info: {scene_info}")

        # 雷达安装信息
        elif control == 0x06:
            # 安装角度设置
            if command == 0x01:
                if data and len(data) >= 6:
                    x, y, z = self._parse_angle_data(data)
                    self.install_angle_x = x
                    self.install_angle_y = y
                    self.install_angle_z = z
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_INSTALL_ANGLE,
                        [x, y, z],
                        "SET INSTALL ANGLE"
                )
            # 安装高度设置(2B)
            if command == 0x02:
                if data and len(data) >= 2:
                    install_height = self._parse_signed_16bit_special(data[0:2])
                    self.install_height = install_height
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_INSTALL_HEIGHT,
                        install_height,
                        "SET INSTALL HEIGHT"
                    )
            # 安装角度查询
            if command == 0x81:
                if data and len(data) >= 6:
                    x, y, z = self._parse_angle_data(data)
                    self.install_angle_x = x
                    self.install_angle_y = y
                    self.install_angle_z = z
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_INSTALL_ANGLE,
                        [x, y, z],
                        "INSTALL ANGLE"
                    )
            # 安装高度查询
            elif command == 0x82:
                if data and len(data) >= 1:
                    if data and len(data) >= 2:
                        install_height = self._parse_signed_16bit_special(data[0:2])
                        self.install_height = install_height
                        self._handle_query_response(
                            R60AFD1.TYPE_QUERY_INSTALL_HEIGHT,
                            install_height,
                            "INSTALL HEIGHT"
                        )
        # 人体存在功能查询
        elif control == 0x80:
            # 开关人体存在功能
            if command == 0x00:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.presence_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_HUMAN_PRESENCE_ON,
                            switch_status,
                            "Human Presence ON"
                        )
                    else:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_HUMAN_PRESENCE_OFF,
                            switch_status,
                            "Human Presence OFF"
                        )
            # 存在信息主动上报
            if command == 0x01:
                if data and len(data) > 0:
                    self.presence_status = data[0]
                    if R60AFD1.DEBUG_ENABLED:
                        presence_text = "No presence"
                        if self.presence_status:
                            presence_text = "Presence detected"
                        print(f"[Presence] {presence_text}")

            # 运动信息主动上报
            elif command == 0x02:
                if data and len(data) > 0:
                    self.motion_status = data[0]
                    if R60AFD1.DEBUG_ENABLED:
                        motion_text = "No motion"
                        if self.motion_status == 1:
                            motion_text = "Static"
                        elif self.motion_status == 2:
                            motion_text = "Active"
                        print(f"[Motion] {motion_text}")
            # 体动参数上报
            elif command == 0x03:
                if data and len(data) > 0:
                    body_motion_param = data[0]
                    self.movement_parameter = body_motion_param
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[Motion] Movement parameter: {body_motion_param}")
            # 静坐水平距离设置(2B)
            elif command == 0x0D:
                if data and len(data) >= 2:
                    static_distance = self._parse_signed_16bit_special(data[0:2])
                    self.static_distance = static_distance
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_STATIC_DISTANCE,
                        static_distance,
                        "SET STATIC DISTANCE"
                    )
            # 运动水平距离设置(2B)
            elif command == 0x0E:
                if data and len(data) >= 2:
                    motion_distance = self._parse_signed_16bit_special(data[0:2])
                    self.motion_distance = motion_distance
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_MOTION_DISTANCE,
                        motion_distance,
                        "SET MOTION DISTANCE"
                    )
            # 最大能量值上报(4B)
            elif command == 0x10:
                if data and len(data) >= 4:
                    max_energy = self._parse_signed_16bit_special(data[0:4])
                    self.max_energy_value = max_energy
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[Energy] Max energy value: {max_energy}"
                    )
            # 人体存在判断阈值设置
            elif command == 0x11:
                if data and len(data) >= 4:
                    presence_threshold = self._parse_signed_16bit_special(data[0:4])
                    self.presence_threshold = presence_threshold
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_PRESENCE_THRESHOLD,
                        presence_threshold,
                        "SET_PRESENCE_THRESHOLD"
                    )
            # 无人时间设置(4B)
            elif command == 0x12:
                if data and len(data) >= 4:
                    no_person_time = self._parse_signed_16bit_special(data[0:4])
                    self.no_person_timeout = no_person_time
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_NO_PERSON_TIME,
                        no_person_time,
                        "SET NO PERSON TIME"
                    )
            # 最大能量值上报开关
            elif command == 0x13:
                if data and len(data) >= 1:
                    energy_report_switch = (data[0] == 0x01)
                    self.energy_report_enabled = energy_report_switch
                    if energy_report_switch:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_ENERGY_REPORT_ON,
                            energy_report_switch,
                            " ENERGY REPORT ON"
                        )
                    else :
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_ENERGY_REPORT_OFF,
                            energy_report_switch,
                            " ENERGY REPORT OFF"
                        )

            # 人体存在开关查询
            elif command ==0x80:
                if data and len(data) >=1:
                    presence_switch = (data[0]==0x01)
                    self.presence_enabled = presence_switch
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH,
                        presence_switch,
                        "HUMAN PRESENCE SWITCH"
                    )
            # 存在信息查询
            elif command == 0x81:
                if data and len(data) >=1:
                    presence_info = data[0]
                    self.presence_status = presence_info
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_HUMAN_EXISTENCE_INFO,
                        presence_info,
                        "HUMAN EXISTENCE INFO"
                    )
            #运动信息查询
            elif command == 0x82:
                if data and len(data) >=1:
                    motion_info = data[0]
                    self.motion_status = motion_info
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_HUMAN_MOTION_INFO,
                        motion_info,
                        "HUMAN MOTION INFO"
                    )
            # 静坐水平距离查询(2B
            elif command == 0x8D:
                if data and len(data) >= 2:
                    static_distance = self._parse_signed_16bit_special(data[0:2])
                    self.static_distance = static_distance
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_STATIC_DISTANCE,
                        static_distance,
                        "STATIC DISTANCE"
                    )
            # 运动水平距离查询(2B)
            elif command == 0x8E:
                if data and len(data) >= 2:
                    motion_distance = self._parse_signed_16bit_special(data[0:2])
                    self.motion_distance = motion_distance
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_MOTION_DISTANCE,
                        motion_distance,
                        "MOTION DISTANCE"
                    )
            # 最大能量值查询(4B)
            elif command == 0x90:
                if data and len(data) >= 4:
                    max_energy = self._parse_signed_16bit_special(data[0:4])
                    self.max_energy_value = max_energy
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_MAX_ENERGY,
                        max_energy,
                        "MAX ENERGY"
                    )
            # 人体存在判断阈值查询
            elif command == 0x91:
                if data and len(data) >= 4:
                    presence_threshold = self._parse_signed_16bit_special(data[0:4])
                    self.presence_threshold = presence_threshold
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_PRESENCE_THRESHOLD,
                        presence_threshold,
                        "PRESENCE THRESHOLD"
                    )
            # 无人时间查询(4B)
            elif command == 0x92:
                if data and len(data) >= 4:
                    no_person_time = self._parse_signed_16bit_special(data[0:4])
                    self.no_person_timeout = no_person_time
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_NO_PERSON_TIME,
                        no_person_time,
                        "NO PERSON TIME"
                    )
            elif command == 0x93:
                if data and len(data) >= 1:
                    energy_report_switch = (data[0] == 0x01)
                    self.energy_report_enabled = energy_report_switch
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_ENERGY_REPORT_SWITCH,
                        energy_report_switch,
                        "ENERGY REPORT SWITCH"
                    )

        elif control == 0x83:
            # 自动测高
            if command == 0x90:
                if data and len(data) >= 2:
                    auto_height = self._parse_signed_16bit_special(data[0:2])
                    self.auto_height = auto_height
                    self._handle_query_response(
                        R60AFD1.TYPE_AUTO_HEIGHT_MEASURE,
                        auto_height,
                        "AUTO MEASURED HEIGHT"
                    )

            # 高度占比上报
            if command == 0x0E:
                if data and len(data) >= 6:
                    height_total, ratio_0_05, ratio_05_1, ratio_1_15, ratio_15_2 = self._parse_height_data(data)
                    self.height_total_count = height_total
                    self.height_ratio_0_05 = ratio_0_05
                    self.height_ratio_05_1 = ratio_05_1
                    self.height_ratio_1_15 = ratio_1_15
                    self.height_ratio_15_2 = ratio_15_2
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[Height] Total: {height_total}, 0-0.5m: {ratio_0_05}%, 0.5-1m: {ratio_05_1}%, 1-1.5m: {ratio_1_15}%, 1.5-2m: {ratio_15_2}%")

            # 轨迹点
            elif command == 0x12:
                if data and len(data) >= 3:
                    track_x = self._parse_signed_16bit_special(data[0:2])
                    track_y = self._parse_signed_16bit_special(data[2:4])
                    self.track_position_x = track_x
                    self.track_position_y = track_y
                    if R60AFD1.DEBUG_ENABLED:
                        print(f"[Track] Position X: {track_x}, Y: {track_y}")
            # 跌倒灵敏度
            elif command == 0x0D:
                if data and len(data) >= 2:
                    fall_sensitivity = data[0]
                    self.fall_sensitivity = fall_sensitivity
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_FALL_SENSITIVITY,
                        fall_sensitivity,
                        "SET FALL SENSITIVITY"
                    )
            # 轨迹点信息查询X(2B)Y(2B)
            elif command == 0x92:
                if data and len(data) >= 3:
                    track_x = self._parse_signed_16bit_special(data[0:2])
                    track_y = self._parse_signed_16bit_special(data[2:4])
                    self.track_position_x = track_x
                    self.track_position_y = track_y
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_TRACK_POINT,
                        (track_x, track_y),
                        "TRACK POINT"
                    )
            # 轨迹点上报频率查询(4B)
            elif command == 0x93:
                if data and len(data) >= 4:
                    track_frequency = self._parse_signed_16bit_special(data[0:4])
                    self.track_report_frequency = track_frequency
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_TRACK_FREQUENCY,
                        track_frequency,
                        "TRACK FREQUENCY"
                    )
            # 轨迹点上报开关查询(1B)
            elif command == 0x94:
                if data and len(data) >= 1:
                    track_switch = (data[0] == 0x01)
                    self.track_report_enabled = track_switch
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_TRACK_SWITCH,
                        track_switch,
                        "TRACK SWITCH"
                    )
            # 跌倒开关监测功能
            elif command == 0x00:
                if data and len(data) > 0:
                    fall_detection_switch = (data[0] == 0x01)
                    self.fall_detection_enabled = fall_detection_switch
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_FALL_DETECTION_ON,
                            True,
                            "Fall Detection ON"
                        )
                    else:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_FALL_DETECTION_OFF,
                            True,
                            "Fall Detection OFF"
                        )
            # 跌倒状态
            elif command == 0x01:
                if data and len(data) > 0:
                    fall_status = data[0]
                    self.fall_status = fall_status
                    if R60AFD1.DEBUG_ENABLED:
                        status_text = "No fall" if self.fall_status == 0 else "Fall detected"
                        print(f"[Fall Detection] {status_text}")
            # 跌倒时长查询(4B)
            elif command == 0x0C:
                if data and len(data) >= 4:
                    fall_duration = self._parse_signed_16bit_special(data[0:4])
                    self.fall_duration_threshold = fall_duration
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_FALL_DURATION,
                        fall_duration,
                        "FALL DETECTION DURATION"
                    )
            # 静止驻留状态
            elif command == 0x05:
                if data and len(data) >0:
                    stationary_status = data[0]
                    self.static_stay_status = stationary_status
                    if R60AFD1.DEBUG_ENABLED:
                        status_text = "Not stationary" if self.static_stay_status ==0 else "Stationary detected"
                        print(f"[Stationary Detection] {status_text}")
            # 静止驻留时长设置(4B)
            elif command == 0x0A:
                if data and len(data) >=4:
                    stationary_duration = self._parse_signed_16bit_special(data[0:4])
                    self.static_stay_duration = stationary_duration
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_STATIC_STAY_DURATION,
                        stationary_duration,
                        "STATIONARY DURATION"
                    )
            elif command == 0x0B:
                if data and len(data) >= 1:
                    stationary_switch = (data[0] == 0x01)
                    self.static_stay_enabled = stationary_switch
                    if stationary_switch:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_STATIC_STAY_ON,
                            stationary_switch,
                            "STATIC STAY ON"
                    )
                    else:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_STATIC_STAY_OFF,
                            stationary_switch,
                            "STATIC STAY OFF"
                    )
            # 跌倒灵敏度设置
            elif command == 0x0D:
                if data and len(data) >= 2:
                    static_distance = data[0]
                    self.static_distance = static_distance
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_FALL_SENSITIVITY,
                        static_distance,
                        "STATIC DISTANCE"
                    )
            # 高度累积时间设置
            elif command == 0x0F:
                if data and len(data) >= 4:
                    height_accumulation_time = self._parse_signed_16bit_special(data[0:4])
                    self.height_accumulation_time = height_accumulation_time
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_HEIGHT_ACCUMULATION_TIME,
                        height_accumulation_time,
                        "HEIGHT ACCUMULATION TIME"
                    )

            # 跌倒打破高度设置
            elif command == 0x11:
                if data and len(data) >= 2:
                    fall_break_height = self._parse_signed_16bit_special(data[0:2])
                    self.fall_break_height = fall_break_height
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_FALL_BREAK_HEIGHT,
                        fall_break_height,
                        "FALL BREAK HEIGHT"
                    )
            # 高度占比开关设置
            elif command == 0x15:
                if data and len(data) >= 1:
                    height_ratio_switch = (data[0] == 0x01)
                    self.height_ratio_enabled = height_ratio_switch
                    if height_ratio_switch:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_HEIGHT_RATIO_ON,
                            height_ratio_switch,
                         "HEIGHT RATIO ON"
                        )
                    else:
                        self._handle_query_response(
                            R60AFD1.TYPE_CONTROL_HEIGHT_RATIO_OFF,
                            height_ratio_switch,
                            "HEIGHT RATIO OFF"
                        )

            # 轨迹点信息上报频率设置(4B)
            elif command == 0x13:
                if data and len(data) >= 4:
                    track_frequency = self._parse_signed_16bit_special(data[0:4])
                    self.track_report_frequency = track_frequency
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_TRACK_FREQUENCY,
                        track_frequency,
                        "TRACK FREQUENCY"
                    )
            # 轨迹点上报开关设置(1B)
            elif command == 0x14:
                if data and len(data) >= 1:
                    track_switch = (data[0] == 0x01)
                    self.track_report_enabled = track_switch
                    self._handle_query_response(
                        R60AFD1.TYPE_SET_TRACK_SWITCH,
                        track_switch,
                        "TRACK SWITCH"
                    )
            # 查询跌倒监测开关
            elif command == 0x80:
                if data and len(data) >= 1:
                    track_switch = (data[0] == 0x01)
                    self.track_report_enabled = track_switch
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_FALL_DETECTION_SWITCH,
                        track_switch,
                        "FALL DETECTION SWITCH"
                    )
            # 跌倒状态查询
            elif command == 0x81:
                if data and len(data) > 0:
                    fall_status = data[0]
                    self.fall_status = fall_status
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_FALL_STATUS,
                        fall_status,
                        "QUERY_FALL_STATUS"
                    )
            elif command == 0x8C:
                if data and len(data) >= 4:
                    fall_duration = self._parse_signed_16bit_special(data[0:4])
                    self.fall_duration_threshold = fall_duration
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_FALL_DURATION,
                        fall_duration,
                        "QUERY FALL DURATION"
                    )
            # 跌倒打破高度查询
            elif command == 0x91:
                if data and len(data) >= 2:
                    fall_break_height = self._parse_signed_16bit_special(data[0:2])
                    self.fall_break_height = fall_break_height
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_FALL_BREAK_HEIGHT,
                        fall_break_height,
                        "QUERY FALL BREAK HEIGHT"
                    )
            # 高度占比开关查询
            elif command == 0x95:
                if data and len(data) >= 1:
                    height_ratio_switch = (data[0] == 0x01)
                    self.height_ratio_enabled = height_ratio_switch
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_HEIGHT_RATIO_SWITCH,
                        height_ratio_switch,
                        "HEIGHT RATIO SWITCH"
                    )
            # 静止驻留状态查询
            elif command == 0x85:
                if data and len(data) >= 4:
                    height_accumulation_time = self._parse_signed_16bit_special(data[0:4])
                    self.height_accumulation_time = height_accumulation_time
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_STATIC_STAY_STATUS,
                        height_accumulation_time,
                        "QUERY STATIC STAY STATUS"
                    )
            # 静止驻留时长查询(4B)
            elif command == 0x8A:
                if data and len(data) >= 4:
                    stationary_duration = self._parse_signed_16bit_special(data[0:4])
                    self.static_stay_duration = stationary_duration
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_STATIC_STAY_DURATION,
                        stationary_duration,
                        "STATIC STAY DURATION"
                    )
            # 静止驻留开关查询(1B)
            elif command == 0x8B:
                if data and len(data) >= 1:
                    stationary_switch = (data[0] == 0x01)
                    self.static_stay_enabled = stationary_switch
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_STATIC_STAY_SWITCH,
                        stationary_switch,
                        "STATIONARY SWITCH"
                    )
            # 跌倒灵敏度查询(1B)
            elif command == 0x8D:
                if data and len(data) >= 1:
                    static_distance = data[0]
                    self.static_distance = static_distance
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_FALL_SENSITIVITY,
                        static_distance,
                        "QUERY FALL SENSITIVITY"
                    )
            # 一段时间高度占比查询(6B)
            elif command == 0x0E:
                    if data and len(data) >= 6:
                        height_total, ratio_0_05, ratio_05_1, ratio_1_15, ratio_15_2 = self._parse_height_data(data)
                        self.height_total_count = height_total
                        self.height_ratio_0_05 = ratio_0_05
                        self.height_ratio_05_1 = ratio_05_1
                        self.height_ratio_1_15 = ratio_1_15
                        self.height_ratio_15_2 = ratio_15_2
                        self._handle_query_response(
                            R60AFD1.TYPE_QUERY_HEIGHT_RATIO,
                            (height_total, ratio_0_05, ratio_05_1, ratio_1_15, ratio_15_2),
                            "HEIGHT RATIO"
                        )
            # 高度累计时间查询(4B)
            elif command == 0x8F:
                if data and len(data) >= 4:
                    height_accumulation_time = self._parse_signed_16bit_special(data[0:4])
                    self.height_accumulation_time = height_accumulation_time
                    self._handle_query_response(
                        R60AFD1.TYPE_QUERY_HEIGHT_ACCUMULATION_TIME,
                        height_accumulation_time,
                        "HEIGHT ACCUMULATION TIME"
                    )

# ============================ 系统基础查询指令 ============================
    def reset_module(self, timeout=200):
        """模组复位"""
        return self._execute_operation(R60AFD1.TYPE_MODULE_RESET, timeout=timeout)


    def query_product_model(self, timeout=200):
        """查询产品型号"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_PRODUCT_MODEL, timeout=timeout)


    def query_product_id(self, timeout=200):
        """查询产品ID"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_PRODUCT_ID, timeout=timeout)


    def query_hardware_model(self, timeout=200):
        """查询硬件型号"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_HARDWARE_MODEL, timeout=timeout)


    def query_firmware_version(self, timeout=200):
        """查询固件版本"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_FIRMWARE_VERSION, timeout=timeout)


    def query_init_complete(self, timeout=200):
        """查询初始化是否完成"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_INIT_COMPLETE, timeout=timeout)

    def query_scene_info(self, timeout=200):
        """查询场景信息"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_SCENE_INFO, timeout=timeout)


    # ============================ 安装参数查询指令 ============================

    def query_install_angle(self, timeout=200):
        """查询安装角度"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_INSTALL_ANGLE, timeout=timeout)



    def query_install_height(self, timeout=200):
        """查询安装高度"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_INSTALL_HEIGHT, timeout=timeout)


    def auto_measure_height(self, timeout=500):
        """自动测高（注意：容易受干扰导致测不准）"""
        return self._execute_operation(R60AFD1.TYPE_AUTO_HEIGHT_MEASURE, timeout=timeout)


    # ============================ 人体存在功能查询指令 ============================

    def query_presence_switch(self, timeout=200):
        """查询人体存在开关状态"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH, timeout=timeout)


    def query_presence_status(self, timeout=200):
        """查询存在信息（有人/无人）"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_HUMAN_EXISTENCE_INFO, timeout=timeout)


    def query_motion_status(self, timeout=200):
        """查询运动信息（静止/活跃）"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_HUMAN_MOTION_INFO, timeout=timeout)


    def query_body_motion_param(self, timeout=200):
        """查询体动参数（0-100）"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_BODY_MOTION_PARAM, timeout=timeout)


    def query_height_ratio(self, timeout=200):
        """查询高度占比"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_HEIGHT_RATIO, timeout=timeout)


    def query_track_point(self, timeout=200):
        """查询轨迹点信息"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_TRACK_POINT, timeout=timeout)


    def query_track_frequency(self, timeout=200):
        """查询轨迹点上报频率"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_TRACK_FREQUENCY, timeout=timeout)


    def query_track_switch(self, timeout=200):
        """查询轨迹点上报开关"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_TRACK_SWITCH, timeout=timeout)


    def query_static_distance(self, timeout=200):
        """查询静坐水平距离"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_STATIC_DISTANCE, timeout=timeout)


    def query_motion_distance(self, timeout=200):
        """查询运动水平距离"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_MOTION_DISTANCE, timeout=timeout)


    def query_no_person_time(self, timeout=200):
        """查询无人时间设置"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_NO_PERSON_TIME, timeout=timeout)


    def query_presence_threshold(self, timeout=200):
        """查询人体存在判断阈值"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_PRESENCE_THRESHOLD, timeout=timeout)


    def query_energy_report_switch(self, timeout=200):
        """查询最大能量值上报开关"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_ENERGY_REPORT_SWITCH, timeout=timeout)


    def query_max_energy(self, timeout=200):
        """查询最大能量值"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_MAX_ENERGY, timeout=timeout)


    # ============================ 跌倒检测功能查询指令 ============================

    def query_fall_detection_switch(self, timeout=200):
        """查询跌倒监测开关"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_FALL_DETECTION_SWITCH, timeout=timeout)


    def query_fall_status(self, timeout=200):
        """查询跌倒状态"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_FALL_STATUS, timeout=timeout)


    def query_fall_duration(self, timeout=200):
        """查询跌倒时长设置"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_FALL_DURATION, timeout=timeout)


    def query_static_stay_duration(self, timeout=200):
        """查询驻留时长设置"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_STATIC_STAY_DURATION, timeout=timeout)


    def query_static_stay_switch(self, timeout=200):
        """查询静止驻留开关"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_STATIC_STAY_SWITCH, timeout=timeout)


    def query_static_stay_status(self, timeout=200):
        """查询静止驻留状态"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_STATIC_STAY_STATUS, timeout=timeout)


    def query_height_accumulation_time(self, timeout=200):
        """查询高度累积时间"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_HEIGHT_ACCUMULATION_TIME, timeout=timeout)


    def query_fall_break_height(self, timeout=200):
        """查询跌倒打破高度"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_FALL_BREAK_HEIGHT, timeout=timeout)


    def query_height_ratio_switch(self, timeout=200):
        """查询高度占比开关"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_HEIGHT_RATIO_SWITCH, timeout=timeout)


    def query_fall_sensitivity(self, timeout=200):
        """查询跌倒灵敏度"""
        return self._execute_operation(R60AFD1.TYPE_QUERY_FALL_SENSITIVITY, timeout=timeout)


    # ============================ 控制指令方法 ============================

    def set_presence_switch(self, enabled=True, timeout=200):
        """设置人体存在开关"""
        command_type = R60AFD1.TYPE_CONTROL_HUMAN_PRESENCE_ON if enabled else R60AFD1.TYPE_CONTROL_HUMAN_PRESENCE_OFF
        return self._execute_operation(command_type, timeout=timeout)


    def set_fall_detection_switch(self, enabled=True, timeout=200):
        """设置跌倒监测开关"""
        command_type = R60AFD1.TYPE_CONTROL_FALL_DETECTION_ON if enabled else R60AFD1.TYPE_CONTROL_FALL_DETECTION_OFF
        return self._execute_operation(command_type, timeout=timeout)


    def set_static_stay_switch(self, enabled=True, timeout=200):
        """设置静止驻留开关"""
        command_type = R60AFD1.TYPE_CONTROL_STATIC_STAY_ON if enabled else R60AFD1.TYPE_CONTROL_STATIC_STAY_OFF
        return self._execute_operation(command_type, timeout=timeout)


    def set_energy_report_switch(self, enabled=True, timeout=200):
        """设置能量值上报开关"""
        command_type = R60AFD1.TYPE_CONTROL_ENERGY_REPORT_ON if enabled else R60AFD1.TYPE_CONTROL_ENERGY_REPORT_OFF
        return self._execute_operation(command_type, timeout=timeout)


    def set_height_ratio_switch(self, enabled=True, timeout=200):
        """设置高度占比开关"""
        command_type = R60AFD1.TYPE_CONTROL_HEIGHT_RATIO_ON if enabled else R60AFD1.TYPE_CONTROL_HEIGHT_RATIO_OFF
        return self._execute_operation(command_type, timeout=timeout)


    def set_track_switch(self, enabled=True, timeout=200):
        """设置轨迹点上报开关（需要传入动态数据）"""
        data = bytes([0x01 if enabled else 0x00])
        return self._execute_operation(R60AFD1.TYPE_SET_TRACK_SWITCH, timeout=timeout, data=data)


    # ============================ 参数设置指令方法 ============================

    def set_install_angle(self, angle_x, angle_y, angle_z, timeout=200):
        """设置安装角度"""
        # 角度数据为2字节每个轴，共6字节
        data = angle_x.to_bytes(2) + angle_y.to_bytes(2) + angle_z.to_bytes(2)
        return self._execute_operation(R60AFD1.TYPE_SET_INSTALL_ANGLE, timeout=timeout, data=data)


    def set_install_height(self, height_cm, timeout=200):
        """设置安装高度（单位：cm）"""
        if height_cm < 0 or height_cm > 65535:
            raise ValueError("高度必须在0-65535cm范围内")
        data = height_cm.to_bytes(2)
        return self._execute_operation(R60AFD1.TYPE_SET_INSTALL_HEIGHT, timeout=timeout, data=data)


    def set_static_distance(self, distance_cm, timeout=200):
        """设置静坐水平距离（单位：cm，范围0-300）"""
        if distance_cm < 0 or distance_cm > 300:
            raise ValueError("静坐水平距离必须在0-300cm范围内")
        data = distance_cm.to_bytes(2)
        return self._execute_operation(R60AFD1.TYPE_SET_STATIC_DISTANCE, timeout=timeout, data=data)


    def set_motion_distance(self, distance_cm, timeout=200):
        """设置运动水平距离（单位：cm，范围0-300）"""
        if distance_cm < 0 or distance_cm > 300:
            raise ValueError("运动水平距离必须在0-300cm范围内")
        data = distance_cm.to_bytes(2)
        return self._execute_operation(R60AFD1.TYPE_SET_MOTION_DISTANCE, timeout=timeout, data=data)


    def set_no_person_time(self, seconds, timeout=200):
        """设置无人时间（单位：秒，范围5-1800）"""
        if seconds < 5 or seconds > 1800:
            raise ValueError("无人时间必须在5-1800秒范围内")
        data = seconds.to_bytes(4)
        return self._execute_operation(R60AFD1.TYPE_SET_NO_PERSON_TIME, timeout=timeout, data=data)


    def set_presence_threshold(self, threshold, timeout=200):
        """设置人体存在判断阈值（范围0-0xffffffff）"""
        if threshold < 0 or threshold > 0xffffffff:
            raise ValueError("阈值必须在0-0xffffffff范围内")
        data = threshold.to_bytes(4)
        return self._execute_operation(R60AFD1.TYPE_SET_PRESENCE_THRESHOLD, timeout=timeout, data=data)


    def set_fall_duration(self, seconds, timeout=200):
        """设置跌倒时长（单位：秒，范围5-180）"""
        if seconds < 5 or seconds > 180:
            raise ValueError("跌倒时长必须在5-180秒范围内")
        data = seconds.to_bytes(4)
        return self._execute_operation(R60AFD1.TYPE_SET_FALL_DURATION, timeout=timeout, data=data)


    def set_static_stay_duration(self, seconds, timeout=200):
        """设置静止驻留时长（单位：秒，范围60-3600）"""
        if seconds < 60 or seconds > 3600:
            raise ValueError("静止驻留时长必须在60-3600秒范围内")
        data = seconds.to_bytes(4)
        return self._execute_operation(R60AFD1.TYPE_SET_STATIC_STAY_DURATION, timeout=timeout, data=data)


    def set_height_accumulation_time(self, seconds, timeout=200):
        """设置高度累积时间（单位：秒，范围0-300）"""
        if seconds < 0 or seconds > 300:
            raise ValueError("高度累积时间必须在0-300秒范围内")
        data = seconds.to_bytes(4)
        return self._execute_operation(R60AFD1.TYPE_SET_HEIGHT_ACCUMULATION_TIME, timeout=timeout, data=data)


    def set_fall_break_height(self, height_cm, timeout=200):
        """设置跌倒打破高度（单位：cm，范围0-150）"""
        if height_cm < 0 or height_cm > 150:
            raise ValueError("跌倒打破高度必须在0-150cm范围内")
        data = height_cm.to_bytes(2)
        return self._execute_operation(R60AFD1.TYPE_SET_FALL_BREAK_HEIGHT, timeout=timeout, data=data)


    def set_track_frequency(self, seconds, timeout=200):
        """设置轨迹点上报频率（单位：秒，范围0-0xffffffff）"""
        if seconds < 0 or seconds > 0xffffffff:
            raise ValueError("轨迹点上报频率超出范围")
        data = seconds.to_bytes(4)
        return self._execute_operation(R60AFD1.TYPE_SET_TRACK_FREQUENCY, timeout=timeout, data=data)

    def set_fall_sensitivity(self, sensitivity, timeout=200):
        """设置跌倒灵敏度（范围1-5）"""
        if sensitivity < 0 or sensitivity > 3:
            raise ValueError("跌倒灵敏度必须在1-5范围内")
        data = bytes([sensitivity])
        return self._execute_operation(R60AFD1.TYPE_SET_FALL_SENSITIVITY, timeout=timeout, data=data)
# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================