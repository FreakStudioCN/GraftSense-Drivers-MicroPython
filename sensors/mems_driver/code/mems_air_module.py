
import time


from machine import SoftI2C, Pin, Timer


from micropython import const


class MEMSGasSensor:

    
    
    TYPE_VOC = const(1)
    TYPE_H2 = const(2)
    TYPE_CO = const(3)
    TYPE_NH3 = const(4)
    TYPE_H2S = const(5)
    TYPE_ETHANOL = const(6)
    TYPE_PROPANE = const(7)
    TYPE_FREON = const(8)
    TYPE_NO2 = const(9)
    TYPE_SMOKE = const(10)
    TYPE_HCHO = const(11)
    TYPE_ACETONE = const(12)

    
    ADDR7 = const(0x2A)
    CMD_READ = const(0xA1)
    CMD_CAL = const(0x32)
    PREHEAT_MS = const(30000)
    OP_DELAY_MS = const(20)

    
    MAX_I2C_FREQ = const(100000)
    CALIB_MIN: int = 0
    CALIB_MAX: int = 65535

    def __init__(self, i2c: SoftI2C, sensor_type: int, addr7: int = ADDR7) -> None:
        
        if not isinstance(i2c, SoftI2C):
            raise TypeError("i2c must be a SoftI2C instance")

        
        valid_types = {
            MEMSGasSensor.TYPE_VOC, MEMSGasSensor.TYPE_H2, MEMSGasSensor.TYPE_CO, MEMSGasSensor.TYPE_NH3,
            MEMSGasSensor.TYPE_H2S, MEMSGasSensor.TYPE_ETHANOL, MEMSGasSensor.TYPE_PROPANE, MEMSGasSensor.TYPE_FREON,
            MEMSGasSensor.TYPE_NO2, MEMSGasSensor.TYPE_SMOKE, MEMSGasSensor.TYPE_HCHO, MEMSGasSensor.TYPE_ACETONE
        }
        if sensor_type not in valid_types:
            raise ValueError(f"Invalid sensor_type {sensor_type}, use TYPE_* constants")

        
        self.i2c: SoftI2C = i2c
        self.addr: int = addr7  
        self.sensor_type: int = sensor_type

    def read_concentration(self) -> int:

        try:
            
            
            ack_count = self.i2c.writeto(self.addr, bytes([MEMSGasSensor.CMD_READ]), False)
            if ack_count != 1:
                raise OSError("No ACK for read command")

            
            data = self.i2c.readfrom(self.addr, 2)
            if len(data) != 2:
                raise OSError("Incomplete data received")

            
            concentration = (data[0] << 8) | data[1]
            return concentration
        except OSError as e:
            print(f"Failed to read concentration: {str(e)}")
            return 0

    def calibrate_zero(self, calib_value: int | None = None) -> bool:

        
        if calib_value is None:
            calib_value = self.read_concentration()

        
        if calib_value > MEMSGasSensor.CALIB_MAX or calib_value < MEMSGasSensor.CALIB_MIN:
            raise ValueError("Calibration value must be between 0 and 65535")

        
        high_byte: int = (calib_value >> 8) & 0xFF
        low_byte: int = calib_value & 0xFF

        try:
            
            
            ack_count = self.i2c.writeto(self.addr, bytes([MEMSGasSensor.CMD_CAL, high_byte, low_byte]))
            
            if ack_count != 1:
                raise OSError("No ACK for calibrate command or data")

            
            post_calib_value = self.read_concentration()
            if post_calib_value != 0:
                print(f"Calibration confirmation failed: Read value {post_calib_value} is not 0")
                return False

            return True

        except OSError as e:
            print(f"Failed to calibrate zero: {str(e)}")
            return False

    def get_address(self) -> int:
        return self.addr

    def get_type(self) -> int:
        return self.sensor_type

class PCA9546ADR:
    addr7 = const(0x70)  
    MAX_CH = const(4)

    def __init__(self, i2c, addr=addr7):
        self.i2c = i2c
        self.addr = addr
        self._current_mask = 0x00

    def write_ctl(self, ctl_byte):
        ctl = int(ctl_byte) & 0x0F  
        try:
            self.i2c.writeto(self.addr, bytearray([ctl]))
        except OSError as e:
            
            raise
        else:
            
            self._current_mask = ctl

    def select_channel(self, ch):
        if ch < 0 or ch >= self.MAX_CH:
            raise ValueError("Invalid channel")
        self.write_ctl(1 << ch)

    def disable_all(self):
        self.write_ctl(0x00)

    def read_status(self):
        try:
            b = self.i2c.readfrom(self.addr, 1)
        except OSError as e:
            
            raise
        else:
            status = b[0] & 0x0F
            self._current_mask = status
            return status

    def current_mask(self):
        return self._current_mask


class AirQualityMonitor:
    """空气质量监测器（整合多路复用器和多个气体传感器）"""
    RESTART_DELAY_MS = const(5000)

    def __init__(self, i2c, pca_addr=PCA9546ADR.addr7):
        self.i2c = i2c
        self.pca = PCA9546ADR(i2c, pca_addr)
        self.sensors = {}  # {通道号: 传感器实例}
        self.channel_map = {}  # {传感器类型: 通道号}
        self.enabled_mask = 0x00

        self._restart_pending = False
        self._restart_target_mask = 0x00
        self._restart_start_time = 0

    def register_sensor(self, channel, sensor_type, sensor_addr=MEMSGasSensor.ADDR7):
        """注册传感器到指定通道"""
        if channel < 0 or channel >= PCA9546ADR.MAX_CH:
            raise ValueError(f"Channel must be 0-{PCA9546ADR.MAX_CH - 1}")
        if channel in self.sensors:
            print(f"Warning: Channel {channel} already has a sensor, overwriting")

        # 切换到目标通道
        self.pca.disable_all()
        self.pca.select_channel(channel)
        # 创建传感器实例
        sensor = MEMSGasSensor(self.i2c, sensor_type, sensor_addr)
        # 注册传感器
        self.sensors[channel] = sensor
        self.channel_map[sensor_type] = channel
        self.enabled_mask |= (1 << channel)
        print(f"Registered {self._sensor_type_name(sensor_type)} sensor on channel {channel}")
        return sensor

    def read_sensor(self, sensor_type):
        """读取指定类型传感器的浓度值"""
        if sensor_type not in self.channel_map:
            raise ValueError(f"No sensor registered for type {sensor_type}")

        channel = self.channel_map[sensor_type]
        self.pca.disable_all()
        self.pca.select_channel(channel)
        concentration = self.sensors[channel].read_concentration()
        return concentration

    def read_all(self):
        """读取所有已注册传感器的浓度值，返回字典 {传感器类型: 浓度值}"""
        results = {}
        for sensor_type, channel in self.channel_map.items():
            self.pca.disable_all()
            self.pca.select_channel(channel)
            results[sensor_type] = self.sensors[channel].read_concentration()
            time.sleep_ms(MEMSGasSensor.OP_DELAY_MS)
        return results

    def calibrate_sensor(self, sensor_type):
        """校准指定类型的传感器"""
        if sensor_type not in self.channel_map:
            raise ValueError(f"No sensor registered for type {sensor_type}")

        channel = self.channel_map[sensor_type]
        self.pca.disable_all()
        self.pca.select_channel(channel)
        success = self.sensors[channel].calibrate_zero()
        return success

    def _sensor_type_name(self, sensor_type):
        """将传感器类型常量转换为名称（便于打印）"""
        type_names = {
            MEMSGasSensor.TYPE_VOC: "VOC",
            MEMSGasSensor.TYPE_H2: "H2",
            MEMSGasSensor.TYPE_CO: "CO",
            MEMSGasSensor.TYPE_NH3: "NH3",
            MEMSGasSensor.TYPE_H2S: "H2S",
            MEMSGasSensor.TYPE_ETHANOL: "ETHANOL",
            MEMSGasSensor.TYPE_PROPANE: "PROPANE",
            MEMSGasSensor.TYPE_FREON: "FREON",
            MEMSGasSensor.TYPE_NO2: "NO2",
            MEMSGasSensor.TYPE_SMOKE: "SMOKE",
            MEMSGasSensor.TYPE_HCHO: "HCHO",
            MEMSGasSensor.TYPE_ACETONE: "ACETONE"
        }
        return type_names.get(sensor_type, f"UNKNOWN({sensor_type})")
