# Python env   : MicroPython v1.23.0
# -*- coding: utf-8 -*-
# @Time    : 2025/9/8 下午11:00
# @Author  : basanovase
# @File    : location.py
# @Description : SIM7600模块GPS/LBS定位功能类 实现网络启停、基站定位、经纬度与时间获取等功能 参考自：https://github.com/basanovase/sim7600
# @License : MIT
__version__ = "1.0.0"
__author__ = "hogeiha"
__license__ = "MIT"
__platform__ = "MicroPython v1.23.0"

# ======================================== 导入相关模块 =========================================

# ======================================== 全局变量 ============================================

# ======================================== 功能函数 ============================================

# ======================================== 自定义类 ============================================


class LBS:
    """
    SIM7600模块GPS/LBS定位功能类
    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command、write_uart、read_uart方法

    Methods:
        __init__(sim7600): 初始化GPS/LBS定位功能类
        start_network(): 打开网络承载，为定位服务提供网络基础
        stop_network(): 关闭网络承载，释放定位相关网络资源
        get_lbs_coords(command): 获取基站定位经纬度信息
        get_lbs_full(command): 获取基站定位经纬度及对应的日期时间信息

    Notes:
        所有定位功能依赖SIM7600核心对象的AT指令发送能力，使用前需确保网络承载已激活

    ==========================================
    SIM7600 Module GPS/LBS Positioning Function Class
    Attributes:
        sim7600 (object): SIM7600 module core object, must contain send_command, write_uart, read_uart methods

    Methods:
        __init__(sim7600): Initialize GPS/LBS positioning function class
        start_network(): Open network bearer to provide network foundation for positioning services
        stop_network(): Close network bearer and release positioning-related network resources
        get_lbs_coords(command): Obtain base station positioning latitude and longitude information
        get_lbs_full(command): Obtain base station positioning latitude, longitude and corresponding date and time information

    Notes:
        All positioning functions depend on the AT command sending capability of the SIM7600 core object, ensure the network bearer is activated before use
    """

    def __init__(self, sim7600: object) -> None:
        """
        初始化GPS/LBS定位功能类
        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command、write_uart、read_uart方法

        Raises:
            TypeError: 当sim7600参数为None时触发
            AttributeError: 当sim7600对象缺少必要方法（send_command/write_uart/read_uart）时触发

        Notes:
            依赖SIM7600核心对象提供的AT指令发送和UART读写方法完成定位通信

        ==========================================
        Initialize GPS/LBS positioning function class
        Args:
            sim7600 (object): SIM7600 module core object, must implement send_command, write_uart, read_uart methods

        Raises:
            TypeError: Triggered when sim7600 parameter is None
            AttributeError: Triggered when sim7600 object lacks necessary methods (send_command/write_uart/read_uart)

        Notes:
            Depends on AT command sending and UART read/write methods provided by SIM7600 core object to complete positioning communication
        """
        # 检查sim7600参数是否为None
        if sim7600 is None:
            raise TypeError("sim7600 parameter cannot be None")
        # 检查sim7600对象是否包含必要方法
        required_methods = ["send_command", "write_uart", "read_uart"]
        for method in required_methods:
            if not hasattr(sim7600, method) or not callable(getattr(sim7600, method)):
                raise AttributeError(f"sim7600 object must implement {method} method")
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def start_network(self) -> str:
        """
        打开网络承载，为定位服务提供网络基础
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CNETSTART指令激活网络承载，需在获取定位前调用
            指令默认超时时间为10000ms，确保网络有足够时间完成激活

        ==========================================
        Open network bearer to provide network foundation for positioning services
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CNETSTART command to activate network bearer, must be called before obtaining positioning
            The default command timeout is 10000ms to ensure the network has enough time to complete activation
        """
        # 发送激活网络承载指令并返回响应
        return self.sim7600.send_command("AT+CNETSTART")

    def stop_network(self) -> str:
        """
        关闭网络承载，释放定位相关网络资源
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CNETSTOP指令终止网络承载，定位完成后建议调用以节省功耗
            指令默认超时时间为10000ms，确保网络有足够时间完成终止

        ==========================================
        Close network bearer and release positioning-related network resources
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CNETSTOP command to terminate network bearer, recommended to call after positioning to save power
            The default command timeout is 10000ms to ensure the network has enough time to complete termination
        """
        # 发送终止网络承载指令并返回响应
        return self.sim7600.send_command("AT+CNETSTOP")

    def get_lbs_coords(self, command: int) -> str:
        """
        获取基站定位经纬度信息
        Args:
            command (int): CLBS指令参数，1表示仅获取经纬度信息

        Raises:
            TypeError: 当command参数非整数类型时触发
            ValueError: 当command参数小于0时触发

        Notes:
            使用AT+CLBS={command}指令获取基站定位的经纬度信息
            需先调用start_network()激活网络，否则定位请求会失败
            指令默认超时时间为10000ms，确保定位数据有足够时间返回

        ==========================================
        Obtain base station positioning latitude and longitude information
        Args:
            command (int): CLBS command parameter, 1 means only get latitude and longitude information

        Raises:
            TypeError: Triggered when command parameter is not integer type
            ValueError: Triggered when command parameter is less than 0

        Notes:
            Use AT+CLBS={command} command to obtain latitude and longitude information of base station positioning
            Must call start_network() to activate network first, otherwise positioning request will fail
            The default command timeout is 10000ms to ensure positioning data has enough time to return
        """
        # 检查command参数类型和有效性
        if not isinstance(command, int):
            raise TypeError("command parameter must be integer type")
        if command < 0:
            raise ValueError("command parameter must be greater than or equal to 0")
        # 发送获取经纬度指令并返回响应
        return self.sim7600.send_command(f"AT+CLBS={command}")

    def get_lbs_full(self, command: int) -> str:
        """
        获取基站定位经纬度及对应的日期时间信息
        Args:
            command (int): CLBS指令参数，4表示获取经纬度及日期时间信息

        Raises:
            TypeError: 当command参数非整数类型时触发
            ValueError: 当command参数小于0时触发

        Notes:
            使用AT+CLBS={command}指令获取基站定位的经纬度及日期时间信息
            需先调用start_network()激活网络，否则定位请求会失败
            指令默认超时时间为10000ms，确保定位数据有足够时间返回

        ==========================================
        Obtain base station positioning latitude, longitude and corresponding date and time information
        Args:
            command (int): CLBS command parameter, 4 means get latitude, longitude and date/time information

        Raises:
            TypeError: Triggered when command parameter is not integer type
            ValueError: Triggered when command parameter is less than 0

        Notes:
            Use AT+CLBS={command} command to obtain latitude, longitude and date/time information of base station positioning
            Must call start_network() to activate network first, otherwise positioning request will fail
            The default command timeout is 10000ms to ensure positioning data has enough time to return
        """
        # 检查command参数类型和有效性
        if not isinstance(command, int):
            raise TypeError("command parameter must be integer type")
        if command < 0:
            raise ValueError("command parameter must be greater than or equal to 0")
        # 发送获取经纬度及时间指令并返回响应
        return self.sim7600.send_command(f"AT+CLBS={command}")


class GPS:
    """
    SIM7600模块GPS/北斗卫星定位功能类
    Attributes:
        sim7600 (object): SIM7600模块核心对象，需包含send_command方法

    Methods:
        __init__(sim7600): 初始化GPS定位功能类
        disable_gps(): 关闭GPS模块
        set_satellite_beidou(): 选择仅北斗卫星系统
        set_satellite_all(): 选择全部卫星系统（GPS+北斗+GLONASS等）
        set_satellite_custom(): 自定义卫星系统选择（示例值：197119）
        enable_gps(): 打开GPS模块
        start_search_satellite(): 开始搜索卫星
        get_gps_info(): 查询GPS相关信息（定位状态、卫星数、经纬度等）

    Notes:
        GPS定位功能需要模块硬件支持GPS/北斗接收，且需在开阔环境下搜星
        卫星系统选择指令参数需根据模块固件版本确认有效性

    ==========================================
    SIM7600 Module GPS/Beidou Satellite Positioning Function Class
    Attributes:
        sim7600 (object): SIM7600 module core object, must contain send_command method

    Methods:
        __init__(sim7600): Initialize GPS positioning function class
        disable_gps(): Disable GPS module
        set_satellite_beidou(): Select Beidou satellite system only
        set_satellite_all(): Select all satellite systems (GPS+Beidou+GLONASS etc.)
        set_satellite_custom(): Custom satellite system selection (example value: 197119)
        enable_gps(): Enable GPS module
        start_search_satellite(): Start searching for satellites
        get_gps_info(): Query GPS related information (positioning status, satellite count, latitude/longitude etc.)

    Notes:
        GPS positioning function requires the module hardware to support GPS/Beidou reception, and needs to search for satellites in an open environment
        The satellite system selection command parameters need to be validated according to the module firmware version
    """

    def __init__(self, sim7600: object) -> None:
        """
        初始化GPS定位功能类
        Args:
            sim7600 (object): SIM7600模块核心对象，需实现send_command方法

        Raises:
            TypeError: 当sim7600参数为None时触发
            AttributeError: 当sim7600对象缺少send_command方法时触发

        Notes:
            依赖SIM7600核心对象提供的AT指令发送方法完成GPS定位相关通信

        ==========================================
        Initialize GPS positioning function class
        Args:
            sim7600 (object): SIM7600 module core object, must implement send_command method

        Raises:
            TypeError: Triggered when sim7600 parameter is None
            AttributeError: Triggered when sim7600 object lacks send_command method

        Notes:
            Depends on the AT command sending method provided by the SIM7600 core object to complete GPS positioning related communication
        """
        # 检查sim7600参数是否为None
        if sim7600 is None:
            raise TypeError("sim7600 parameter cannot be None")
        # 检查sim7600对象是否包含send_command方法
        if not hasattr(sim7600, "send_command") or not callable(getattr(sim7600, "send_command")):
            raise AttributeError("sim7600 object must implement send_command method")
        # 保存SIM7600模块核心对象引用
        self.sim7600 = sim7600

    def disable_gps(self) -> str:
        """
        关闭GPS模块
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGPS=0指令关闭GPS模块，关闭后停止卫星定位功能

        ==========================================
        Disable GPS module
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGPS=0 command to disable GPS module, stop satellite positioning function after disabling
        """
        # 发送关闭GPS模块指令并返回响应
        return self.sim7600.send_command("AT+CGPS=0")

    def set_satellite_beidou(self) -> str:
        """
        选择仅北斗卫星系统
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGPSNMEA=196608指令设置仅使用北斗卫星系统
            需在开启GPS前配置，配置后需重启GPS生效

        ==========================================
        Select Beidou satellite system only
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGPSNMEA=196608 command to set to use only Beidou satellite system
            Must be configured before enabling GPS, need to restart GPS to take effect after configuration
        """
        # 发送选择北斗卫星系统指令并返回响应
        return self.sim7600.send_command("AT+CGPSNMEA=196608")

    def set_satellite_all(self) -> str:
        """
        选择全部卫星系统（GPS+北斗+GLONASS等）
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGPSNMEA=198143指令设置使用全部卫星系统
            需在开启GPS前配置，配置后需重启GPS生效
            多系统定位可提高搜星速度和定位精度

        ==========================================
        Select all satellite systems (GPS+Beidou+GLONASS etc.)
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGPSNMEA=198143 command to set to use all satellite systems
            Must be configured before enabling GPS, need to restart GPS to take effect after configuration
            Multi-system positioning can improve satellite search speed and positioning accuracy
        """
        # 发送选择全部卫星系统指令并返回响应
        return self.sim7600.send_command("AT+CGPSNMEA=198143")

    def set_satellite_custom(self) -> str:
        """
        自定义卫星系统选择（示例值：197119）
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGPSNMEA=197119指令自定义卫星系统选择
            指令超时时间设置为5000ms，适配自定义配置的响应速度
            需在开启GPS前配置，配置后需重启GPS生效

        ==========================================
        Custom satellite system selection (example value: 197119)
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGPSNMEA=197119 command for custom satellite system selection
            The command timeout is set to 5000ms to adapt to the response speed of custom configuration
            Must be configured before enabling GPS, need to restart GPS to take effect after configuration
        """
        # 发送自定义卫星系统选择指令并返回响应
        return self.sim7600.send_command("AT+CGPSNMEA=197119", timeout=5000)

    def enable_gps(self) -> str:
        """
        打开GPS模块
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGPS=1指令打开GPS模块，开启后开始卫星定位功能
            建议先配置卫星系统再开启GPS

        ==========================================
        Enable GPS module
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGPS=1 command to enable GPS module, start satellite positioning function after enabling
            It is recommended to configure the satellite system before enabling GPS
        """
        # 发送打开GPS模块指令并返回响应
        return self.sim7600.send_command("AT+CGPS=1")

    def start_search_satellite(self) -> str:
        """
        开始搜索卫星
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGPSFTM=1指令启动卫星搜索
            需在GPS开启后调用，搜星时间受环境影响（开阔环境约30秒）

        ==========================================
        Start searching for satellites
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGPSFTM=1 command to start satellite search
            Must be called after GPS is enabled, satellite search time is affected by environment (about 30 seconds in open environment)
        """
        # 发送启动搜星指令并返回响应
        return self.sim7600.send_command("AT+CGPSFTM=1")

    def get_gps_info(self) -> str:
        """
        查询GPS相关信息（定位状态、卫星数、经纬度等）
        Args:
            无

        Raises:
            无

        Notes:
            使用AT+CGPSINFO指令查询GPS定位信息
            响应数据包含定位状态、纬度、经度、UTC时间、卫星数等关键信息
            未定位成功时返回的经纬度数据为空

        ==========================================
        Query GPS related information (positioning status, satellite count, latitude/longitude etc.)
        Args:
            None

        Raises:
            None

        Notes:
            Use AT+CGPSINFO command to query GPS positioning information
            Response data includes key information such as positioning status, latitude, longitude, UTC time, satellite count
            Latitude and longitude data is empty when positioning is not successful
        """
        # 发送查询GPS信息指令并返回响应
        return self.sim7600.send_command("AT+CGPSINFO")


# ======================================== 初始化配置 ===========================================

# ========================================  主程序  ===========================================
