# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-        
# @Time    : 2025/11/4 下午5:35   
# @Author  : 李清水            
# @File    : r60abd1.py       
# @Description : R60ABD1雷达设备业务处理类相关代码
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

    当R60ABD1设备初始化过程中发生严重错误时抛出。

    ==========================================

    Device initialization error exception class.

    Raised when critical errors occur during R60ABD1 device initialization.
    """
    pass

class R60ABD1:
    """
    R60ABD1雷达设备业务处理类。

    该类负责与R60ABD1雷达设备进行通信，管理设备状态，处理数据解析和业务逻辑。
    支持人体存在检测、心率监测、呼吸监测、睡眠监测等多种功能。

    Attributes:
        DEBUG_ENABLED (bool): 调试模式开关。
        data_processor (DataFlowProcessor): 数据流处理器实例。
        parse_interval (int): 数据解析间隔（毫秒）。
        max_retries (int): 最大重试次数。
        retry_delay (int): 重试延迟时间（毫秒）。
        init_timeout (int): 初始化超时时间（毫秒）。
        _is_running (bool): 设备运行状态标志。
        _initialization_complete (bool): 初始化完成标志。
        _configuration_errors (list): 配置错误列表。

    Methods:
        __init__(): 初始化R60ABD1实例。
        _validate_init_parameters(): 验证初始化参数。
        _complete_initialization(): 执行完整的初始化流程。
        _load_device_information(): 加载设备基本信息。
        _wait_for_device_initialization(): 等待设备初始化完成。
        _reset_and_wait_for_initialization(): 重置设备并等待初始化完成。
        _auto_configure_device(): 自动配置设备功能。
        _verify_critical_configuration(): 验证关键配置。
        _execute_with_retry(): 带重试的执行操作。
        get_configuration_status(): 获取设备配置状态。
        _start_timer(): 启动定时器。
        _timer_callback(): 定时器回调函数。
        _parse_human_position_data(): 解析人体方位数据。
        _parse_signed_16bit_special(): 解析有符号16位数据。
        _parse_heart_rate_waveform_data(): 解析心率波形数据。
        _parse_sleep_comprehensive_data(): 解析睡眠综合状态数据。
        _parse_sleep_statistics_data(): 解析睡眠统计信息数据。
        _parse_breath_waveform_data(): 解析呼吸波形数据。
        _parse_product_info_data(): 解析产品信息数据。
        _parse_firmware_version_data(): 解析固件版本数据。
        _execute_operation(): 执行操作（查询或设置）的统一方法。
        query_heartbeat(): 查询心跳包。
        reset_module(): 模组复位。
        query_product_model(): 查询产品型号。
        query_product_id(): 查询产品ID。
        query_hardware_model(): 查询硬件型号。
        query_firmware_version(): 查询固件版本。
        query_init_complete(): 查询初始化是否完成。
        query_radar_range_boundary(): 查询雷达探测范围越界状态。
        enable_human_presence(): 打开人体存在功能。
        disable_human_presence(): 关闭人体存在功能。
        query_human_presence_switch(): 查询人体存在开关状态。
        query_presence_status(): 查询存在信息状态。
        query_human_motion_info(): 查询运动信息。
        query_human_body_motion_param(): 查询体动参数。
        query_human_distance(): 查询人体距离。
        query_human_direction(): 查询人体方位。
        enable_heart_rate_monitor(): 打开心率监测功能。
        disable_heart_rate_monitor(): 关闭心率监测功能。
        query_heart_rate_monitor_switch(): 查询心率监测开关状态。
        enable_heart_rate_waveform_report(): 打开心率波形上报开关。
        disable_heart_rate_waveform_report(): 关闭心率波形上报开关。
        query_heart_rate_waveform_report_switch(): 查询心率波形上报开关状态。
        query_heart_rate_value(): 查询心率数值。
        query_heart_rate_waveform(): 查询心率波形。
        enable_breath_monitor(): 打开呼吸监测功能。
        disable_breath_monitor(): 关闭呼吸监测功能。
        query_breath_monitor_switch(): 查询呼吸监测开关状态。
        set_low_breath_threshold(): 设置低缓呼吸判读阈值。
        query_low_breath_threshold(): 查询低缓呼吸判读阈值。
        query_breath_info(): 查询呼吸信息。
        query_breath_value(): 查询呼吸数值。
        enable_breath_waveform_report(): 打开呼吸波形上报开关。
        disable_breath_waveform_report(): 关闭呼吸波形上报开关。
        query_breath_waveform_report_switch(): 查询呼吸波形上报开关状态。
        query_breath_waveform(): 查询呼吸波形。
        enable_sleep_monitor(): 打开睡眠监测功能。
        disable_sleep_monitor(): 关闭睡眠监测功能。
        query_sleep_monitor_switch(): 查询睡眠监测开关状态。
        enable_abnormal_struggle_monitor(): 打开异常挣扎状态监测。
        disable_abnormal_struggle_monitor(): 关闭异常挣扎状态监测。
        query_abnormal_struggle_switch(): 查询异常挣扎状态开关。
        query_abnormal_struggle_status(): 查询异常挣扎状态。
        set_struggle_sensitivity(): 设置挣扎状态判读灵敏度。
        query_struggle_sensitivity(): 查询挣扎状态判读灵敏度。
        enable_no_person_timing(): 打开无人计时功能。
        disable_no_person_timing(): 关闭无人计时功能。
        query_no_person_timing_switch(): 查询无人计时功能开关。
        set_no_person_timing_duration(): 设置无人计时时长。
        query_no_person_timing_duration(): 查询无人计时时长。
        set_sleep_end_duration(): 设置睡眠截止时长。
        query_sleep_end_duration(): 查询睡眠截止时长。
        query_no_person_timing_status(): 查询无人计时状态。
        query_bed_status(): 查询入床/离床状态。
        query_sleep_status(): 查询睡眠状态。
        query_awake_duration(): 查询清醒时长。
        query_light_sleep_duration(): 查询浅睡时长。
        query_deep_sleep_duration(): 查询深睡时长。
        query_sleep_quality_score(): 查询睡眠质量评分。
        query_sleep_comprehensive_status(): 查询睡眠综合状态。
        query_sleep_anomaly(): 查询睡眠异常。
        query_sleep_statistics(): 查询睡眠统计。
        query_sleep_quality_level(): 查询睡眠质量评级。
        _handle_query_response(): 统一处理查询响应。
        _update_property_with_debug(): 更新属性并输出调试信息。
        update_properties_from_frame(): 根据解析的帧更新属性值。
        close(): 停止定时器，解析剩余数据帧，输出统计信息。

    ==========================================

    R60ABD1 radar device business processing class.

    This class handles communication with R60ABD1 radar device, manages device status,
    processes data parsing and business logic. Supports various functions including
    human presence detection, heart rate monitoring, breath monitoring, sleep monitoring, etc.

    Attributes:
        DEBUG_ENABLED (bool): Debug mode switch.
        data_processor (DataFlowProcessor): Data flow processor instance.
        parse_interval (int): Data parsing interval (milliseconds).
        max_retries (int): Maximum retry count.
        retry_delay (int): Retry delay time (milliseconds).
        init_timeout (int): Initialization timeout (milliseconds).
        _is_running (bool): Device running status flag.
        _initialization_complete (bool): Initialization completion flag.
        _configuration_errors (list): Configuration errors list.

    Methods:
        __init__(): Initialize R60ABD1 instance.
        _validate_init_parameters(): Validate initialization parameters.
        _complete_initialization(): Execute complete initialization process.
        _load_device_information(): Load device basic information.
        _wait_for_device_initialization(): Wait for device initialization completion.
        _reset_and_wait_for_initialization(): Reset device and wait for initialization.
        _auto_configure_device(): Auto-configure device functions.
        _verify_critical_configuration(): Verify critical configuration.
        _execute_with_retry(): Execute operation with retry.
        get_configuration_status(): Get device configuration status.
        _start_timer(): Start timer.
        _timer_callback(): Timer callback function.
        _parse_human_position_data(): Parse human position data.
        _parse_signed_16bit_special(): Parse signed 16-bit data.
        _parse_heart_rate_waveform_data(): Parse heart rate waveform data.
        _parse_sleep_comprehensive_data(): Parse sleep comprehensive status data.
        _parse_sleep_statistics_data(): Parse sleep statistics data.
        _parse_breath_waveform_data(): Parse breath waveform data.
        _parse_product_info_data(): Parse product information data.
        _parse_firmware_version_data(): Parse firmware version data.
        _execute_operation(): Unified method for executing operations (query or set).
        query_heartbeat(): Query heartbeat packet.
        reset_module(): Module reset.
        query_product_model(): Query product model.
        query_product_id(): Query product ID.
        query_hardware_model(): Query hardware model.
        query_firmware_version(): Query firmware version.
        query_init_complete(): Query if initialization is complete.
        query_radar_range_boundary(): Query radar detection range boundary status.
        enable_human_presence(): Enable human presence detection.
        disable_human_presence(): Disable human presence detection.
        query_human_presence_switch(): Query human presence switch status.
        query_presence_status(): Query presence status information.
        query_human_motion_info(): Query human motion information.
        query_human_body_motion_param(): Query human body motion parameters.
        query_human_distance(): Query human distance.
        query_human_direction(): Query human direction.
        enable_heart_rate_monitor(): Enable heart rate monitoring.
        disable_heart_rate_monitor(): Disable heart rate monitoring.
        query_heart_rate_monitor_switch(): Query heart rate monitor switch status.
        enable_heart_rate_waveform_report(): Enable heart rate waveform reporting.
        disable_heart_rate_waveform_report(): Disable heart rate waveform reporting.
        query_heart_rate_waveform_report_switch(): Query heart rate waveform report switch status.
        query_heart_rate_value(): Query heart rate value.
        query_heart_rate_waveform(): Query heart rate waveform.
        enable_breath_monitor(): Enable breath monitoring.
        disable_breath_monitor(): Disable breath monitoring.
        query_breath_monitor_switch(): Query breath monitor switch status.
        set_low_breath_threshold(): Set low breath threshold.
        query_low_breath_threshold(): Query low breath threshold.
        query_breath_info(): Query breath information.
        query_breath_value(): Query breath value.
        enable_breath_waveform_report(): Enable breath waveform reporting.
        disable_breath_waveform_report(): Disable breath waveform reporting.
        query_breath_waveform_report_switch(): Query breath waveform report switch status.
        query_breath_waveform(): Query breath waveform.
        enable_sleep_monitor(): Enable sleep monitoring.
        disable_sleep_monitor(): Disable sleep monitoring.
        query_sleep_monitor_switch(): Query sleep monitor switch status.
        enable_abnormal_struggle_monitor(): Enable abnormal struggle monitoring.
        disable_abnormal_struggle_monitor(): Disable abnormal struggle monitoring.
        query_abnormal_struggle_switch(): Query abnormal struggle switch status.
        query_abnormal_struggle_status(): Query abnormal struggle status.
        set_struggle_sensitivity(): Set struggle sensitivity.
        query_struggle_sensitivity(): Query struggle sensitivity.
        enable_no_person_timing(): Enable no person timing.
        disable_no_person_timing(): Disable no person timing.
        query_no_person_timing_switch(): Query no person timing switch status.
        set_no_person_timing_duration(): Set no person timing duration.
        query_no_person_timing_duration(): Query no person timing duration.
        set_sleep_end_duration(): Set sleep end duration.
        query_sleep_end_duration(): Query sleep end duration.
        query_no_person_timing_status(): Query no person timing status.
        query_bed_status(): Query bed status (enter/leave).
        query_sleep_status(): Query sleep status.
        query_awake_duration(): Query awake duration.
        query_light_sleep_duration(): Query light sleep duration.
        query_deep_sleep_duration(): Query deep sleep duration.
        query_sleep_quality_score(): Query sleep quality score.
        query_sleep_comprehensive_status(): Query sleep comprehensive status.
        query_sleep_anomaly(): Query sleep anomaly.
        query_sleep_statistics(): Query sleep statistics.
        query_sleep_quality_level(): Query sleep quality level.
        _handle_query_response(): Unified query response handling.
        _update_property_with_debug(): Update property with debug output.
        update_properties_from_frame(): Update properties from parsed frame.
        close(): Stop timer, parse remaining data frames, output statistics.
    """

    # 是否启用调试
    DEBUG_ENABLED = False

    # R60ABD1雷达设备业务处理类中各种状态值和配置选项的常量
    # 运动信息状态
    MOTION_NONE, MOTION_STATIC, MOTION_ACTIVE = (0x00, 0x01, 0x02)
    # 呼吸信息状态
    BREATH_NORMAL, BREATH_HIGH, BREATH_LOW, BREATH_NONE = (0x01, 0x02, 0x03, 0x04)
    # 床状态
    BED_LEAVE, BED_ENTER, BED_NONE = (0x00, 0x01, 0x02)
    # 睡眠状态
    SLEEP_DEEP, SLEEP_LIGHT, SLEEP_AWAKE, SLEEP_NONE = (0x00, 0x01, 0x02, 0x03)
    # 睡眠异常信息
    SLEEP_ANOMALY_NONE, SLEEP_ANOMALY_SHORT, SLEEP_ANOMALY_LONG, SLEEP_ANOMALY_NO_PERSON = (0x03, 0x00, 0x01, 0x02)
    # 睡眠质量级别
    SLEEP_QUALITY_NONE, SLEEP_QUALITY_GOOD, SLEEP_QUALITY_NORMAL, SLEEP_QUALITY_POOR = (0x00, 0x01, 0x02, 0x03)
    # 异常挣扎状态
    STRUGGLE_NONE, STRUGGLE_NORMAL, STRUGGLE_ABNORMAL = (0x00, 0x01, 0x02)
    # 无人计时状态
    NO_PERSON_TIMING_NONE, NO_PERSON_TIMING_NORMAL, NO_PERSON_TIMING_ABNORMAL = (0x00, 0x01, 0x02)
    # 挣扎状态判读灵敏度
    SENSITIVITY_LOW, SENSITIVITY_MEDIUM, SENSITIVITY_HIGH = (0x00, 0x01, 0x02)

    # R60ABD1雷达设备指令类型常量，用于标识不同的查询和控制操作
    # 基础指令信息查询和设置类型
    # 心跳包查询
    TYPE_QUERY_HEARTBEAT = 0
    # 模组复位指令
    TYPE_MODULE_RESET = 1
    # 产品型号查询
    TYPE_QUERY_PRODUCT_MODEL = 2
    # 产品 ID 查询
    TYPE_QUERY_PRODUCT_ID = 3
    # 硬件型号查询
    TYPE_QUERY_HARDWARE_MODEL = 4
    # 固件版本查询
    TYPE_QUERY_FIRMWARE_VERSION = 5
    # 初始化是否完成查询
    TYPE_QUERY_INIT_COMPLETE = 6
    # 雷达探测范围越界状态查询
    TYPE_QUERY_RADAR_RANGE_BOUNDARY = 7

    # 人体存在指令信息查询和设置类型
    # 打开人体存在功能
    TYPE_CONTROL_HUMAN_PRESENCE_ON = 8
    # 关闭人体存在功能
    TYPE_CONTROL_HUMAN_PRESENCE_OFF = 9
    # 查询人体存在开关状态
    TYPE_QUERY_HUMAN_PRESENCE_SWITCH = 10
    # 存在信息查询
    TYPE_QUERY_HUMAN_EXISTENCE_INFO = 11
    # 运动信息查询
    TYPE_QUERY_HUMAN_MOTION_INFO = 12
    # 体动参数查询
    TYPE_QUERY_HUMAN_BODY_MOTION_PARAM = 13
    # 人体距离查询
    TYPE_QUERY_HUMAN_DISTANCE = 14
    # 人体方位查询
    TYPE_QUERY_HUMAN_DIRECTION = 15

    # 心率监测指令信息查询和设置类型
    # 打开心率监测功能
    TYPE_CONTROL_HEART_RATE_MONITOR_ON = 16
    # 关闭心率监测功能
    TYPE_CONTROL_HEART_RATE_MONITOR_OFF = 17
    # 查询心率监测开关状态
    TYPE_QUERY_HEART_RATE_MONITOR_SWITCH = 18
    # 打开心率波形上报开关
    TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_ON = 19
    # 关闭心率波形上报开关
    TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_OFF = 20
    # 查询心率波形上报开关状态
    TYPE_QUERY_HEART_RATE_WAVEFORM_REPORT_SWITCH = 21
    # 心率数值查询
    TYPE_QUERY_HEART_RATE_VALUE = 22
    # 心率波形查询
    TYPE_QUERY_HEART_RATE_WAVEFORM = 23

    # 呼吸监测指令信息查询和设置类型
    # 打开呼吸监测功能
    TYPE_CONTROL_BREATH_MONITOR_ON = 24
    # 关闭呼吸监测功能
    TYPE_CONTROL_BREATH_MONITOR_OFF = 25
    # 查询呼吸监测开关状态
    TYPE_QUERY_BREATH_MONITOR_SWITCH = 26
    # 设置低缓呼吸判读阈值
    TYPE_SET_LOW_BREATH_THRESHOLD = 27
    # 查询低缓呼吸判读阈值
    TYPE_QUERY_LOW_BREATH_THRESHOLD = 28
    # 呼吸信息查询
    TYPE_QUERY_BREATH_INFO = 29
    # 呼吸数值查询
    TYPE_QUERY_BREATH_VALUE = 30
    # 打开呼吸波形上报开关
    TYPE_CONTROL_BREATH_WAVEFORM_REPORT_ON = 31
    # 关闭呼吸波形上报开关
    TYPE_CONTROL_BREATH_WAVEFORM_REPORT_OFF = 32
    # 查询呼吸波形上报开关状态
    TYPE_QUERY_BREATH_WAVEFORM_REPORT_SWITCH = 33
    # 呼吸波形查询
    TYPE_QUERY_BREATH_WAVEFORM = 34

    # 睡眠监测指令信息查询和设置类型
    # 打开睡眠监测功能
    TYPE_CONTROL_SLEEP_MONITOR_ON = 35
    # 关闭睡眠监测功能
    TYPE_CONTROL_SLEEP_MONITOR_OFF = 36
    # 查询睡眠监测开关状态
    TYPE_QUERY_SLEEP_MONITOR_SWITCH = 37
    # 打开异常挣扎状态监测
    TYPE_CONTROL_ABNORMAL_STRUGGLE_ON = 38
    # 关闭异常挣扎状态监测
    TYPE_CONTROL_ABNORMAL_STRUGGLE_OFF = 39
    # 查询异常挣扎状态开关
    TYPE_QUERY_ABNORMAL_STRUGGLE_SWITCH = 40
    # 查询异常挣扎状态
    TYPE_QUERY_ABNORMAL_STRUGGLE_STATUS = 41
    # 设置挣扎状态判读灵敏度
    TYPE_SET_STRUGGLE_SENSITIVITY = 42
    # 查询挣扎状态判读灵敏度
    TYPE_QUERY_STRUGGLE_SENSITIVITY = 43
    # 打开无人计时功能
    TYPE_CONTROL_NO_PERSON_TIMING_ON = 44
    # 关闭无人计时功能
    TYPE_CONTROL_NO_PERSON_TIMING_OFF = 45
    # 查询无人计时功能开关
    TYPE_QUERY_NO_PERSON_TIMING_SWITCH = 46
    # 设置无人计时时长
    TYPE_SET_NO_PERSON_TIMING_DURATION = 47
    # 查询无人计时时长
    TYPE_QUERY_NO_PERSON_TIMING_DURATION = 48
    # 无人计时状态查询
    TYPE_QUERY_NO_PERSON_TIMING_STATUS = 61
    # 设置睡眠截止时长
    TYPE_SET_SLEEP_END_DURATION = 49
    # 查询睡眠截止时长
    TYPE_QUERY_SLEEP_END_DURATION = 50
    # 入床/离床状态查询
    TYPE_QUERY_BED_STATUS = 51
    # 睡眠状态查询
    TYPE_QUERY_SLEEP_STATUS = 52
    # 清醒时长查询
    TYPE_QUERY_AWAKE_DURATION = 53
    # 浅睡时长查询
    TYPE_QUERY_LIGHT_SLEEP_DURATION = 54
    # 深睡时长查询
    TYPE_QUERY_DEEP_SLEEP_DURATION = 55
    # 睡眠质量评分查询
    TYPE_QUERY_SLEEP_QUALITY_SCORE = 56
    # 睡眠综合状态查询
    TYPE_QUERY_SLEEP_COMPREHENSIVE_STATUS = 57
    # 睡眠异常查询
    TYPE_QUERY_SLEEP_ANOMALY = 58
    # 睡眠统计查询
    TYPE_QUERY_SLEEP_STATISTICS = 59
    # 睡眠质量评级查询
    TYPE_QUERY_SLEEP_QUALITY_LEVEL = 60

    # 指令映射表 - 将查询、开关、设置类型指令的命令字和控制字的具体值映射到帧参数
    COMMAND_MAP = {
        # 基础指令信息查询和设置类型
        TYPE_QUERY_HEARTBEAT: {
            'control_byte': 0x01,  # 系统指令
            'command_byte': 0x80,  # 心跳包查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_MODULE_RESET: {
            'control_byte': 0x01,  # 系统指令
            'command_byte': 0x02,  # 模组复位
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_PRODUCT_MODEL: {
            'control_byte': 0x02,  # 产品信息
            'command_byte': 0xA1,  # 产品型号查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_PRODUCT_ID: {
            'control_byte': 0x02,  # 产品信息
            'command_byte': 0xA2,  # 产品ID查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HARDWARE_MODEL: {
            'control_byte': 0x02,  # 产品信息
            'command_byte': 0xA3,  # 硬件型号查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_FIRMWARE_VERSION: {
            'control_byte': 0x02,  # 产品信息
            'command_byte': 0xA4,  # 固件版本查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_INIT_COMPLETE: {
            'control_byte': 0x05,  # 系统初始化状态
            'command_byte': 0x81,  # 初始化完成查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_RADAR_RANGE_BOUNDARY: {
            'control_byte': 0x07,  # 雷达探测范围
            'command_byte': 0x87,  # 范围越界状态查询
            'data': bytes([0x0F])  # 固定数据
        },

        # 人体存在指令信息查询和设置类型
        TYPE_CONTROL_HUMAN_PRESENCE_ON: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x00,  # 打开人体存在功能
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_HUMAN_PRESENCE_OFF: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x00,  # 关闭人体存在功能
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_HUMAN_PRESENCE_SWITCH: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x80,  # 查询人体存在开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HUMAN_EXISTENCE_INFO: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x81,  # 存在信息查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HUMAN_MOTION_INFO: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x82,  # 运动信息查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HUMAN_BODY_MOTION_PARAM: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x83,  # 体动参数查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HUMAN_DISTANCE: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x84,  # 人体距离查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HUMAN_DIRECTION: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x85,  # 人体方位查询
            'data': bytes([0x0F])  # 固定数据
        },

        # 心率监测指令信息查询和设置类型
        TYPE_CONTROL_HEART_RATE_MONITOR_ON: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x00,  # 打开心率监测功能
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_HEART_RATE_MONITOR_OFF: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x00,  # 关闭心率监测功能
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_HEART_RATE_MONITOR_SWITCH: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x80,  # 查询心率监测开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_ON: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x0A,  # 打开心率波形上报开关
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_OFF: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x0A,  # 关闭心率波形上报开关
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_HEART_RATE_WAVEFORM_REPORT_SWITCH: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x8A,  # 查询心率波形上报开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HEART_RATE_VALUE: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x82,  # 心率数值查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_HEART_RATE_WAVEFORM: {
            'control_byte': 0x85,  # 心率监测
            'command_byte': 0x85,  # 心率波形查询
            'data': bytes([0x0F])  # 固定数据
        },

        # 呼吸监测指令信息查询和设置类型
        TYPE_CONTROL_BREATH_MONITOR_ON: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x00,  # 打开呼吸监测功能
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_BREATH_MONITOR_OFF: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x00,  # 关闭呼吸监测功能
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_BREATH_MONITOR_SWITCH: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x80,  # 查询呼吸监测开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_SET_LOW_BREATH_THRESHOLD: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x0B,  # 设置低缓呼吸判读阈值
            'data': None  # 数据需要动态设置
        },
        TYPE_QUERY_LOW_BREATH_THRESHOLD: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x8B,  # 查询低缓呼吸判读阈值
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_BREATH_INFO: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x81,  # 呼吸信息查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_BREATH_VALUE: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x82,  # 呼吸数值查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_CONTROL_BREATH_WAVEFORM_REPORT_ON: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x0C,  # 打开呼吸波形上报开关
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_BREATH_WAVEFORM_REPORT_OFF: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x0C,  # 关闭呼吸波形上报开关
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_BREATH_WAVEFORM_REPORT_SWITCH: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x8C,  # 查询呼吸波形上报开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_BREATH_WAVEFORM: {
            'control_byte': 0x81,  # 呼吸监测
            'command_byte': 0x85,  # 呼吸波形查询
            'data': bytes([0x0F])  # 固定数据
        },

        # 睡眠监测指令信息查询和设置类型
        TYPE_CONTROL_SLEEP_MONITOR_ON: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x00,  # 打开睡眠监测功能
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_SLEEP_MONITOR_OFF: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x00,  # 关闭睡眠监测功能
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_SLEEP_MONITOR_SWITCH: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x80,  # 查询睡眠监测开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_CONTROL_ABNORMAL_STRUGGLE_ON: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x13,  # 打开异常挣扎状态监测
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_ABNORMAL_STRUGGLE_OFF: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x13,  # 关闭异常挣扎状态监测
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_ABNORMAL_STRUGGLE_SWITCH: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x93,  # 查询异常挣扎状态开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_ABNORMAL_STRUGGLE_STATUS: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x91,  # 查询异常挣扎状态
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_SET_STRUGGLE_SENSITIVITY: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x1A,  # 设置挣扎状态判读灵敏度
            'data': None  # 数据需要动态设置
        },
        TYPE_QUERY_STRUGGLE_SENSITIVITY: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x9A,  # 查询挣扎状态判读灵敏度
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_CONTROL_NO_PERSON_TIMING_ON: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x14,  # 打开无人计时功能
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_NO_PERSON_TIMING_OFF: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x14,  # 关闭无人计时功能
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_NO_PERSON_TIMING_SWITCH: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x94,  # 查询无人计时功能开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_SET_NO_PERSON_TIMING_DURATION: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x15,  # 设置无人计时时长
            'data': None  # 数据需要动态设置
        },
        TYPE_QUERY_NO_PERSON_TIMING_DURATION: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x95,  # 查询无人计时时长
            'data': bytes([0x0F])  # 固定数据
        },
        # 无人计时状态查询
        TYPE_QUERY_NO_PERSON_TIMING_STATUS: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x92,  # 无人计时状态查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_SET_SLEEP_END_DURATION: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x16,  # 设置睡眠截止时长
            'data': None  # 数据需要动态设置
        },
        TYPE_QUERY_SLEEP_END_DURATION: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x96,  # 查询睡眠截止时长
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_BED_STATUS: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x81,  # 入床/离床状态查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_SLEEP_STATUS: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x82,  # 睡眠状态查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_AWAKE_DURATION: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x83,  # 清醒时长查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_LIGHT_SLEEP_DURATION: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x84,  # 浅睡时长查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_DEEP_SLEEP_DURATION: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x85,  # 深睡时长查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_SLEEP_QUALITY_SCORE: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x86,  # 睡眠质量评分查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_SLEEP_COMPREHENSIVE_STATUS: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x8D,  # 睡眠综合状态查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_SLEEP_ANOMALY: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x8E,  # 睡眠异常查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_SLEEP_STATISTICS: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x8F,  # 睡眠统计查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_SLEEP_QUALITY_LEVEL: {
            'control_byte': 0x84,  # 睡眠监测
            'command_byte': 0x90,  # 睡眠质量评级查询
            'data': bytes([0x0F])  # 固定数据
        }
    }

    # 查询类型到名称的映射（用于调试输出）
    QUERY_NAME_MAP = {
        # 基础指令信息查询和设置
        TYPE_QUERY_HEARTBEAT: "Heartbeat",
        TYPE_MODULE_RESET: "Module Reset",
        TYPE_QUERY_PRODUCT_MODEL: "Product Model",
        TYPE_QUERY_PRODUCT_ID: "Product ID",
        TYPE_QUERY_HARDWARE_MODEL: "Hardware Model",
        TYPE_QUERY_FIRMWARE_VERSION: "Firmware Version",
        TYPE_QUERY_INIT_COMPLETE: "Init Complete",
        TYPE_QUERY_RADAR_RANGE_BOUNDARY: "Radar Range Boundary",

        # 人体存在指令信息查询和设置
        TYPE_CONTROL_HUMAN_PRESENCE_ON: "Human Presence ON",
        TYPE_CONTROL_HUMAN_PRESENCE_OFF: "Human Presence OFF",
        TYPE_QUERY_HUMAN_PRESENCE_SWITCH: "Human Presence Switch",
        TYPE_QUERY_HUMAN_EXISTENCE_INFO: "Presence Status",
        TYPE_QUERY_HUMAN_MOTION_INFO: "Human Motion Info",
        TYPE_QUERY_HUMAN_BODY_MOTION_PARAM: "Body Motion Parameter",
        TYPE_QUERY_HUMAN_DISTANCE: "Human Distance",
        TYPE_QUERY_HUMAN_DIRECTION: "Human Direction",

        # 心率监测指令信息查询和设置
        TYPE_CONTROL_HEART_RATE_MONITOR_ON: "Heart Rate Monitor ON",
        TYPE_CONTROL_HEART_RATE_MONITOR_OFF: "Heart Rate Monitor OFF",
        TYPE_QUERY_HEART_RATE_MONITOR_SWITCH: "Heart Rate Monitor Switch",
        TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_ON: "Heart Rate Waveform Report ON",
        TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_OFF: "Heart Rate Waveform Report OFF",
        TYPE_QUERY_HEART_RATE_WAVEFORM_REPORT_SWITCH: "Heart Rate Waveform Report Switch",
        TYPE_QUERY_HEART_RATE_VALUE: "Heart Rate Value",
        TYPE_QUERY_HEART_RATE_WAVEFORM: "Heart Rate Waveform",

        # 呼吸监测指令
        TYPE_CONTROL_BREATH_MONITOR_ON: "Breath Monitor ON",
        TYPE_CONTROL_BREATH_MONITOR_OFF: "Breath Monitor OFF",
        TYPE_QUERY_BREATH_MONITOR_SWITCH: "Breath Monitor Switch",
        TYPE_SET_LOW_BREATH_THRESHOLD: "Set Low Breath Threshold",
        TYPE_QUERY_LOW_BREATH_THRESHOLD: "Query Low Breath Threshold",
        TYPE_QUERY_BREATH_INFO: "Breath Info",
        TYPE_QUERY_BREATH_VALUE: "Breath Value",
        TYPE_CONTROL_BREATH_WAVEFORM_REPORT_ON: "Breath Waveform Report ON",
        TYPE_CONTROL_BREATH_WAVEFORM_REPORT_OFF: "Breath Waveform Report OFF",
        TYPE_QUERY_BREATH_WAVEFORM_REPORT_SWITCH: "Breath Waveform Report Switch",
        TYPE_QUERY_BREATH_WAVEFORM: "Breath Waveform",

        # 睡眠监测指令
        TYPE_CONTROL_SLEEP_MONITOR_ON: "Sleep Monitor ON",
        TYPE_CONTROL_SLEEP_MONITOR_OFF: "Sleep Monitor OFF",
        TYPE_QUERY_SLEEP_MONITOR_SWITCH: "Sleep Monitor Switch",
        TYPE_CONTROL_ABNORMAL_STRUGGLE_ON: "Abnormal Struggle Monitor ON",
        TYPE_CONTROL_ABNORMAL_STRUGGLE_OFF: "Abnormal Struggle Monitor OFF",
        TYPE_QUERY_ABNORMAL_STRUGGLE_SWITCH: "Abnormal Struggle Monitor Switch",
        TYPE_QUERY_ABNORMAL_STRUGGLE_STATUS: "Abnormal Struggle Status",
        TYPE_SET_STRUGGLE_SENSITIVITY: "Set Struggle Sensitivity",
        TYPE_QUERY_STRUGGLE_SENSITIVITY: "Query Struggle Sensitivity",
        TYPE_CONTROL_NO_PERSON_TIMING_ON: "No Person Timing ON",
        TYPE_CONTROL_NO_PERSON_TIMING_OFF: "No Person Timing OFF",
        TYPE_QUERY_NO_PERSON_TIMING_SWITCH: "No Person Timing Switch",
        TYPE_SET_NO_PERSON_TIMING_DURATION: "Set No Person Timing Duration",
        TYPE_QUERY_NO_PERSON_TIMING_DURATION: "Query No Person Timing Duration",
        # 无人计时状态查询
        TYPE_QUERY_NO_PERSON_TIMING_STATUS: "No Person Timing Status",
        TYPE_SET_SLEEP_END_DURATION: "Set Sleep End Duration",
        TYPE_QUERY_SLEEP_END_DURATION: "Query Sleep End Duration",
        TYPE_QUERY_BED_STATUS: "Bed Status",
        TYPE_QUERY_SLEEP_STATUS: "Sleep Status",
        TYPE_QUERY_AWAKE_DURATION: "Awake Duration",
        TYPE_QUERY_LIGHT_SLEEP_DURATION: "Light Sleep Duration",
        TYPE_QUERY_DEEP_SLEEP_DURATION: "Deep Sleep Duration",
        TYPE_QUERY_SLEEP_QUALITY_SCORE: "Sleep Quality Score",
        TYPE_QUERY_SLEEP_COMPREHENSIVE_STATUS: "Sleep Comprehensive Status",
        TYPE_QUERY_SLEEP_ANOMALY: "Sleep Anomaly",
        TYPE_QUERY_SLEEP_STATISTICS: "Sleep Statistics",
        TYPE_QUERY_SLEEP_QUALITY_LEVEL: "Sleep Quality Level"
    }

    def __init__(self, data_processor, parse_interval=200,
                 presence_enabled=True,
                 heart_rate_enabled=True, heart_rate_waveform_enabled=False,
                 breath_monitoring_enabled=True, breath_waveform_enabled=False,
                 sleep_monitoring_enabled=True,
                 abnormal_struggle_enabled=False, struggle_sensitivity=1,
                 no_person_timing_enabled=False, no_person_timing_duration=30,
                 sleep_cutoff_duration=120,
                 max_retries=3, retry_delay=100, init_timeout=5000):
        """
        初始化R60ABD1实例。

        Args:
            data_processor: DataFlowProcessor实例。
            parse_interval: 数据解析间隔，单位毫秒 (建议50-200ms)。
            presence_enabled: 是否开启人体存在信息监测。
            heart_rate_enabled: 是否开启心率监测。
            heart_rate_waveform_enabled: 是否开启心率波形主动上报。
            breath_monitoring_enabled: 是否开启呼吸监测。
            breath_waveform_enabled: 是否开启呼吸波形主动上报。
            sleep_monitoring_enabled: 是否开启睡眠监测。
            abnormal_struggle_enabled: 是否开启异常挣扎监测。
            struggle_sensitivity: 挣扎灵敏度 (0=低, 1=中, 2=高)。
            no_person_timing_enabled: 是否开启无人计时功能。
            no_person_timing_duration: 无人计时时长 (30-180分钟)。
            sleep_cutoff_duration: 睡眠截止时长 (5-120分钟)。
            max_retries: 最大重试次数。
            retry_delay: 重试延迟时间，单位毫秒。
            init_timeout: 初始化超时时间，单位毫秒。

        Raises:
            ValueError: 参数验证失败。
            DeviceInitializationError: 设备初始化失败。

        Note:
            - 初始化过程包括参数验证、设备信息加载、设备初始化检查、功能配置等步骤。
            - 如果初始化失败，会停止定时器并抛出异常。
            - 成功初始化后，设备进入运行状态，定时器开始周期性解析数据。

        ==========================================

        Initialize R60ABD1 instance.

        Args:
            data_processor: DataFlowProcessor instance.
            parse_interval: Data parsing interval in milliseconds (recommended 50-200ms).
            presence_enabled: Whether to enable human presence information monitoring.
            heart_rate_enabled: Whether to enable heart rate monitoring.
            heart_rate_waveform_enabled: Whether to enable heart rate waveform active reporting.
            breath_monitoring_enabled: Whether to enable breath monitoring.
            breath_waveform_enabled: Whether to enable breath waveform active reporting.
            sleep_monitoring_enabled: Whether to enable sleep monitoring.
            abnormal_struggle_enabled: Whether to enable abnormal struggle monitoring.
            struggle_sensitivity: Struggle sensitivity (0=low, 1=medium, 2=high).
            no_person_timing_enabled: Whether to enable no person timing function.
            no_person_timing_duration: No person timing duration (30-180 minutes).
            sleep_cutoff_duration: Sleep cutoff duration (5-120 minutes).
            max_retries: Maximum retry count.
            retry_delay: Retry delay time in milliseconds.
            init_timeout: Initialization timeout in milliseconds.

        Raises:
            ValueError: Parameter validation failed.
            DeviceInitializationError: Device initialization failed.

        Note:
            - Initialization process includes parameter validation, device information loading,
              device initialization check, function configuration, etc.
            - If initialization fails, timer will be stopped and exception raised.
            - After successful initialization, device enters running state and timer starts periodic data parsing.
        """
        # 参数验证
        self._validate_init_parameters(
            parse_interval, struggle_sensitivity, no_person_timing_duration,
            sleep_cutoff_duration, max_retries, retry_delay, init_timeout
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

        # 产品信息
        # 产品型号(字符串)
        self.product_model = ""
        # 产品ID(字符串)
        self.product_id = ""
        # 硬件型号(字符串)
        self.hardware_model = ""
        # 固件版本(字符串)
        self.firmware_version = ""

        # ============================ 雷达探测属性 ============================

        # 位置状态
        # 是否在探测范围内
        self.radar_in_range = False

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
        # 人体距离(0-65535 cm)
        self.human_distance = 0
        # X坐标(有符号)
        self.human_position_x = 0
        # Y坐标(有符号)
        self.human_position_y = 0
        # Z坐标(有符号)
        self.human_position_z = 0

        # ============================= 呼吸监测属性 ===========================

        # 功能配置
        # 呼吸监测开关
        self.breath_monitoring_enabled = breath_monitoring_enabled
        # 呼吸波形上报开关
        self.breath_waveform_enabled = False
        # 低缓呼吸阈值(10-20次/min)
        self.low_breath_threshold = 10

        # 监测数据
        # 1:正常, 2:过高, 3:过低, 4:无
        self.breath_status = 0
        # 呼吸数值(0-35次/分)
        self.breath_value = 0
        # 5个字节的波形数据
        self.breath_waveform = [0, 0, 0, 0, 0]

        # ============================= 心率监测属性 ============================

        # 功能配置
        # 心率监测开关
        self.heart_rate_enabled = heart_rate_enabled
        # 心率波形上报开关
        self.heart_rate_waveform_enabled = False

        # 监测数据
        # 心率数值(60-120)
        self.heart_rate_value = 0
        # 5个字节的波形数据
        self.heart_rate_waveform = [0, 0, 0, 0, 0]

        # ============================ 睡眠监测属性 ============================

        # 基础状态
        # 睡眠监测开关
        self.sleep_monitoring_enabled = sleep_monitoring_enabled

        # 入床/离床状态
        # 0:离床, 1:入床, 2:无
        self.bed_status = 0
        # 睡眠状态
        # 0:深睡, 1:浅睡, 2:清醒, 3:无
        self.sleep_status = 0

        # 时长统计
        # 清醒时长(分钟)
        self.awake_duration = 0
        # 浅睡时长(分钟)
        self.light_sleep_duration = 0
        # 深睡时长(分钟)
        self.deep_sleep_duration = 0

        # 睡眠质量
        # 睡眠质量评分(0-100)
        self.sleep_quality_score = 0
        # 睡眠质量评级
        self.sleep_quality_rating = 0

        # 综合状态
        # 包含8个字段的字典
        self.sleep_comprehensive_status = {}
        # 睡眠异常状态
        self.sleep_anomaly = 0
        # 异常挣扎状态
        self.abnormal_struggle_status = 0
        # 无人计时状态
        self.no_person_timing_status = 0

        # 配置参数
        # 异常挣扎开关
        self.abnormal_struggle_enabled = abnormal_struggle_enabled
        # 无人计时开关
        self.no_person_timing_enabled = no_person_timing_enabled
        # 无人计时时长
        self.no_person_timing_duration = no_person_timing_duration
        # 睡眠截止时长
        self.sleep_cutoff_duration = sleep_cutoff_duration
        # 挣扎灵敏度
        self.struggle_sensitivity = struggle_sensitivity

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

            if R60ABD1.DEBUG_ENABLED:
                print(f"[Init] R60ABD1 initialized successfully")
                status = self.get_configuration_status()
                print(f"[Init] Configuration errors: {len(status['configuration_errors'])}")
                print(f"[Init] Product: {self.product_model} v{self.firmware_version}")

        except Exception as e:
            # 初始化失败，停止定时器
            self._is_running = False
            if hasattr(self, '_timer'):
                self._timer.deinit()
            raise DeviceInitializationError(f"Device initialization failed: {str(e)}")

    def _validate_init_parameters(self, parse_interval, struggle_sensitivity,
                                  no_person_timing_duration, sleep_cutoff_duration,
                                  max_retries, retry_delay, init_timeout):
        """
        验证初始化参数。

        Args:
            parse_interval: 数据解析间隔。
            struggle_sensitivity: 挣扎灵敏度。
            no_person_timing_duration: 无人计时时长。
            sleep_cutoff_duration: 睡眠截止时长。
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
            struggle_sensitivity: Struggle sensitivity.
            no_person_timing_duration: No person timing duration.
            sleep_cutoff_duration: Sleep cutoff duration.
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

        if struggle_sensitivity not in [self.SENSITIVITY_LOW, self.SENSITIVITY_MEDIUM, self.SENSITIVITY_HIGH]:
            raise ValueError("struggle_sensitivity must be 0 (low), 1 (medium), or 2 (high)")

        if no_person_timing_duration < 30 or no_person_timing_duration > 180 or no_person_timing_duration % 10 != 0:
            raise ValueError("no_person_timing_duration must be between 30-180 minutes in steps of 10")

        if sleep_cutoff_duration < 5 or sleep_cutoff_duration > 120:
            raise ValueError("sleep_cutoff_duration must be between 5-120 minutes")

        if max_retries < 0 or max_retries > 10:
            raise ValueError("max_retries must be between 0 and 10")

        if retry_delay < 0 or retry_delay > 1000:
            raise ValueError("retry_delay must be between 0ms and 1000ms")

        if init_timeout < 1000 or init_timeout > 30000:
            raise ValueError("init_timeout must be between 1000ms and 30000ms")

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
            if R60ABD1.DEBUG_ENABLED:
                print("[Init] Device not initialized, attempting reset...")
            reset_success = self._reset_and_wait_for_initialization()
            if not reset_success:
                raise DeviceInitializationError("Device initialization failed even after reset")

        # 步骤3: 配置设备功能
        self._auto_configure_device()

        # 步骤4: 验证关键功能配置
        self._verify_critical_configuration()

        elapsed_time = time.ticks_diff(time.ticks_ms(), start_time)
        if R60ABD1.DEBUG_ENABLED:
            print(f"[Init] Initialization completed in {elapsed_time}ms")

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
                if R60ABD1.DEBUG_ENABLED:
                    print(f"[Init] Warning: Failed to load {info_name}")

        return all_success

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
                if R60ABD1.DEBUG_ENABLED:
                    print("[Init] Device initialization confirmed")
                return True

            # 短暂延迟后重试
            time.sleep_ms(200)

        if R60ABD1.DEBUG_ENABLED:
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
        if R60ABD1.DEBUG_ENABLED:
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

        # 基础功能配置
        if self.presence_enabled:
            configuration_steps.append(("Enable Human Presence", self.enable_human_presence))
        else:
            configuration_steps.append(("Disable Human Presence", self.disable_human_presence))

        # 心率监测配置
        if self.heart_rate_enabled:
            configuration_steps.append(("Enable Heart Rate Monitor", self.enable_heart_rate_monitor))
            if self.heart_rate_waveform_enabled:
                configuration_steps.append(
                    ("Enable Heart Rate Waveform Report", self.enable_heart_rate_waveform_report))
            else:
                configuration_steps.append(
                    ("Disable Heart Rate Waveform Report", self.disable_heart_rate_waveform_report))
        else:
            configuration_steps.append(("Disable Heart Rate Monitor", self.disable_heart_rate_monitor))

        # 呼吸监测配置
        if self.breath_monitoring_enabled:
            configuration_steps.append(("Enable Breath Monitor", self.enable_breath_monitor))
            if self.breath_waveform_enabled:
                configuration_steps.append(("Enable Breath Waveform Report", self.enable_breath_waveform_report))
            else:
                configuration_steps.append(("Disable Breath Waveform Report", self.disable_breath_waveform_report))
        else:
            configuration_steps.append(("Disable Breath Monitor", self.disable_breath_monitor))

        # 睡眠监测配置
        if self.sleep_monitoring_enabled:
            configuration_steps.append(("Enable Sleep Monitor", self.enable_sleep_monitor))

            # 异常挣扎配置
            if self.abnormal_struggle_enabled:
                configuration_steps.append(("Enable Abnormal Struggle Monitor", self.enable_abnormal_struggle_monitor))
                # 设置挣扎灵敏度
                configuration_steps.append(("Set Struggle Sensitivity",
                                            lambda: self.set_struggle_sensitivity(self.struggle_sensitivity)))
            else:
                configuration_steps.append(
                    ("Disable Abnormal Struggle Monitor", self.disable_abnormal_struggle_monitor))

            # 无人计时配置
            if self.no_person_timing_enabled:
                configuration_steps.append(("Enable No Person Timing", self.enable_no_person_timing))
                # 设置无人计时时长
                configuration_steps.append(("Set No Person Timing Duration",
                                            lambda: self.set_no_person_timing_duration(self.no_person_timing_duration)))
            else:
                configuration_steps.append(("Disable No Person Timing", self.disable_no_person_timing))

            # 设置睡眠截止时长
            configuration_steps.append(("Set Sleep End Duration",
                                        lambda: self.set_sleep_end_duration(self.sleep_cutoff_duration)))
        else:
            configuration_steps.append(("Disable Sleep Monitor", self.disable_sleep_monitor))

        # 执行配置步骤
        for step_name, step_function in configuration_steps:
            success = self._execute_with_retry(step_function, step_name)
            if not success:
                self._configuration_errors.append(f"Failed to {step_name}")
                if R60ABD1.DEBUG_ENABLED:
                    print(f"[Init] Warning: {step_name} failed")

    def _verify_critical_configuration(self):
        """
        验证关键配置是否成功。

        Note:
            - 验证设备初始化状态和雷达范围状态。
            - 根据启用的功能验证相应模块的开关状态。
            - 验证失败会记录到配置错误列表中。

        ==========================================

        Verify critical configuration success.

        Note:
            - Verify device initialization status and radar range status.
            - Verify switch status of corresponding modules based on enabled functions.
            - Verification failures are recorded in configuration errors list.
        """
        critical_verifications = []

        # 验证设备初始化状态
        critical_verifications.append(("Device Initialization", self.query_init_complete))

        # 验证雷达范围状态
        critical_verifications.append(("Radar Range", self.query_radar_range_boundary))

        # 根据启用的功能添加验证
        if self.presence_enabled:
            critical_verifications.append(("Presence Detection", self.query_human_presence_switch))

        if self.heart_rate_enabled:
            critical_verifications.append(("Heart Rate Monitor", self.query_heart_rate_monitor_switch))

        if self.breath_monitoring_enabled:
            critical_verifications.append(("Breath Monitor", self.query_breath_monitor_switch))

        if self.sleep_monitoring_enabled:
            critical_verifications.append(("Sleep Monitor", self.query_sleep_monitor_switch))

        # 执行验证
        for verify_name, verify_func in critical_verifications:
            success, result = verify_func(timeout=500)
            if not success:
                self._configuration_errors.append(f"Verification failed: {verify_name}")
                if R60ABD1.DEBUG_ENABLED:
                    print(f"[Init] Warning: {verify_name} verification failed")

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
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Init] {operation_name} failed after {self.max_retries + 1} attempts: {e}")

        return False

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
            - Configuration errors list is a copy of the original list to prevent external modification.
        """
        return {
            'initialization_complete': self._initialization_complete,
            'configuration_errors': self._configuration_errors.copy(),
            'device_info': {
                'product_model': self.product_model,
                'product_id': self.product_id,
                'hardware_model': self.hardware_model,
                'firmware_version': self.firmware_version
            },
            'current_settings': {
                'presence_enabled': self.presence_enabled,
                'heart_rate_enabled': self.heart_rate_enabled,
                'heart_rate_waveform_enabled': self.heart_rate_waveform_enabled,
                'breath_monitoring_enabled': self.breath_monitoring_enabled,
                'breath_waveform_enabled': self.breath_waveform_enabled,
                'sleep_monitoring_enabled': self.sleep_monitoring_enabled,
                'abnormal_struggle_enabled': self.abnormal_struggle_enabled,
                'struggle_sensitivity': self.struggle_sensitivity,
                'no_person_timing_enabled': self.no_person_timing_enabled,
                'no_person_timing_duration': self.no_person_timing_duration,
                'sleep_cutoff_duration': self.sleep_cutoff_duration
            }
        }

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

    def _parse_human_position_data(self, data_bytes):
        """
        解析人体方位数据 (6字节: X(2B), Y(2B), Z(2B))。

        Args:
            data_bytes: 6字节的位置数据。

        Returns:
            tuple: (x, y, z) 坐标值，单位cm。

        Note:
            - 位置信息有正负：16位数据，最高位为符号位，剩余15位为数据位。
            - 使用_parse_signed_16bit_special方法解析每个坐标。

        ==========================================

        Parse human position data (6 bytes: X(2B), Y(2B), Z(2B)).

        Args:
            data_bytes: 6-byte position data.

        Returns:
            tuple: (x, y, z) coordinate values in cm.

        Note:
            - Position information has positive/negative: 16-bit data, highest bit is sign bit, remaining 15 bits are data bits.
            - Use _parse_signed_16bit_special method to parse each coordinate.
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

    def _parse_heart_rate_waveform_data(self, data_bytes):
        """
        解析心率波形数据 (5字节)。

        Args:
            data_bytes: 5字节的波形数据。

        Returns:
            tuple: 5个波形数据值 (v1, v2, v3, v4, v5)，数值范围0-255。

        Note:
            - 5个字节代表实时1s内5个数值。
            - 波形为正弦波数据，中轴线为128。
            - 数据长度不正确时返回默认值(128,128,128,128,128)。

        ==========================================

        Parse heart rate waveform data (5 bytes).

        Args:
            data_bytes: 5-byte waveform data.

        Returns:
            tuple: 5 waveform data values (v1, v2, v3, v4, v5), value range 0-255.

        Note:
            - 5 bytes represent 5 values in real-time 1 second.
            - Waveform is sine wave data, center axis is 128.
            - Returns default values (128,128,128,128,128) if data length is incorrect.
        """
        if len(data_bytes) != 5:
            return (128, 128, 128, 128, 128)

        return (
            data_bytes[0],
            data_bytes[1],
            data_bytes[2],
            data_bytes[3],
            data_bytes[4]
        )

    def _parse_sleep_comprehensive_data(self, data_bytes):
        """
        解析睡眠综合状态数据 (8字节)。

        Args:
            data_bytes: 8字节的睡眠综合状态数据。

        Returns:
            tuple: (存在, 睡眠状态, 平均呼吸, 平均心跳, 翻身次数, 大幅度体动占比, 小幅度体动占比, 呼吸暂停次数)

        Note:
            - 存在: 1有人 0无人。
            - 睡眠状态: 3离床 2清醒 1浅睡 0深睡。
            - 平均呼吸: 10分钟内检测的平均值。
            - 平均心跳: 10分钟内检测的平均值。
            - 翻身次数: 处于浅睡或深睡的翻身次数。
            - 大幅度体动占比: 0~100。
            - 小幅度体动占比: 0~100。
            - 呼吸暂停次数: 10分钟呼吸暂停次数。

        ==========================================

        Parse sleep comprehensive status data (8 bytes).

        Args:
            data_bytes: 8-byte sleep comprehensive status data.

        Returns:
            tuple: (presence, sleep status, average breath, average heartbeat, turnover count, large movement ratio, small movement ratio, apnea count)

        Note:
            - Presence: 1 someone 0 no one.
            - Sleep status: 3 leave bed 2 awake 1 light sleep 0 deep sleep.
            - Average breath: Average value detected in 10 minutes.
            - Average heartbeat: Average value detected in 10 minutes.
            - Turnover count: Turnover count while in light or deep sleep.
            - Large movement ratio: 0~100.
            - Small movement ratio: 0~100.
            - Apnea count: Apnea count in 10 minutes.
        """
        if len(data_bytes) != 8:
            return (0, 0, 0, 0, 0, 0, 0, 0)

        return (
            data_bytes[0],  # 存在: 1有人 0无人
            data_bytes[1],  # 睡眠状态: 3离床 2清醒 1浅睡 0深睡
            data_bytes[2],  # 平均呼吸: 10分钟内检测的平均值
            data_bytes[3],  # 平均心跳: 10分钟内检测的平均值
            data_bytes[4],  # 翻身次数: 处于浅睡或深睡的翻身次数
            data_bytes[5],  # 大幅度体动占比: 0~100
            data_bytes[6],  # 小幅度体动占比: 0~100
            data_bytes[7]  # 呼吸暂停次数: 10分钟呼吸暂停次数
        )

    def _parse_sleep_statistics_data(self, data_bytes):
        """
        解析睡眠统计信息数据 (12字节)。

        Args:
            data_bytes: 12字节的睡眠统计信息数据。

        Returns:
            tuple: (睡眠质量评分, 睡眠总时长, 清醒时长占比, 浅睡时长占比, 深睡时长占比,
                   离床时长, 离床次数, 翻身次数, 平均呼吸, 平均心跳, 呼吸暂停次数)

        Note:
            - 睡眠质量评分: 0~100。
            - 睡眠总时长: 0~65535分钟。
            - 清醒时长占比: 0~100。
            - 浅睡时长占比: 0~100。
            - 深睡时长占比: 0~100。
            - 离床时长: 0~255。
            - 离床次数: 0~255。
            - 翻身次数: 0~255。
            - 平均呼吸: 0~25。
            - 平均心跳: 0~100。
            - 呼吸暂停次数: 0~10。

        ==========================================

        Parse sleep statistics data (12 bytes).

        Args:
            data_bytes: 12-byte sleep statistics data.

        Returns:
            tuple: (sleep quality score, total sleep duration, awake duration ratio, light sleep duration ratio, deep sleep duration ratio,
                   leave bed duration, leave bed count, turnover count, average breath, average heartbeat, apnea count)

        Note:
            - Sleep quality score: 0~100.
            - Total sleep duration: 0~65535 minutes.
            - Awake duration ratio: 0~100.
            - Light sleep duration ratio: 0~100.
            - Deep sleep duration ratio: 0~100.
            - Leave bed duration: 0~255.
            - Leave bed count: 0~255.
            - Turnover count: 0~255.
            - Average breath: 0~25.
            - Average heartbeat: 0~100.
            - Apnea count: 0~10.
        """
        if len(data_bytes) != 12:
            return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        # 解析2字节的睡眠总时长
        total_sleep_duration = (data_bytes[1] << 8) | data_bytes[2]

        return (
            data_bytes[0],  # 睡眠质量评分: 0~100
            total_sleep_duration,  # 睡眠总时长: 0~65535分钟
            data_bytes[3],  # 清醒时长占比: 0~100
            data_bytes[4],  # 浅睡时长占比: 0~100
            data_bytes[5],  # 深睡时长占比: 0~100
            data_bytes[6],  # 离床时长: 0~255
            data_bytes[7],  # 离床次数: 0~255
            data_bytes[8],  # 翻身次数: 0~255
            data_bytes[9],  # 平均呼吸: 0~25
            data_bytes[10],  # 平均心跳: 0~100
            data_bytes[11]  # 呼吸暂停次数: 0~10
        )

    def _parse_breath_waveform_data(self, data_bytes):
        """
        解析呼吸波形数据 (5字节)。

        Args:
            data_bytes: 5字节的呼吸波形数据。

        Returns:
            tuple: 5个波形数据值 (v1, v2, v3, v4, v5)，数值范围0-255。

        Note:
            - 5个字节代表实时1s内5个数值。
            - 波形为正弦波数据，中轴线为128。
            - 数据长度不正确时返回默认值(128,128,128,128,128)。

        ==========================================

        Parse breath waveform data (5 bytes).

        Args:
            data_bytes: 5-byte breath waveform data.

        Returns:
            tuple: 5 waveform data values (v1, v2, v3, v4, v5), value range 0-255.

        Note:
            - 5 bytes represent 5 values in real-time 1 second.
            - Waveform is sine wave data, center axis is 128.
            - Returns default values (128,128,128,128,128) if data length is incorrect.
        """
        if len(data_bytes) != 5:
            return (128, 128, 128, 128, 128)

        return (
            data_bytes[0],
            data_bytes[1],
            data_bytes[2],
            data_bytes[3],
            data_bytes[4]
        )

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
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Parse] Raw product data: {data_bytes}, hex: {data_bytes.hex()}")

            # 找到第一个空字节的位置，截取有效部分
            if b'\x00' in data_bytes:
                # 找到第一个空字节，截取之前的部分
                null_index = data_bytes.index(b'\x00')
                valid_data = data_bytes[:null_index]
                if R60ABD1.DEBUG_ENABLED:
                    print(f"[Parse] After null removal: {valid_data}, hex: {valid_data.hex()}")
            else:
                valid_data = data_bytes

            # 解码为字符串 - 移除关键字参数
            # MicroPython 的 decode 方法不支持 errors='ignore' 关键字参数
            product_info = valid_data.decode('utf-8').strip()
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Parse] Decoded product info: '{product_info}'")

            return (product_info,)
        except Exception as e:
            # 如果解码失败，尝试其他方式
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Parse] Product info parse error: {e}, data: {data_bytes}")

            # 尝试使用 ascii 解码作为备选方案
            try:
                product_info = valid_data.decode('ascii').strip()
                if R60ABD1.DEBUG_ENABLED:
                    print(f"[Parse] ASCII decoded product info: '{product_info}'")
                return (product_info,)
            except:
                return ("",)

    def _parse_firmware_version_data(self, data_bytes):
        """
        解析固件版本数据 (可变长度字符串)。

        Args:
            data_bytes: 固件版本字节数据。

        Returns:
            tuple: (固件版本字符串,)

        Note:
            - 正确处理包含空字节的字符串。
            - 找到第一个空字节的位置，截取有效部分。
            - 优先使用UTF-8解码，失败时尝试ASCII解码。

        ==========================================

        Parse firmware version data (variable length string).

        Args:
            data_bytes: Firmware version byte data.

        Returns:
            tuple: (Firmware version string,)

        Note:
            - Correctly handles strings containing null bytes.
            - Find position of first null byte, extract valid part.
            - Prefer UTF-8 decoding, fall back to ASCII decoding if failed.
        """
        try:
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Parse] Raw firmware data: {data_bytes}, hex: {data_bytes.hex()}")

            # 找到第一个空字节的位置，截取有效部分
            if b'\x00' in data_bytes:
                # 找到第一个空字节，截取之前的部分
                null_index = data_bytes.index(b'\x00')
                valid_data = data_bytes[:null_index]
                if R60ABD1.DEBUG_ENABLED:
                    print(f"[Parse] After null removal: {valid_data}, hex: {valid_data.hex()}")
            else:
                valid_data = data_bytes

            # 解码为字符串 - 移除关键字参数
            version = valid_data.decode('utf-8').strip()
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Parse] Decoded firmware version: '{version}'")

            return (version,)
        except Exception as e:
            # 如果解码失败，尝试其他方式
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Parse] Firmware version parse error: {e}, data: {data_bytes}")

            # 尝试使用 ascii 解码作为备选方案
            try:
                version = valid_data.decode('ascii').strip()
                if R60ABD1.DEBUG_ENABLED:
                    print(f"[Parse] ASCII decoded firmware version: '{version}'")
                return (version,)
            except:
                return ("",)

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
            if R60ABD1.DEBUG_ENABLED:
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
                if R60ABD1.DEBUG_ENABLED:
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
            if R60ABD1.DEBUG_ENABLED:
                operation_name = self.QUERY_NAME_MAP.get(operation_type, f"Unknown({operation_type})")
                print(f"[Operation] {operation_name} operation sent")
                frame_hex = ' '.join(['{:02X}'.format(b) for b in operation_frame])
                print(f"[Operation] Sent frame: {frame_hex}")

            # 等待设备响应
            start_time = time.ticks_ms()
            while not self._query_response_received:
                # 检查超时
                if time.ticks_diff(time.ticks_ms(), start_time) >= timeout:
                    if R60ABD1.DEBUG_ENABLED:
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
            if R60ABD1.DEBUG_ENABLED:
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

            if R60ABD1.DEBUG_ENABLED:
                print("[Operation] Operation state reset")

    def query_heartbeat(self, timeout=200):
        """查询心跳包（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_HEARTBEAT, timeout=timeout)

    def reset_module(self, timeout=500):
        """模组复位（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_MODULE_RESET, timeout=timeout)

    def query_product_model(self, timeout=200):
        """查询产品型号（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_PRODUCT_MODEL, timeout=timeout)

    def query_product_id(self, timeout=200):
        """查询产品ID（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_PRODUCT_ID, timeout=timeout)

    def query_hardware_model(self, timeout=200):
        """查询硬件型号（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_HARDWARE_MODEL, timeout=timeout)

    def query_firmware_version(self, timeout=200):
        """查询固件版本（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_FIRMWARE_VERSION, timeout=timeout)

    def query_init_complete(self, timeout=200):
        """查询初始化是否完成（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_INIT_COMPLETE, timeout=timeout)

    def query_radar_range_boundary(self, timeout=200):
        """查询雷达探测范围越界状态（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_RADAR_RANGE_BOUNDARY, timeout=timeout)

    def enable_human_presence(self, timeout=200):
        """
        打开人体存在功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_HUMAN_PRESENCE_ON, timeout=timeout)

    def disable_human_presence(self, timeout=200):
        """
        关闭人体存在功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_HUMAN_PRESENCE_OFF, timeout=timeout)

    def query_human_presence_switch(self, timeout=200):
        """
        查询人体存在开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH, timeout=timeout)

    def query_presence_status(self, timeout=200):
        """查询存在信息状态（阻塞式）"""
        return self._execute_operation(R60ABD1.TYPE_QUERY_HUMAN_EXISTENCE_INFO, timeout=timeout)

    def query_human_motion_info(self, timeout=200):
        """
        查询运动信息（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 运动状态)
                    - 运动状态: 必须是 R60ABD1.MOTION_NONE, R60ABD1.MOTION_STATIC, R60ABD1.MOTION_ACTIVE 中的一个

        Raises:
            ValueError: 如果返回的运动状态不是预定义的有效值
        """
        success, motion_status = self._execute_operation(
            R60ABD1.TYPE_QUERY_HUMAN_MOTION_INFO,
            timeout=timeout
        )
        # 验证返回的运动状态是否有效
        if success and motion_status not in (R60ABD1.MOTION_NONE, R60ABD1.MOTION_STATIC, R60ABD1.MOTION_ACTIVE):
            raise ValueError(f"Invalid motion status: {motion_status}")

        return success, motion_status

    def query_human_body_motion_param(self, timeout=200):
        """
        查询体动参数（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 体动参数值)
                    - 体动参数值: 0-100
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HUMAN_BODY_MOTION_PARAM, timeout=timeout)

    def query_human_distance(self, timeout=200):
        """
        查询人体距离（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 人体距离)
                    - 人体距离: 0-65535 cm
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HUMAN_DISTANCE, timeout=timeout)

    def query_human_direction(self, timeout=200):
        """
        查询人体方位（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 方位坐标)
                    - 方位坐标: (x, y, z) 三元组，单位cm
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HUMAN_DIRECTION, timeout=timeout)

    def enable_heart_rate_monitor(self, timeout=200):
        """
        打开心率监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_HEART_RATE_MONITOR_ON, timeout=timeout)

    def disable_heart_rate_monitor(self, timeout=200):
        """
        关闭心率监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_HEART_RATE_MONITOR_OFF, timeout=timeout)

    def query_heart_rate_monitor_switch(self, timeout=200):
        """
        查询心率监测开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HEART_RATE_MONITOR_SWITCH, timeout=timeout)

    def enable_heart_rate_waveform_report(self, timeout=200):
        """
        打开心率波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_ON, timeout=timeout)

    def disable_heart_rate_waveform_report(self, timeout=200):
        """
        关闭心率波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_OFF, timeout=timeout)

    def query_heart_rate_waveform_report_switch(self, timeout=200):
        """
        查询心率波形上报开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HEART_RATE_WAVEFORM_REPORT_SWITCH, timeout=timeout)

    def query_heart_rate_value(self, timeout=200):
        """
        查询心率数值（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 心率数值)
                    - 心率数值: 60-120 次/分
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HEART_RATE_VALUE, timeout=timeout)

    def query_heart_rate_waveform(self, timeout=200):
        """
        查询心率波形（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 心率波形数据)
                    - 心率波形数据: 5个字节的波形数据列表
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_HEART_RATE_WAVEFORM, timeout=timeout)

    def enable_breath_monitor(self, timeout=200):
        """
        打开呼吸监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_BREATH_MONITOR_ON, timeout=timeout)

    def disable_breath_monitor(self, timeout=200):
        """
        关闭呼吸监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_BREATH_MONITOR_OFF, timeout=timeout)

    def query_breath_monitor_switch(self, timeout=200):
        """
        查询呼吸监测开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_BREATH_MONITOR_SWITCH, timeout=timeout)

    def set_low_breath_threshold(self, threshold, timeout=200):
        """
        设置低缓呼吸判读阈值（阻塞式）

        Args:
            threshold: 阈值数值，范围10-20
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if threshold < 10 or threshold > 20:
            raise ValueError("Low breath threshold must be between 10 and 20")

        data = bytes([threshold])
        return self._execute_operation(R60ABD1.TYPE_SET_LOW_BREATH_THRESHOLD, data=data, timeout=timeout)

    def query_low_breath_threshold(self, timeout=200):
        """
        查询低缓呼吸判读阈值（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 阈值数值)
                    - 阈值数值: 10-20
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_LOW_BREATH_THRESHOLD, timeout=timeout)

    def query_breath_info(self, timeout=200):
        """
        查询呼吸信息（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 呼吸状态)
                    - 呼吸状态: 必须是 R60ABD1.BREATH_NORMAL, R60ABD1.BREATH_HIGH,
                               R60ABD1.BREATH_LOW, R60ABD1.BREATH_NONE 中的一个

        Raises:
            ValueError: 如果返回的呼吸状态不是预定义的有效值
        """
        success, breath_status = self._execute_operation(
            R60ABD1.TYPE_QUERY_BREATH_INFO,
            timeout=timeout
        )
        # 验证返回的呼吸状态是否有效
        if success and breath_status not in (R60ABD1.BREATH_NORMAL, R60ABD1.BREATH_HIGH,
                                             R60ABD1.BREATH_LOW, R60ABD1.BREATH_NONE):
            raise ValueError(f"Invalid breath status: {breath_status}")

        return success, breath_status

    def query_breath_value(self, timeout=200):
        """
        查询呼吸数值（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 呼吸数值)
                    - 呼吸数值: 0-35 次/分
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_BREATH_VALUE, timeout=timeout)

    def enable_breath_waveform_report(self, timeout=200):
        """
        打开呼吸波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_BREATH_WAVEFORM_REPORT_ON, timeout=timeout)

    def disable_breath_waveform_report(self, timeout=200):
        """
        关闭呼吸波形上报开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_BREATH_WAVEFORM_REPORT_OFF, timeout=timeout)

    def query_breath_waveform_report_switch(self, timeout=200):
        """
        查询呼吸波形上报开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_BREATH_WAVEFORM_REPORT_SWITCH, timeout=timeout)

    def query_breath_waveform(self, timeout=200):
        """
        查询呼吸波形（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 呼吸波形数据)
                    - 呼吸波形数据: 5个字节的波形数据列表
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_BREATH_WAVEFORM, timeout=timeout)

    def enable_sleep_monitor(self, timeout=200):
        """
        打开睡眠监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_SLEEP_MONITOR_ON, timeout=timeout)

    def disable_sleep_monitor(self, timeout=200):
        """
        关闭睡眠监测功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_SLEEP_MONITOR_OFF, timeout=timeout)

    def query_sleep_monitor_switch(self, timeout=200):
        """
        查询睡眠监测开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_SLEEP_MONITOR_SWITCH, timeout=timeout)

    def enable_abnormal_struggle_monitor(self, timeout=200):
        """
        打开异常挣扎状态监测（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_ABNORMAL_STRUGGLE_ON, timeout=timeout)

    def disable_abnormal_struggle_monitor(self, timeout=200):
        """
        关闭异常挣扎状态监测（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_ABNORMAL_STRUGGLE_OFF, timeout=timeout)

    def query_abnormal_struggle_switch(self, timeout=200):
        """
        查询异常挣扎状态开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_ABNORMAL_STRUGGLE_SWITCH, timeout=timeout)

    def query_abnormal_struggle_status(self, timeout=200):
        """
        查询异常挣扎状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 挣扎状态)
                    - 挣扎状态: 必须是 R60ABD1.STRUGGLE_NONE, R60ABD1.STRUGGLE_NORMAL,
                               R60ABD1.STRUGGLE_ABNORMAL 中的一个

        Raises:
            ValueError: 如果返回的挣扎状态不是预定义的有效值
        """
        success, struggle_status = self._execute_operation(
            R60ABD1.TYPE_QUERY_ABNORMAL_STRUGGLE_STATUS,
            timeout=timeout
        )
        # 验证返回的挣扎状态是否有效
        if success and struggle_status not in (R60ABD1.STRUGGLE_NONE, R60ABD1.STRUGGLE_NORMAL,
                                               R60ABD1.STRUGGLE_ABNORMAL):
            raise ValueError(f"Invalid struggle status: {struggle_status}")

        return success, struggle_status

    def set_struggle_sensitivity(self, sensitivity, timeout=200):
        """
        设置挣扎状态判读灵敏度（阻塞式）

        Args:
            sensitivity: 灵敏度 (0=低, 1=中, 2=高)
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if sensitivity not in [R60ABD1.SENSITIVITY_LOW, R60ABD1.SENSITIVITY_MEDIUM, R60ABD1.SENSITIVITY_HIGH]:
            raise ValueError("Sensitivity must be 0 (low), 1 (medium), or 2 (high)")

        data = bytes([sensitivity])
        return self._execute_operation(R60ABD1.TYPE_SET_STRUGGLE_SENSITIVITY, data=data, timeout=timeout)

    def query_struggle_sensitivity(self, timeout=200):
        """
        查询挣扎状态判读灵敏度（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 灵敏度值)
                    - 灵敏度值: 0-低, 1-中, 2-高
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_STRUGGLE_SENSITIVITY, timeout=timeout)

    def enable_no_person_timing(self, timeout=200):
        """
        打开无人计时功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_NO_PERSON_TIMING_ON, timeout=timeout)

    def disable_no_person_timing(self, timeout=200):
        """
        关闭无人计时功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60ABD1.TYPE_CONTROL_NO_PERSON_TIMING_OFF, timeout=timeout)

    def query_no_person_timing_switch(self, timeout=200):
        """
        查询无人计时功能开关（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_SWITCH, timeout=timeout)

    def set_no_person_timing_duration(self, duration, timeout=200):
        """
        设置无人计时时长（阻塞式）

        Args:
            duration: 时长数值，范围30-180分钟，步长10分钟
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if duration < 30 or duration > 180 or duration % 10 != 0:
            raise ValueError("No person timing duration must be between 30-180 minutes in steps of 10")

        data = bytes([duration])
        return self._execute_operation(R60ABD1.TYPE_SET_NO_PERSON_TIMING_DURATION, data=data, timeout=timeout)

    def query_no_person_timing_duration(self, timeout=200):
        """
        查询无人计时时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 30-180分钟
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_DURATION, timeout=timeout)

    def set_sleep_end_duration(self, duration, timeout=200):
        """
        设置睡眠截止时长（阻塞式）

        Args:
            duration: 时长数值，范围5-120分钟
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        if duration < 5 or duration > 120:
            raise ValueError("Sleep end duration must be between 5-120 minutes")

        data = bytes([duration])
        return self._execute_operation(R60ABD1.TYPE_SET_SLEEP_END_DURATION, data=data, timeout=timeout)

    def query_sleep_end_duration(self, timeout=200):
        """
        查询睡眠截止时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 5-120分钟
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_SLEEP_END_DURATION, timeout=timeout)

    def query_no_person_timing_status(self, timeout=200):
        """
        查询无人计时状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 无人计时状态)
                    - 无人计时状态: 必须是 R60ABD1.NO_PERSON_TIMING_NONE, R60ABD1.NO_PERSON_TIMING_NORMAL,
                                   R60ABD1.NO_PERSON_TIMING_ABNORMAL 中的一个

        Raises:
            ValueError: 如果返回的无人计时状态不是预定义的有效值
        """
        success, timing_status = self._execute_operation(
            R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_STATUS,
            timeout=timeout
        )

        # 验证返回的无人计时状态是否有效
        if success and timing_status not in (R60ABD1.NO_PERSON_TIMING_NONE, R60ABD1.NO_PERSON_TIMING_NORMAL,
                                             R60ABD1.NO_PERSON_TIMING_ABNORMAL):
            raise ValueError(f"Invalid no person timing status: {timing_status}")

        return success, timing_status

    def query_bed_status(self, timeout=200):
        """
        查询入床/离床状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 床状态)
                    - 床状态: 必须是 R60ABD1.BED_LEAVE, R60ABD1.BED_ENTER, R60ABD1.BED_NONE 中的一个

        Raises:
            ValueError: 如果返回的床状态不是预定义的有效值
        """
        success, bed_status = self._execute_operation(
            R60ABD1.TYPE_QUERY_BED_STATUS,
            timeout=timeout
        )
        # 验证返回的床状态是否有效
        if success and bed_status not in (R60ABD1.BED_LEAVE, R60ABD1.BED_ENTER, R60ABD1.BED_NONE):
            raise ValueError(f"Invalid bed status: {bed_status}")

        return success, bed_status

    def query_sleep_status(self, timeout=200):
        """
        查询睡眠状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 睡眠状态)
                    - 睡眠状态: 必须是 R60ABD1.SLEEP_DEEP, R60ABD1.SLEEP_LIGHT,
                               R60ABD1.SLEEP_AWAKE, R60ABD1.SLEEP_NONE 中的一个

        Raises:
            ValueError: 如果返回的睡眠状态不是预定义的有效值
        """
        success, sleep_status = self._execute_operation(
            R60ABD1.TYPE_QUERY_SLEEP_STATUS,
            timeout=timeout
        )
        # 验证返回的睡眠状态是否有效
        if success and sleep_status not in (R60ABD1.SLEEP_DEEP, R60ABD1.SLEEP_LIGHT,
                                            R60ABD1.SLEEP_AWAKE, R60ABD1.SLEEP_NONE):
            raise ValueError(f"Invalid sleep status: {sleep_status}")

        return success, sleep_status

    def query_awake_duration(self, timeout=200):
        """
        查询清醒时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 分钟数
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_AWAKE_DURATION, timeout=timeout)

    def query_light_sleep_duration(self, timeout=200):
        """
        查询浅睡时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 分钟数
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_LIGHT_SLEEP_DURATION, timeout=timeout)

    def query_deep_sleep_duration(self, timeout=200):
        """
        查询深睡时长（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 时长数值)
                    - 时长数值: 分钟数
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_DEEP_SLEEP_DURATION, timeout=timeout)

    def query_sleep_quality_score(self, timeout=200):
        """
        查询睡眠质量评分（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 评分数值)
                    - 评分数值: 0-100
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_SLEEP_QUALITY_SCORE, timeout=timeout)

    def query_sleep_comprehensive_status(self, timeout=200):
        """
        查询睡眠综合状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 综合状态数据)
                    - 综合状态数据: 8字节的睡眠综合状态
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_SLEEP_COMPREHENSIVE_STATUS, timeout=timeout)

    def query_sleep_anomaly(self, timeout=200):
        """
        查询睡眠异常（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 异常状态)
                    - 异常状态: 必须是 R60ABD1.SLEEP_ANOMALY_SHORT, R60ABD1.SLEEP_ANOMALY_LONG,
                               R60ABD1.SLEEP_ANOMALY_NO_PERSON, R60ABD1.SLEEP_ANOMALY_NONE 中的一个

        Raises:
            ValueError: 如果返回的异常状态不是预定义的有效值
        """
        success, anomaly_status = self._execute_operation(
            R60ABD1.TYPE_QUERY_SLEEP_ANOMALY,
            timeout=timeout
        )
        # 验证返回的异常状态是否有效
        if success and anomaly_status not in (R60ABD1.SLEEP_ANOMALY_SHORT, R60ABD1.SLEEP_ANOMALY_LONG,
                                              R60ABD1.SLEEP_ANOMALY_NO_PERSON, R60ABD1.SLEEP_ANOMALY_NONE):
            raise ValueError(f"Invalid sleep anomaly status: {anomaly_status}")

        return success, anomaly_status

    def query_sleep_statistics(self, timeout=200):
        """
        查询睡眠统计（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 统计数据)
                    - 统计数据: 12字节的睡眠统计信息
        """
        return self._execute_operation(R60ABD1.TYPE_QUERY_SLEEP_STATISTICS, timeout=timeout)

    def query_sleep_quality_level(self, timeout=200):
        """
        查询睡眠质量评级（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 质量评级)
                    - 质量评级: 必须是 R60ABD1.SLEEP_QUALITY_NONE, R60ABD1.SLEEP_QUALITY_GOOD,
                               R60ABD1.SLEEP_QUALITY_NORMAL, R60ABD1.SLEEP_QUALITY_POOR 中的一个

        Raises:
            ValueError: 如果返回的质量评级不是预定义的有效值
        """
        success, quality_level = self._execute_operation(
            R60ABD1.TYPE_QUERY_SLEEP_QUALITY_LEVEL,
            timeout=timeout
        )
        # 验证返回的质量评级是否有效
        if success and quality_level not in (R60ABD1.SLEEP_QUALITY_NONE, R60ABD1.SLEEP_QUALITY_GOOD,
                                             R60ABD1.SLEEP_QUALITY_NORMAL, R60ABD1.SLEEP_QUALITY_POOR):
            raise ValueError(f"Invalid sleep quality level: {quality_level}")

        return success, quality_level

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

            if R60ABD1.DEBUG_ENABLED:
                query_name = self.QUERY_NAME_MAP.get(expected_type, f"Unknown({expected_type})")
                print(f"[Query] {query_name} response received: {response_data}")

        # 情况2：当前正在进行其他类型的查询，但收到了本响应
        elif self._query_in_progress and self._current_query_type != expected_type:
            if R60ABD1.DEBUG_ENABLED:
                current_query = self.QUERY_NAME_MAP.get(self._current_query_type,
                                                        f"Unknown({self._current_query_type})")
                print(f"[Query] Unexpected {response_name} response during {current_query} query: {response_data}")

        # 情况3：没有查询在进行，但收到了查询响应
        elif not self._query_in_progress:
            if R60ABD1.DEBUG_ENABLED:
                print(f"[Query] Unsolicited {response_name} response: {response_data}")

    def _update_property_with_debug(self, property_name, new_value, debug_message):
        """
        更新属性并输出调试信息。

        Args:
            property_name: 属性名称。
            new_value: 新值。
            debug_message: 调试信息。

        Note:
            - 使用setattr动态设置属性值。
            - 如果启用调试模式，输出调试信息。

        ==========================================

        Update property with debug output.

        Args:
            property_name: Property name.
            new_value: New value.
            debug_message: Debug message.

        Note:
            - Use setattr to dynamically set property value.
            - Output debug information if debug mode is enabled.
        """
        setattr(self, property_name, new_value)
        if R60ABD1.DEBUG_ENABLED:
            print(debug_message)

    def update_properties_from_frame(self, frame):
        """
        根据解析的帧更新属性值。

        Args:
            frame: DataFlowProcessor解析后的帧数据字典。

        Note:
            - 根据控制字和命令字分发到不同的处理逻辑。
            - 更新对应的设备属性值。
            - 处理查询响应和主动上报数据。

        ==========================================

        Update properties from parsed frame.

        Args:
            frame: DataFlowProcessor parsed frame data dictionary.

        Note:
            - Dispatch to different processing logic based on control byte and command byte.
            - Update corresponding device property values.
            - Handle query responses and active reporting data.
        """
        control = frame['control_byte']
        command = frame['command_byte']
        data = frame['data']

        # 心跳包 (0x01)
        if control == 0x01:
            # 心跳包上报
            if command == 0x01:
                self.heartbeat_last_received = time.ticks_ms()
                if R60ABD1.DEBUG_ENABLED:
                    print("[Heartbeat] Received")
            # 心跳包查询响应
            elif command == 0x80:
                self.heartbeat_last_received = time.ticks_ms()
                self._handle_query_response(
                    R60ABD1.TYPE_QUERY_HEARTBEAT,
                    True,
                    "Heartbeat"
                )

            # 模组复位响应
            elif command == 0x02:
                self.module_reset_flag = True
                self.module_reset_timestamp = time.ticks_ms()
                self._handle_query_response(
                    R60ABD1.TYPE_MODULE_RESET,
                    True,
                    "Module Reset"
                )

        # 产品信息指令 (0x02)
        elif control == 0x02:
            # 产品型号查询响应
            if command == 0xA1:
                if data:
                    product_info = self._parse_product_info_data(data)[0]
                    self.product_model = product_info
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_PRODUCT_MODEL,
                        product_info,
                        "Product Model"
                    )

            # 产品ID查询响应
            elif command == 0xA2:
                if data:
                    # 解析产品ID数据
                    product_id = self._parse_product_info_data(data)[0]
                    # 更新产品ID属性
                    self.product_id = product_id
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_PRODUCT_ID,
                        product_id,
                        "Product ID"
                    )

            # 硬件型号查询响应
            elif command == 0xA3:
                if data:
                    # 解析硬件型号数据
                    hardware_model = self._parse_product_info_data(data)[0]
                    # 更新硬件型号属性
                    self.hardware_model = hardware_model
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HARDWARE_MODEL,
                        hardware_model,
                        "Hardware Model"
                    )

            # 固件版本查询响应
            elif command == 0xA4:
                if data:
                    # 解析固件版本数据
                    firmware_version = self._parse_firmware_version_data(data)[0]
                    # 更新固件版本属性
                    self.firmware_version = firmware_version
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_FIRMWARE_VERSION,
                        firmware_version,
                        "Firmware Version"
                    )

        # 系统初始化状态 (0x05)
        elif control == 0x05:
            # 初始化完成信息
            if command == 0x01:
                if data and len(data) > 0:
                    self.system_initialized = (data[0] == 0x01)
                    self.system_initialized_timestamp = time.ticks_ms()
                    if R60ABD1.DEBUG_ENABLED:
                        status = "completed" if self.system_initialized else "not completed"
                        print(f"[System] Initialization {status}")

            # 初始化完成查询响应
            elif command == 0x81:
                if data and len(data) > 0:
                    init_status = (data[0] == 0x01)
                    self.system_initialized = init_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_INIT_COMPLETE,
                        init_status,
                        "Init Complete"
                    )

        # 雷达探测范围 (0x07)
        elif control == 0x07:
            # 位置越界状态上报
            if command == 0x07:
                if data and len(data) > 0:
                    self.radar_in_range = (data[0] == 0x01)
                    if R60ABD1.DEBUG_ENABLED:
                        status = "in range" if self.radar_in_range else "out of range"
                        print(f"[Radar] {status}")

            # 位置越界状态查询响应
            elif command == 0x87:
                if data and len(data) > 0:
                    boundary_status = (data[0] == 0x01)
                    self.radar_in_range = not boundary_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_RADAR_RANGE_BOUNDARY,
                        boundary_status,
                        "Radar Range Boundary"
                    )

        # 人体存在检测 (0x80)
        elif control == 0x80:
            # 人体存在开关控制响应
            if command == 0x00:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.presence_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_HUMAN_PRESENCE_ON,
                            True,
                            "Human Presence ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_HUMAN_PRESENCE_OFF,
                            True,
                            "Human Presence OFF"
                        )

            # 存在信息
            if command == 0x01:
                if data and len(data) > 0:
                    self.presence_status = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = "No one" if self.presence_status == 0 else "Someone"
                        print(f"[Presence] {status_text}")

            # 人体存在开关查询响应
            elif command == 0x80:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.presence_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH,
                        switch_status,
                        "Human Presence Switch"
                    )

            # 存在信息（查询响应）
            elif command == 0x81:
                if data and len(data) > 0:
                    presence_value = data[0]
                    self.presence_status = presence_value
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HUMAN_EXISTENCE_INFO,
                        presence_value,
                        "Presence Status"
                    )

            # 运动信息查询响应
            elif command == 0x82:
                if data and len(data) > 0:
                    motion_value = data[0]
                    self.motion_status = motion_value
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HUMAN_MOTION_INFO,
                        motion_value,
                        "Human Motion Info"
                    )

            # 体动参数查询响应
            elif command == 0x83:
                if data and len(data) > 0:
                    motion_param = data[0]
                    self.movement_parameter = motion_param
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HUMAN_BODY_MOTION_PARAM,
                        motion_param,
                        "Body Motion Parameter"
                    )

            # 人体距离查询响应
            elif command == 0x84:
                if data and len(data) >= 2:
                    distance = (data[0] << 8) | data[1]
                    self.human_distance = distance
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HUMAN_DISTANCE,
                        distance,
                        "Human Distance"
                    )

            # 人体方位查询响应
            elif command == 0x85:
                if data and len(data) == 6:
                    x, y, z = self._parse_human_position_data(data)
                    self.human_position_x = x
                    self.human_position_y = y
                    self.human_position_z = z
                    position_data = (x, y, z)
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HUMAN_DIRECTION,
                        position_data,
                        "Human Direction"
                    )

            elif command == 0x02:  # 运动信息
                if data and len(data) > 0:
                    self.motion_status = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["No motion", "Static", "Active"][
                            self.motion_status] if self.motion_status < 3 else "Unknown"
                        print(f"[Motion] {status_text}")

            elif command == 0x03:  # 体动参数
                if data and len(data) > 0:
                    self.movement_parameter = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Movement] Parameter: {self.movement_parameter}")

            elif command == 0x04:  # 人体距离
                if data and len(data) >= 2:
                    self.human_distance = (data[0] << 8) | data[1]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Distance] {self.human_distance} cm")

            elif command == 0x05:  # 人体方位
                if data and len(data) == 6:
                    x, y, z = self._parse_human_position_data(data)
                    self.human_position_x = x
                    self.human_position_y = y
                    self.human_position_z = z
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Position] X={x}, Y={y}, Z={z}")

        # 呼吸监测 (0x81)
        elif control == 0x81:
            # 呼吸状态
            if command == 0x01:
                if data and len(data) > 0:
                    self.breath_status = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["Normal", "High", "Low", "None"][
                            self.breath_status - 1] if 1 <= self.breath_status <= 4 else "Unknown"
                        print(f"[Breath] Status: {status_text}")

            # 呼吸数值
            elif command == 0x02:
                if data and len(data) > 0:
                    self.breath_value = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Breath] Value: {self.breath_value}")

            # 呼吸波形
            elif command == 0x05:
                if data and len(data) == 5:
                    waveform = self._parse_breath_waveform_data(data)
                    self.breath_waveform = list(waveform)
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Breath] Waveform updated: {waveform}")

            # 呼吸监测开关控制响应
            elif command == 0x00:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.breath_monitoring_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_BREATH_MONITOR_ON,
                            True,
                            "Breath Monitor ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_BREATH_MONITOR_OFF,
                            True,
                            "Breath Monitor OFF"
                        )

            # 呼吸波形上报开关控制响应
            elif command == 0x0C:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.breath_waveform_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_BREATH_WAVEFORM_REPORT_ON,
                            True,
                            "Breath Waveform Report ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_BREATH_WAVEFORM_REPORT_OFF,
                            True,
                            "Breath Waveform Report OFF"
                        )

            # 低缓呼吸阈值设置响应
            elif command == 0x0B:
                if data and len(data) > 0:
                    threshold = data[0]
                    self.low_breath_threshold = threshold
                    self._handle_query_response(
                        R60ABD1.TYPE_SET_LOW_BREATH_THRESHOLD,
                        threshold,
                        "Set Low Breath Threshold"
                    )

            # 呼吸监测开关查询响应
            elif command == 0x80:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.breath_monitoring_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_BREATH_MONITOR_SWITCH,
                        switch_status,
                        "Breath Monitor Switch"
                    )

            # 低缓呼吸阈值查询响应
            elif command == 0x8B:
                if data and len(data) > 0:
                    threshold = data[0]
                    self.low_breath_threshold = threshold
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_LOW_BREATH_THRESHOLD,
                        threshold,
                        "Query Low Breath Threshold"
                    )

            # 呼吸信息查询响应
            elif command == 0x81:
                if data and len(data) > 0:
                    breath_status = data[0]
                    self.breath_status = breath_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_BREATH_INFO,
                        breath_status,
                        "Breath Info"
                    )

            # 呼吸数值查询响应
            elif command == 0x82:
                if data and len(data) > 0:
                    breath_value = data[0]
                    self.breath_value = breath_value
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_BREATH_VALUE,
                        breath_value,
                        "Breath Value"
                    )

            # 呼吸波形上报开关查询响应
            elif command == 0x8C:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.breath_waveform_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_BREATH_WAVEFORM_REPORT_SWITCH,
                        switch_status,
                        "Breath Waveform Report Switch"
                    )

            # 呼吸波形查询响应
            elif command == 0x85:
                if data and len(data) == 5:
                    waveform = self._parse_breath_waveform_data(data)
                    self.breath_waveform = list(waveform)
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_BREATH_WAVEFORM,
                        list(waveform),
                        "Breath Waveform"
                    )

        # 心率监测 (0x85)
        elif control == 0x85:
            # 心率数值
            if command == 0x02:
                if data and len(data) > 0:
                    self.heart_rate_value = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Heart Rate] Value: {self.heart_rate_value}")
            # 心率波形
            elif command == 0x05:
                if data and len(data) == 5:
                    waveform = self._parse_heart_rate_waveform_data(data)
                    self.heart_rate_waveform = list(waveform)
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Heart Rate] Waveform updated: {waveform}")
            # 心率监测开关控制响应
            elif command == 0x00:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.heart_rate_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_HEART_RATE_MONITOR_ON,
                            True,
                            "Heart Rate Monitor ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_HEART_RATE_MONITOR_OFF,
                            True,
                            "Heart Rate Monitor OFF"
                        )
            # 心率波形上报开关控制响应
            elif command == 0x0A:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.heart_rate_waveform_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_ON,
                            True,
                            "Heart Rate Waveform Report ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_HEART_RATE_WAVEFORM_REPORT_OFF,
                            True,
                            "Heart Rate Waveform Report OFF"
                        )
            # 心率监测开关查询响应
            elif command == 0x80:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.heart_rate_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HEART_RATE_MONITOR_SWITCH,
                        switch_status,
                        "Heart Rate Monitor Switch"
                    )
            # 心率波形上报开关查询响应
            elif command == 0x8A:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.heart_rate_waveform_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HEART_RATE_WAVEFORM_REPORT_SWITCH,
                        switch_status,
                        "Heart Rate Waveform Report Switch"
                    )
            # 心率数值查询响应
            elif command == 0x82:
                if data and len(data) > 0:
                    heart_rate = data[0]
                    self.heart_rate_value = heart_rate
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HEART_RATE_VALUE,
                        heart_rate,
                        "Heart Rate Value"
                    )
            # 心率波形查询响应
            elif command == 0x85:
                if data and len(data) == 5:
                    waveform = self._parse_heart_rate_waveform_data(data)
                    self.heart_rate_waveform = list(waveform)
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_HEART_RATE_WAVEFORM,
                        list(waveform),
                        "Heart Rate Waveform"
                    )
        # 睡眠监测 (0x84)
        elif control == 0x84:
            if command == 0x01:  # 入床/离床状态
                if data and len(data) > 0:
                    self.bed_status = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["Leave bed", "Enter bed", "None"][
                            self.bed_status] if self.bed_status < 3 else "Unknown"
                        print(f"[Bed] Status: {status_text}")

            elif command == 0x02:  # 睡眠状态
                if data and len(data) > 0:
                    self.sleep_status = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["Deep sleep", "Light sleep", "Awake", "None"][
                            self.sleep_status] if self.sleep_status < 4 else "Unknown"
                        print(f"[Sleep] Status: {status_text}")

            elif command == 0x03:  # 清醒时长
                if data and len(data) >= 2:
                    self.awake_duration = (data[0] << 8) | data[1]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Sleep] Awake duration: {self.awake_duration} min")

            elif command == 0x04:  # 浅睡时长
                if data and len(data) >= 2:
                    self.light_sleep_duration = (data[0] << 8) | data[1]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Sleep] Light sleep duration: {self.light_sleep_duration} min")

            elif command == 0x05:  # 深睡时长
                if data and len(data) >= 2:
                    self.deep_sleep_duration = (data[0] << 8) | data[1]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Sleep] Deep sleep duration: {self.deep_sleep_duration} min")

            elif command == 0x06:  # 睡眠质量评分
                if data and len(data) > 0:
                    self.sleep_quality_score = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Sleep] Quality score: {self.sleep_quality_score}")

            elif command == 0x0C:  # 睡眠综合状态
                if data and len(data) == 8:
                    comprehensive_data = self._parse_sleep_comprehensive_data(data)
                    # 更新到字典属性
                    self.sleep_comprehensive_status = {
                        'presence': comprehensive_data[0],
                        'sleep_status': comprehensive_data[1],
                        'avg_breath': comprehensive_data[2],
                        'avg_heart_rate': comprehensive_data[3],
                        'turnover_count': comprehensive_data[4],
                        'large_movement_ratio': comprehensive_data[5],
                        'small_movement_ratio': comprehensive_data[6],
                        'apnea_count': comprehensive_data[7]
                    }
                    if R60ABD1.DEBUG_ENABLED:
                        print(f"[Sleep] Comprehensive status updated")

            elif command == 0x0D:  # 睡眠质量分析/统计信息
                if data and len(data) == 12:
                    stats_data = self._parse_sleep_statistics_data(data)
                    # 更新对应的睡眠统计属性
                    self.sleep_quality_score = stats_data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        # 注意：stats_data[1]是总睡眠时长，需要根据实际情况决定如何分配
                        print(f"[Sleep] Statistics updated")

            elif command == 0x0E:  # 睡眠异常
                if data and len(data) > 0:
                    self.sleep_anomaly = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["Short sleep (<4h)", "Long sleep (>12h)", "No person anomaly", "Normal"][
                            self.sleep_anomaly] if self.sleep_anomaly < 4 else "Unknown"
                        print(f"[Sleep] Anomaly: {status_text}")

            elif command == 0x10:  # 睡眠质量评级
                if data and len(data) > 0:
                    self.sleep_quality_rating = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["None", "Good", "Normal", "Poor"][
                            self.sleep_quality_rating] if self.sleep_quality_rating < 4 else "Unknown"
                        print(f"[Sleep] Quality rating: {status_text}")

            elif command == 0x11:  # 异常挣扎状态
                if data and len(data) > 0:
                    self.abnormal_struggle_status = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["None", "Normal", "Abnormal"][
                            self.abnormal_struggle_status] if self.abnormal_struggle_status < 3 else "Unknown"
                        print(f"[Sleep] Struggle status: {status_text}")

            elif command == 0x12:  # 无人计时状态
                if data and len(data) > 0:
                    self.no_person_timing_status = data[0]
                    if R60ABD1.DEBUG_ENABLED:
                        status_text = ["None", "Normal", "Abnormal"][
                            self.no_person_timing_status] if self.no_person_timing_status < 3 else "Unknown"
                        print(f"[Sleep] No person timing: {status_text}")

            # 睡眠监测开关控制响应
            elif command == 0x00:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.sleep_monitoring_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_SLEEP_MONITOR_ON,
                            True,
                            "Sleep Monitor ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_SLEEP_MONITOR_OFF,
                            True,
                            "Sleep Monitor OFF"
                        )

            # 异常挣扎状态开关控制响应
            elif command == 0x13:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.abnormal_struggle_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_ABNORMAL_STRUGGLE_ON,
                            True,
                            "Abnormal Struggle Monitor ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_ABNORMAL_STRUGGLE_OFF,
                            True,
                            "Abnormal Struggle Monitor OFF"
                        )

            # 挣扎灵敏度设置响应
            elif command == 0x1A:
                if data and len(data) > 0:
                    sensitivity = data[0]
                    self.struggle_sensitivity = sensitivity
                    self._handle_query_response(
                        R60ABD1.TYPE_SET_STRUGGLE_SENSITIVITY,
                        sensitivity,
                        "Set Struggle Sensitivity"
                    )

            # 无人计时功能开关控制响应
            elif command == 0x14:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.no_person_timing_enabled = switch_status
                    # 根据数据内容判断是打开还是关闭操作
                    if data[0] == 0x01:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_NO_PERSON_TIMING_ON,
                            True,
                            "No Person Timing ON"
                        )
                    else:
                        self._handle_query_response(
                            R60ABD1.TYPE_CONTROL_NO_PERSON_TIMING_OFF,
                            True,
                            "No Person Timing OFF"
                        )

            # 无人计时时长设置响应
            elif command == 0x15:
                if data and len(data) > 0:
                    duration = data[0]
                    self.no_person_timing_duration = duration
                    self._handle_query_response(
                        R60ABD1.TYPE_SET_NO_PERSON_TIMING_DURATION,
                        duration,
                        "Set No Person Timing Duration"
                    )

            # 睡眠截止时长设置响应
            elif command == 0x16:
                if data and len(data) > 0:
                    duration = data[0]
                    self.sleep_cutoff_duration = duration
                    self._handle_query_response(
                        R60ABD1.TYPE_SET_SLEEP_END_DURATION,
                        duration,
                        "Set Sleep End Duration"
                    )

            # 睡眠监测开关查询响应
            elif command == 0x80:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.sleep_monitoring_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_MONITOR_SWITCH,
                        switch_status,
                        "Sleep Monitor Switch"
                    )

            # 异常挣扎状态开关查询响应
            elif command == 0x93:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.abnormal_struggle_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_ABNORMAL_STRUGGLE_SWITCH,
                        switch_status,
                        "Abnormal Struggle Monitor Switch"
                    )

            # 异常挣扎状态查询响应
            elif command == 0x91:
                if data and len(data) > 0:
                    struggle_status = data[0]
                    self.abnormal_struggle_status = struggle_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_ABNORMAL_STRUGGLE_STATUS,
                        struggle_status,
                        "Abnormal Struggle Status"
                    )

            # 挣扎灵敏度查询响应
            elif command == 0x9A:
                if data and len(data) > 0:
                    sensitivity = data[0]
                    self.struggle_sensitivity = sensitivity
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_STRUGGLE_SENSITIVITY,
                        sensitivity,
                        "Query Struggle Sensitivity"
                    )

            # 无人计时功能开关查询响应
            elif command == 0x94:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.no_person_timing_enabled = switch_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_SWITCH,
                        switch_status,
                        "No Person Timing Switch"
                    )

            # 无人计时时长查询响应
            elif command == 0x95:
                if data and len(data) > 0:
                    duration = data[0]
                    self.no_person_timing_duration = duration
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_DURATION,
                        duration,
                        "Query No Person Timing Duration"
                    )

            # 无人计时状态查询响应
            elif command == 0x92:
                if data and len(data) > 0:
                    timing_status = data[0]
                    self.no_person_timing_status = timing_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_NO_PERSON_TIMING_STATUS,
                        timing_status,
                        "No Person Timing Status"
                    )

            # 睡眠截止时长查询响应
            elif command == 0x96:
                if data and len(data) > 0:
                    duration = data[0]
                    self.sleep_cutoff_duration = duration
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_END_DURATION,
                        duration,
                        "Query Sleep End Duration"
                    )

            # 入床/离床状态查询响应
            elif command == 0x81:
                if data and len(data) > 0:
                    bed_status = data[0]
                    self.bed_status = bed_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_BED_STATUS,
                        bed_status,
                        "Bed Status"
                    )

            # 睡眠状态查询响应
            elif command == 0x82:
                if data and len(data) > 0:
                    sleep_status = data[0]
                    self.sleep_status = sleep_status
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_STATUS,
                        sleep_status,
                        "Sleep Status"
                    )

            # 清醒时长查询响应
            elif command == 0x83:
                if data and len(data) >= 2:
                    awake_duration = (data[0] << 8) | data[1]
                    self.awake_duration = awake_duration
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_AWAKE_DURATION,
                        awake_duration,
                        "Awake Duration"
                    )

            # 浅睡时长查询响应
            elif command == 0x84:
                if data and len(data) >= 2:
                    light_sleep_duration = (data[0] << 8) | data[1]
                    self.light_sleep_duration = light_sleep_duration
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_LIGHT_SLEEP_DURATION,
                        light_sleep_duration,
                        "Light Sleep Duration"
                    )

            # 深睡时长查询响应
            elif command == 0x85:
                if data and len(data) >= 2:
                    deep_sleep_duration = (data[0] << 8) | data[1]
                    self.deep_sleep_duration = deep_sleep_duration
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_DEEP_SLEEP_DURATION,
                        deep_sleep_duration,
                        "Deep Sleep Duration"
                    )

            # 睡眠质量评分查询响应
            elif command == 0x86:
                if data and len(data) > 0:
                    quality_score = data[0]
                    self.sleep_quality_score = quality_score
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_QUALITY_SCORE,
                        quality_score,
                        "Sleep Quality Score"
                    )

            # 睡眠综合状态查询响应
            elif command == 0x8D:
                if data and len(data) == 8:
                    comprehensive_data = self._parse_sleep_comprehensive_data(data)
                    self.sleep_comprehensive_status = {
                        'presence': comprehensive_data[0],
                        'sleep_status': comprehensive_data[1],
                        'avg_breath': comprehensive_data[2],
                        'avg_heart_rate': comprehensive_data[3],
                        'turnover_count': comprehensive_data[4],
                        'large_movement_ratio': comprehensive_data[5],
                        'small_movement_ratio': comprehensive_data[6],
                        'apnea_count': comprehensive_data[7]
                    }
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_COMPREHENSIVE_STATUS,
                        comprehensive_data,
                        "Sleep Comprehensive Status"
                    )

            # 睡眠异常查询响应
            elif command == 0x8E:
                if data and len(data) > 0:
                    sleep_anomaly = data[0]
                    self.sleep_anomaly = sleep_anomaly
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_ANOMALY,
                        sleep_anomaly,
                        "Sleep Anomaly"
                    )

            # 睡眠统计查询响应
            elif command == 0x8F:
                if data and len(data) == 12:
                    stats_data = self._parse_sleep_statistics_data(data)
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_STATISTICS,
                        stats_data,
                        "Sleep Statistics"
                    )

            # 睡眠质量评级查询响应
            elif command == 0x90:
                if data and len(data) > 0:
                    quality_level = data[0]
                    self.sleep_quality_rating = quality_level
                    self._handle_query_response(
                        R60ABD1.TYPE_QUERY_SLEEP_QUALITY_LEVEL,
                        quality_level,
                        "Sleep Quality Level"
                    )

    def close(self):
        """
        停止定时器，解析剩余数据帧，输出统计信息。

        Raises:
            Exception: 反初始化过程中发生错误。

        Note:
            - 停止定时器并设置运行状态为False。
            - 重置所有查询状态。
            - 解析剩余的数据帧。
            - 获取并输出最终统计信息。
            - 清空数据缓冲区。

        ==========================================

        Stop timer, parse remaining data frames, output statistics.

        Raises:
            Exception: Error occurred during deinitialization.

        Note:
            - Stop timer and set running status to False.
            - Reset all query status.
            - Parse remaining data frames.
            - Get and output final statistics.
            - Clear data buffer.
        """
        # 停止定时器
        self._is_running = False
        self._timer.deinit()

        # 是否有查询在进行中
        self._query_in_progress = False
        # 是否收到查询响应
        self._query_response_received = False
        # 查询结果
        self._query_result = None
        # 当前查询类型
        self._current_query_type = None

        # 解析剩余数据帧
        try:
            frames = self.data_processor.read_and_parse()
            for frame in frames:
                self.update_properties_from_frame(frame)
        except Exception as e:
            raise Exception(f"Failed to deinitialize timer: {str(e)}")

        # 获取并输出统计信息
        try:
            stats = self.data_processor.get_stats()
            if R60ABD1.DEBUG_ENABLED:
                print("  [R60ABD1] Final statistics: %s" % format_time())
                print("  Total bytes received: %d" % stats['total_bytes_received'])
                print("  Total frames parsed: %d" % stats['total_frames_parsed'])
                print("  CRC errors: %d" % stats['crc_errors'])
                print("  Frame errors: %d" % stats['frame_errors'])
                print("  Invalid frames: %d" % stats['invalid_frames'])
        except Exception as e:
            raise Exception(f"Failed to get statistics: {str(e)}")

        # 清空缓冲区
        try:
            self.data_processor.clear_buffer()
        except Exception as e:
            raise Exception(f"Failed to clear buffer: {str(e)}")

        if R60ABD1.DEBUG_ENABLED:
            print("%s [R60ABD1] Resources fully released" % format_time())

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================