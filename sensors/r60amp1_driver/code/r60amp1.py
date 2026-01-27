# -*- coding: utf-8 -*-
# @Time    : 2025/11/4 下午5:35
# @Author  : hogeiha
# @File    : r60amp1.py
# @Description : R60AMP1多人轨迹雷达设备业务处理类
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
        args (tuple): 传递给函数/位置参数。
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

    当R60AMP1设备初始化过程中发生严重错误时抛出。

    ==========================================

    Device initialization error exception class.

    Raised when critical errors occur during R60AMP1 device initialization.
    """
    pass


class R60AMP1:
    """
    R60AMP1多人轨迹雷达设备业务处理类。

    该类负责与R60AMP1多人轨迹雷达设备进行通信，管理设备状态，处理数据解析和业务逻辑。
    支持多人轨迹跟踪、人体存在检测、运动状态检测等多种功能。

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
        __init__(): 初始化R60AMP1实例。
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
        _parse_trajectory_data(): 解析轨迹数据。
        _parse_signed_16bit_special(): 解析有符号16位数据。
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
        enable_human_presence(): 打开人体存在功能。
        disable_human_presence(): 关闭人体存在功能。
        query_human_presence_switch(): 查询人体存在开关状态。
        query_presence_status(): 查询存在信息状态。
        query_motion_info(): 查询运动信息。
        query_body_motion_param(): 查询体动参数。
        query_trajectory_info(): 查询轨迹信息。
        _handle_query_response(): 统一处理查询响应。
        _update_property_with_debug(): 更新属性并输出调试信息。
        update_properties_from_frame(): 根据解析的帧更新属性值。
        close(): 停止定时器，解析剩余数据帧，输出统计信息。

    ==========================================

    R60AMP1 multi-person trajectory radar device business processing class.

    This class handles communication with R60AMP1 multi-person trajectory radar device, manages device status,
    processes data parsing and business logic. Supports various functions including
    multi-person trajectory tracking, human presence detection, motion status detection, etc.

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
        __init__(): Initialize R60AMP1 instance.
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
        _parse_trajectory_data(): Parse trajectory data.
        _parse_signed_16bit_special(): Parse signed 16-bit data.
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
        enable_human_presence(): Enable human presence detection.
        disable_human_presence(): Disable human presence detection.
        query_human_presence_switch(): Query human presence switch status.
        query_presence_status(): Query presence status information.
        query_motion_info(): Query motion information.
        query_body_motion_param(): Query body motion parameters.
        query_trajectory_info(): Query trajectory information.
        _handle_query_response(): Unified query response handling.
        _update_property_with_debug(): Update property with debug output.
        update_properties_from_frame(): Update properties from parsed frame.
        close(): Stop timer, parse remaining data frames, output statistics.
    """

    # 是否启用调试
    DEBUG_ENABLED = False

    # R60AMP1雷达设备业务处理类中各种状态值和配置选项的常量
    # 存在信息状态
    PRESENCE_NO_PERSON, PRESENCE_PERSON = (0x00, 0x01)
    # 运动信息状态
    MOTION_NONE, MOTION_STATIC, MOTION_ACTIVE = (0x00, 0x01, 0x02)
    # 目标特征状态
    TARGET_FEATURE_STATIC, TARGET_FEATURE_MOVING = (0x00, 0x01)
    # 雷达故障状态
    RADAR_FAULT_NONE, RADAR_FAULT_CHIP_ERROR, RADAR_FAULT_ENCRYPT_ERROR = (0x00, 0x01, 0x02)

    # R60AMP1雷达设备指令类型常量，用于标识不同的查询和控制操作
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
    # 雷达故障上传
    TYPE_RADAR_FAULT_UPLOAD = 7
    # 初始化完成信息上报
    TYPE_INIT_COMPLETE_UPLOAD = 8

    # 人体存在指令信息查询和设置类型
    # 打开人体存在功能
    TYPE_CONTROL_HUMAN_PRESENCE_ON = 9
    # 关闭人体存在功能
    TYPE_CONTROL_HUMAN_PRESENCE_OFF = 10
    # 查询人体存在开关状态
    TYPE_QUERY_HUMAN_PRESENCE_SWITCH = 11
    # 存在信息查询
    TYPE_QUERY_PRESENCE_STATUS = 12
    # 运动信息查询
    TYPE_QUERY_MOTION_INFO = 13
    # 体动参数查询
    TYPE_QUERY_BODY_MOTION_PARAM = 14
    # 存在信息主动上报
    TYPE_PRESENCE_STATUS_UPLOAD = 15
    # 运动信息主动上报
    TYPE_MOTION_INFO_UPLOAD = 16
    # 体动参数主动上报
    TYPE_BODY_MOTION_PARAM_UPLOAD = 17

    # 轨迹信息指令类型
    # 轨迹信息主动上报
    TYPE_TRAJECTORY_INFO_UPLOAD = 18
    # 轨迹信息查询
    TYPE_QUERY_TRAJECTORY_INFO = 19


    # 指令映射表 - 将查询、开关、设置类型指令的命令字和控制字的具体值映射到帧参数
    COMMAND_MAP = {
        # 基础指令信息查询和设置类型
        TYPE_QUERY_HEARTBEAT: {
            'control_byte': 0x01,  # 系统指令
            'command_byte': 0x01,  # 心跳包查询
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
            'control_byte': 0x05,  # 工作状态
            'command_byte': 0x81,  # 初始化完成查询
            'data': bytes([0x0F])  # 固定数据
        },

        # 人体存在指令信息查询和设置类型
        TYPE_CONTROL_HUMAN_PRESENCE_ON: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x00,  # 开关人体存在功能
            'data': bytes([0x01])  # 打开指令数据
        },
        TYPE_CONTROL_HUMAN_PRESENCE_OFF: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x00,  # 开关人体存在功能
            'data': bytes([0x00])  # 关闭指令数据
        },
        TYPE_QUERY_HUMAN_PRESENCE_SWITCH: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x80,  # 查询人体存在开关
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_PRESENCE_STATUS: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x81,  # 存在信息查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_MOTION_INFO: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x82,  # 运动信息查询
            'data': bytes([0x0F])  # 固定数据
        },
        TYPE_QUERY_BODY_MOTION_PARAM: {
            'control_byte': 0x80,  # 人体存在检测
            'command_byte': 0x83,  # 体动参数查询
            'data': bytes([0x0F])  # 固定数据
        },

        # 轨迹信息指令类型
        TYPE_QUERY_TRAJECTORY_INFO: {
            'control_byte': 0x82,  # 轨迹信息
            'command_byte': 0x82,  # 轨迹信息查询
            'data': bytes([0x0F])  # 固定数据
        },

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
        TYPE_RADAR_FAULT_UPLOAD: "Radar Fault Upload",
        TYPE_INIT_COMPLETE_UPLOAD: "Init Complete Upload",

        # 人体存在指令信息查询和设置
        TYPE_CONTROL_HUMAN_PRESENCE_ON: "Human Presence ON",
        TYPE_CONTROL_HUMAN_PRESENCE_OFF: "Human Presence OFF",
        TYPE_QUERY_HUMAN_PRESENCE_SWITCH: "Human Presence Switch",
        TYPE_QUERY_PRESENCE_STATUS: "Presence Status",
        TYPE_QUERY_MOTION_INFO: "Motion Info",
        TYPE_QUERY_BODY_MOTION_PARAM: "Body Motion Parameter",
        TYPE_PRESENCE_STATUS_UPLOAD: "Presence Status Upload",
        TYPE_MOTION_INFO_UPLOAD: "Motion Info Upload",
        TYPE_BODY_MOTION_PARAM_UPLOAD: "Body Motion Parameter Upload",

        # 轨迹信息指令
        TYPE_TRAJECTORY_INFO_UPLOAD: "Trajectory Info Upload",
        TYPE_QUERY_TRAJECTORY_INFO: "Trajectory Info Query"
    }

    def __init__(self, data_processor, parse_interval=200,
                 presence_enabled=True,
                 max_retries=3, retry_delay=100, init_timeout=5000):
        """
        初始化R60AMP1实例。

        Args:
            data_processor: DataFlowProcessor实例。
            parse_interval: 数据解析间隔，单位毫秒 (建议50-200ms)。
            presence_enabled: 是否开启人体存在信息监测。
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

        Initialize R60AMP1 instance.

        Args:
            data_processor: DataFlowProcessor instance.
            parse_interval: Data parsing interval in milliseconds (recommended 50-200ms).
            presence_enabled: Whether to enable human presence information monitoring.
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
            parse_interval, max_retries, retry_delay, init_timeout
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

        # 雷达故障状态
        # 0:正常, 1:雷达芯片异常, 2:加密异常
        self.radar_fault_status = 0
        # 雷达故障时间戳(ms)
        self.radar_fault_timestamp = 0
        # 场景默认(目前没有下发指令)
        self.environment_mode = 0
        # =========================== 人体存在检测属性 ==========================

        # 基本状态
        # 人体存在功能开关
        self.presence_enabled = presence_enabled
        # 存在状态: 0:无人, 1:有人
        self.presence_status = 0
        # 运动状态: 0:无, 1:静止, 2:活跃
        self.motion_status = 0

        # 量化数据
        # 体动参数(0-100)
        self.body_motion_param = 0

        # =========================== 轨迹信息属性 ==========================

        # 轨迹目标点列表
        # 每个目标点包含: 索引, 目标大小, 目标特征, X轴位置, Y轴位置, 高度, 速度
        self.trajectory_targets = []
        # 最后轨迹更新时间戳(ms)
        self.trajectory_last_update = 0

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

            if R60AMP1.DEBUG_ENABLED:
                print(f"[Init] R60AMP1 initialized successfully")
                status = self.get_configuration_status()
                print(f"[Init] Configuration errors: {len(status['configuration_errors'])}")
                print(f"[Init] Product: {self.product_model} v{self.firmware_version}")

        except Exception as e:
            # 初始化失败，停止定时器
            self._is_running = False
            if hasattr(self, '_timer'):
                self._timer.deinit()
            raise DeviceInitializationError(f"Device initialization failed: {str(e)}")

    def _validate_init_parameters(self, parse_interval,
                                  max_retries, retry_delay, init_timeout):
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
        """
        if parse_interval > 500 or parse_interval < 10:
            raise ValueError("parse_interval must be between 10ms and 500ms")

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
            if R60AMP1.DEBUG_ENABLED:
                print("[Init] Device not initialized, attempting reset...")
            reset_success = self._reset_and_wait_for_initialization()
            if not reset_success:
                raise DeviceInitializationError("Device initialization failed even after reset")

        # 步骤3: 配置设备功能
        self._auto_configure_device()

        # 步骤4: 验证关键功能配置
        self._verify_critical_configuration()

        elapsed_time = time.ticks_diff(time.ticks_ms(), start_time)
        if R60AMP1.DEBUG_ENABLED:
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
                if R60AMP1.DEBUG_ENABLED:
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
                if R60AMP1.DEBUG_ENABLED:
                    print("[Init] Device initialization confirmed")
                return True

            # 短暂延迟后重试
            time.sleep_ms(200)

        if R60AMP1.DEBUG_ENABLED:
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
        if R60AMP1.DEBUG_ENABLED:
            print("[Init] Waiting 3 seconds for device reset...")
        time.sleep(3)

        # 重新等待初始化完成
        return self._wait_for_device_initialization(timeout=10000)  # 10秒超时

    def _auto_configure_device(self):
        """
        自动配置设备功能。

        Note:
            - 根据初始化参数配置各功能模块。
            - 包括人体存在功能配置。
            - 每个配置步骤失败都会记录错误信息。

        ==========================================

        Auto-configure device functions.

        Note:
            - Configure each function module based on initialization parameters.
            - Includes human presence function configuration.
            - Each configuration step failure records error information.
        """
        configuration_steps = []

        # 基础功能配置
        if self.presence_enabled:
            configuration_steps.append(("Enable Human Presence", self.enable_human_presence))
        else:
            configuration_steps.append(("Disable Human Presence", self.disable_human_presence))

        # 执行配置步骤
        for step_name, step_function in configuration_steps:
            success = self._execute_with_retry(step_function, step_name)
            if not success:
                self._configuration_errors.append(f"Failed to {step_name}")
                if R60AMP1.DEBUG_ENABLED:
                    print(f"[Init] Warning: {step_name} failed")

    def _verify_critical_configuration(self):
        """
        验证关键配置是否成功。

        Note:
            - 验证设备初始化状态。
            - 根据启用的功能验证相应模块的开关状态。
            - 验证失败会记录到配置错误列表中。

        ==========================================

        Verify critical configuration success.

        Note:
            - Verify device initialization status.
            - Verify switch status of corresponding modules based on enabled functions.
            - Verification failures are recorded in configuration errors list.
        """
        critical_verifications = []

        # 验证设备初始化状态
        critical_verifications.append(("Device Initialization", self.query_init_complete))

        # 根据启用的功能添加验证
        if self.presence_enabled:
            critical_verifications.append(("Presence Detection", self.query_human_presence_switch))

        # 执行验证
        for verify_name, verify_func in critical_verifications:
            success, result = verify_func(timeout=500)
            if not success:
                self._configuration_errors.append(f"Verification failed: {verify_name}")
                if R60AMP1.DEBUG_ENABLED:
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
                    if R60AMP1.DEBUG_ENABLED:
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

    def _parse_trajectory_data(self, data_bytes):
        """
        解析轨迹数据。

        Args:
            data_bytes: 轨迹数据字节。

        Returns:
            list: 轨迹目标点列表，每个目标点是一个字典。

        Note:
            - 每个目标点: 1B索引, 1B目标大小, 1B目标特征, 2BX轴位置, 2BY轴位置, 2B高度, 2B速度
            - X轴数据: -32767 cm ~ 32767 cm
            - Y轴数据: -32767 cm ~ 32767 cm
            - 高度数据: 0 cm ~ 65535 cm
            - 速度: -32767 cm/s ~ 32767 cm/s，靠近为正，远离为负

        ==========================================

        Parse trajectory data.

        Args:
            data_bytes: Trajectory data bytes.

        Returns:
            list: Trajectory target points list, each target point is a dictionary.

        Note:
            - Each target point: 1B index, 1B target size, 1B target feature, 2B X position, 2B Y position, 2B height, 2B speed
            - X axis data: -32767 cm ~ 32767 cm
            - Y axis data: -32767 cm ~ 32767 cm
            - Height data: 0 cm ~ 65535 cm
            - Speed: -32767 cm/s ~ 32767 cm/s, positive for approaching, negative for moving away
        """
        targets = []
        data_len = len(data_bytes)

        # 每个目标点占用11字节
        target_size = 11

        for i in range(0, data_len, target_size):
            if i + target_size > data_len:
                break

            target_data = data_bytes[i:i + target_size]

            target = {
                'index': target_data[0],  # 1B索引
                'size': target_data[1],  # 1B目标大小: 0-100
                'feature': target_data[2],  # 1B目标特征: 0x00静止, 0x01运动
                'x': self._parse_signed_16bit_special(target_data[3:5]),  # 2B X轴位置
                'y': self._parse_signed_16bit_special(target_data[5:7]),  # 2B Y轴位置
                'height': (target_data[7] << 8) | target_data[8],  # 2B高度
                'speed': self._parse_signed_16bit_special(target_data[9:11])  # 2B速度
            }

            targets.append(target)

        return targets

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
        magnitude = unsigned_value & 0x7FFF  # 低15位为数值

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
            if R60AMP1.DEBUG_ENABLED:
                print(f"[Parse] Raw product data: {data_bytes}, hex: {data_bytes.hex()}")

            # 找到第一个空字节的位置，截取有效部分
            if b'\x00' in data_bytes:
                # 找到第一个空字节，截取之前的部分
                null_index = data_bytes.index(b'\x00')
                valid_data = data_bytes[:null_index]
                if R60AMP1.DEBUG_ENABLED:
                    print(f"[Parse] After null removal: {valid_data}, hex: {valid_data.hex()}")
            else:
                valid_data = data_bytes

            # 解码为字符串
            product_info = valid_data.decode('utf-8').strip()
            if R60AMP1.DEBUG_ENABLED:
                print(f"[Parse] Decoded product info: '{product_info}'")

            return (product_info,)
        except Exception as e:
            # 如果解码失败，尝试其他方式
            if R60AMP1.DEBUG_ENABLED:
                print(f"[Parse] Product info parse error: {e}, data: {data_bytes}")

            # 尝试使用 ascii 解码作为备选方案
            try:
                product_info = valid_data.decode('ascii').strip()
                if R60AMP1.DEBUG_ENABLED:
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
            if R60AMP1.DEBUG_ENABLED:
                print(f"[Parse] Raw firmware data: {data_bytes}, hex: {data_bytes.hex()}")

            # 找到第一个空字节的位置，截取有效部分
            if b'\x00' in data_bytes:
                # 找到第一个空字节，截取之前的部分
                null_index = data_bytes.index(b'\x00')
                valid_data = data_bytes[:null_index]
                if R60AMP1.DEBUG_ENABLED:
                    print(f"[Parse] After null removal: {valid_data}, hex: {valid_data.hex()}")
            else:
                valid_data = data_bytes

            # 解码为字符串
            version = valid_data.decode('utf-8').strip()
            if R60AMP1.DEBUG_ENABLED:
                print(f"[Parse] Decoded firmware version: '{version}'")

            return (version,)
        except Exception as e:
            # 如果解码失败，尝试其他方式
            if R60AMP1.DEBUG_ENABLED:
                print(f"[Parse] Firmware version parse error: {e}, data: {data_bytes}")

            # 尝试使用 ascii 解码作为备选方案
            try:
                version = valid_data.decode('ascii').strip()
                if R60AMP1.DEBUG_ENABLED:
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
            if R60AMP1.DEBUG_ENABLED:
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
                if R60AMP1.DEBUG_ENABLED:
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
            if R60AMP1.DEBUG_ENABLED:
                operation_name = self.QUERY_NAME_MAP.get(operation_type, f"Unknown({operation_type})")
                print(f"[Operation] {operation_name} operation sent")
                frame_hex = ' '.join(['{:02X}'.format(b) for b in operation_frame])
                print(f"[Operation] Sent frame: {frame_hex}")

            # 等待设备响应
            start_time = time.ticks_ms()
            while not self._query_response_received:
                # 检查超时
                if time.ticks_diff(time.ticks_ms(), start_time) >= timeout:
                    if R60AMP1.DEBUG_ENABLED:
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
            if R60AMP1.DEBUG_ENABLED:
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

            if R60AMP1.DEBUG_ENABLED:
                print("[Operation] Operation state reset")

    def query_heartbeat(self, timeout=200):
        """
        查询心跳包（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 心跳状态)
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_HEARTBEAT, timeout=timeout)

    def reset_module(self, timeout=500):
        """
        模组复位（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 复位结果)
        """
        return self._execute_operation(R60AMP1.TYPE_MODULE_RESET, timeout=timeout)

    def query_product_model(self, timeout=200):
        """
        查询产品型号（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 产品型号)
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_PRODUCT_MODEL, timeout=timeout)

    def query_product_id(self, timeout=200):
        """
        查询产品ID（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 产品ID)
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_PRODUCT_ID, timeout=timeout)

    def query_hardware_model(self, timeout=200):
        """
        查询硬件型号（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 硬件型号)
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_HARDWARE_MODEL, timeout=timeout)

    def query_firmware_version(self, timeout=200):
        """
        查询固件版本（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 固件版本)
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_FIRMWARE_VERSION, timeout=timeout)

    def query_init_complete(self, timeout=200):
        """
        查询初始化是否完成（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 初始化状态)
                    - 初始化状态: True-完成, False-未完成
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_INIT_COMPLETE, timeout=timeout)

    def enable_human_presence(self, timeout=200):
        """
        打开人体存在功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60AMP1.TYPE_CONTROL_HUMAN_PRESENCE_ON, timeout=timeout)

    def disable_human_presence(self, timeout=200):
        """
        关闭人体存在功能（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 实际执行结果)
        """
        return self._execute_operation(R60AMP1.TYPE_CONTROL_HUMAN_PRESENCE_OFF, timeout=timeout)

    def query_human_presence_switch(self, timeout=200):
        """
        查询人体存在开关状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 开关状态)
                    - 开关状态: True-开启, False-关闭
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH, timeout=timeout)

    def query_presence_status(self, timeout=200):
        """
        查询存在信息状态（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 存在状态)
                    - 存在状态: 必须是 R60AMP1.PRESENCE_NO_PERSON, R60AMP1.PRESENCE_PERSON 中的一个
        """
        success, presence_status = self._execute_operation(
            R60AMP1.TYPE_QUERY_PRESENCE_STATUS,
            timeout=timeout
        )
        # 验证返回的存在状态是否有效
        if success and presence_status not in (R60AMP1.PRESENCE_NO_PERSON, R60AMP1.PRESENCE_PERSON):
            raise ValueError(f"Invalid presence status: {presence_status}")

        return success, presence_status

    def query_motion_info(self, timeout=200):
        """
        查询运动信息（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 运动状态)
                    - 运动状态: 必须是 R60AMP1.MOTION_NONE, R60AMP1.MOTION_STATIC, R60AMP1.MOTION_ACTIVE 中的一个
        """
        success, motion_status = self._execute_operation(
            R60AMP1.TYPE_QUERY_MOTION_INFO,
            timeout=timeout
        )
        # 验证返回的运动状态是否有效
        if success and motion_status not in (R60AMP1.MOTION_NONE, R60AMP1.MOTION_STATIC, R60AMP1.MOTION_ACTIVE):
            raise ValueError(f"Invalid motion status: {motion_status}")

        return success, motion_status

    def query_body_motion_param(self, timeout=200):
        """
        查询体动参数（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 体动参数值)
                    - 体动参数值: 0-100
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_BODY_MOTION_PARAM, timeout=timeout)

    def query_trajectory_info(self, timeout=200):
        """
        查询轨迹信息（阻塞式）

        Args:
            timeout: 超时时间，单位毫秒

        Returns:
            tuple: (指令发送成功状态, 轨迹目标点列表)
                    - 轨迹目标点列表: 每个目标点包含索引、大小、特征、X/Y位置、高度、速度
        """
        return self._execute_operation(R60AMP1.TYPE_QUERY_TRAJECTORY_INFO, timeout=timeout)

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

            if R60AMP1.DEBUG_ENABLED:
                query_name = self.QUERY_NAME_MAP.get(expected_type, f"Unknown({expected_type})")
                print(f"[Query] {query_name} response received: {response_data}")

        # 情况2：当前正在进行其他类型的查询，但收到了本响应
        elif self._query_in_progress and self._current_query_type != expected_type:
            if R60AMP1.DEBUG_ENABLED:
                current_query = self.QUERY_NAME_MAP.get(self._current_query_type,
                                                        f"Unknown({self._current_query_type})")
                print(f"[Query] Unexpected {response_name} response during {current_query} query: {response_data}")

        # 情况3：没有查询在进行，但收到了查询响应
        elif not self._query_in_progress:
            if R60AMP1.DEBUG_ENABLED:
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
        if R60AMP1.DEBUG_ENABLED:
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

        # 系统功能 (0x01)
        if control == 0x01:
            # 心跳包查询响应
            if command == 0x01:
                self.heartbeat_last_received = time.ticks_ms()
                self._handle_query_response(
                    R60AMP1.TYPE_QUERY_HEARTBEAT,
                    True,
                    "Heartbeat"
                )

            # 模组复位响应
            elif command == 0x02:
                self.module_reset_flag = True
                self.module_reset_timestamp = time.ticks_ms()
                self._handle_query_response(
                    R60AMP1.TYPE_MODULE_RESET,
                    True,
                    "Module Reset"
                )

        # 产品信息 (0x02)
        elif control == 0x02:
            # 产品型号查询响应
            if command == 0xA1:
                if data:
                    product_info = self._parse_product_info_data(data)[0]
                    self.product_model = product_info
                    self._handle_query_response(
                        R60AMP1.TYPE_QUERY_PRODUCT_MODEL,
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
                        R60AMP1.TYPE_QUERY_PRODUCT_ID,
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
                        R60AMP1.TYPE_QUERY_HARDWARE_MODEL,
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
                        R60AMP1.TYPE_QUERY_FIRMWARE_VERSION,
                        firmware_version,
                        "Firmware Version"
                    )

        # 工作状态 (0x05)
        elif control == 0x05:
            # 初始化完成信息上报
            if command == 0x01:
                if data and len(data) > 0:
                    self.system_initialized = (data[0] == 0x0F)
                    self.system_initialized_timestamp = time.ticks_ms()
                    if R60AMP1.DEBUG_ENABLED:
                        status = "completed" if self.system_initialized else "not completed"
                        print(f"[System] Initialization {status}")

            # 雷达故障上传
            elif command == 0x02:
                if data and len(data) > 0:
                    fault_code = data[0]
                    self.radar_fault_status = fault_code
                    self.radar_fault_timestamp = time.ticks_ms()
                    if R60AMP1.DEBUG_ENABLED:
                        fault_text = ["None", "Radar chip error", "Encryption error"][
                            fault_code] if fault_code < 3 else "Unknown"
                        print(f"[System] Radar fault: {fault_text}")
            # 在数据手册中有一个没有下发的回复
            # 对应数值：00:默认 01:客厅 02：卧室 03:洗手间
            elif command == 0x07:
                if data and len(data) > 0:
                    env_mode = data[0]
                    self.environment_mode = env_mode
                    if R60AMP1.DEBUG_ENABLED:
                        mode_text = ["Default", "Living Room", "Bedroom", "Bathroom"][
                            env_mode] if env_mode < 4 else "Unknown"
                        print(f"[System] Environment mode: {mode_text}")

            # 初始化完成查询响应
            elif command == 0x81:
                if data and len(data) > 0:
                    init_status = (data[0] == 0x01)
                    self.system_initialized = init_status
                    self._handle_query_response(
                        R60AMP1.TYPE_QUERY_INIT_COMPLETE,
                        init_status,
                        "Init Complete"
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
                            R60AMP1.TYPE_CONTROL_HUMAN_PRESENCE_ON,
                            True,
                            "Human Presence ON"
                        )
                    else:
                        self._handle_query_response(
                            R60AMP1.TYPE_CONTROL_HUMAN_PRESENCE_OFF,
                            True,
                            "Human Presence OFF"
                        )

            # 存在信息主动上报
            elif command == 0x01:
                if data and len(data) > 0:
                    self.presence_status = data[0]
                    if R60AMP1.DEBUG_ENABLED:
                        status_text = "No one" if self.presence_status == 0 else "Someone"
                        print(f"[Presence] {status_text}")

            # 运动信息主动上报
            elif command == 0x02:
                if data and len(data) > 0:
                    self.motion_status = data[0]
                    if R60AMP1.DEBUG_ENABLED:
                        status_text = ["No motion", "Static", "Active"][
                            self.motion_status] if self.motion_status < 3 else "Unknown"
                        print(f"[Motion] {status_text}")

            # 体动参数主动上报
            elif command == 0x03:
                if data and len(data) > 0:
                    self.body_motion_param = data[0]
                    if R60AMP1.DEBUG_ENABLED:
                        print(f"[Body Motion] Parameter: {self.body_motion_param}")

            # 人体存在开关查询响应
            elif command == 0x80:
                if data and len(data) > 0:
                    switch_status = (data[0] == 0x01)
                    self.presence_enabled = switch_status
                    self._handle_query_response(
                        R60AMP1.TYPE_QUERY_HUMAN_PRESENCE_SWITCH,
                        switch_status,
                        "Human Presence Switch"
                    )

            # 存在信息查询响应
            elif command == 0x81:
                if data and len(data) > 0:
                    presence_value = data[0]
                    self.presence_status = presence_value
                    self._handle_query_response(
                        R60AMP1.TYPE_QUERY_PRESENCE_STATUS,
                        presence_value,
                        "Presence Status"
                    )

            # 运动信息查询响应
            elif command == 0x82:
                if data and len(data) > 0:
                    motion_value = data[0]
                    self.motion_status = motion_value
                    self._handle_query_response(
                        R60AMP1.TYPE_QUERY_MOTION_INFO,
                        motion_value,
                        "Motion Info"
                    )

            # 体动参数查询响应
            elif command == 0x83:
                if data and len(data) > 0:
                    motion_param = data[0]
                    self.body_motion_param = motion_param
                    self._handle_query_response(
                        R60AMP1.TYPE_QUERY_BODY_MOTION_PARAM,
                        motion_param,
                        "Body Motion Parameter"
                    )

        # 轨迹信息 (0x82)
        elif control == 0x82:
            # 轨迹信息主动上报
            if command == 0x02:
                if data and len(data) > 0:
                    targets = self._parse_trajectory_data(data)
                    self.trajectory_targets = targets
                    self.trajectory_last_update = time.ticks_ms()
                    if R60AMP1.DEBUG_ENABLED:
                        print(f"[Trajectory] {len(targets)} target(s) updated")

            # 轨迹信息查询响应
            elif command == 0x82:
                if data and len(data) > 0:
                    targets = self._parse_trajectory_data(data)
                    self.trajectory_targets = targets
                    self._handle_query_response(
                        R60AMP1.TYPE_QUERY_TRAJECTORY_INFO,
                        targets,
                        "Trajectory Info"
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
            if R60AMP1.DEBUG_ENABLED:
                print("  [R60AMP1] Final statistics: %s" % format_time())
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

        if R60AMP1.DEBUG_ENABLED:
            print("%s [R60AMP1] Resources fully released" % format_time())

# ======================================== 初始化配置 ==========================================

# ========================================  主程序  ===========================================
