# MicroPython
# mail: goctaprog@gmail.com
# MIT license
from sensor_pack import bus_service, geosensmod
from sensor_pack.base_sensor import check_value, Iterator, TemperatureSensor
import array
import time


# little endian byte order
# Geomagnetic Sensor HSCDTD008A
class HSCDTD008A(geosensmod.GeoMagneticSensor, Iterator, TemperatureSensor):
    """Высокочувствительный трех осевой датчик магнитного поля от AlpsAlpine
    A high sensitivity three axis terrestrial magnetic sensor from AlpsAlpine.
    Electronic Compass function."""

    def __init__(self, adapter: bus_service.BusAdapter):
        super().__init__(adapter=adapter, address=0x0C, big_byte_order=False)  # адрес фиксирован!
        self._mag_field_comp = array.array("h", [0 for _ in range(3)])
        self._mag_field_offs = array.array("h", [0 for _ in range(3)])
        self._buf_2 = bytearray((0 for _ in range(2)))  # для хранения
        self._buf_6 = bytearray((0 for _ in range(6)))  # для хранения
        # Этот датчик имеет режим ожидания и активный режим работы.
        # Состояние с низким энергопотреблением. В режиме ожидания есть доступ к регистрам!
        # self._stand_by_pwr_mode = None
        # Переход в активное (рабочее) состояние производится изменением содержимого управляющего регистра
        # В активном режиме датчик может производить однократное (Force State)
        # или периодические (Normal State) измерения с частотой .5, 10, 20, 100 Hz
        # режим однократных или периодических измерений (только в Active Power Mode)
        # чтение смещений и запись из в _mag_field_offs
        self._read_offset()
        self._use_offset = False
        # self.enable_temp_meas(True)

    def read_buf_from_mem(self, mem_addr: int, buf: bytearray):
        """Читает из устройства с адресом address в буфер buf, начиная с адреса в устройстве mem_addr.
        Количество считываемых байт определяется длинной буфера buf."""
        return self.adapter.read_buf_from_mem(self.address, mem_addr, buf)  # 16 bit value (int16)

    def __del__(self):
        # go to stand by mode
        self.start_measure(active_pwr_mode=False)

    @staticmethod
    def _copy(destination, source):
        for i, item in enumerate(source):
            destination[i] = item

    def _read_ctrl1(self) -> int:
        """Чтение регистра управления 1"""
        return self._read_reg(0x1B)[0]

    def _read_field(self, offset: bool = False):
        """Считывает в заранее подготовленные буферы составляющие магнитного поля (при offset=False),
        иначе считывает Offset drift values"""
        source_addr = 0x10  # read output X, output Y, output Z
        destination = self._mag_field_comp
        if offset:  # read offset X, offset Y, offset Z
            source_addr = 0x20
            destination = self._mag_field_offs
        b_val = self._buf_6
        self.read_buf_from_mem(source_addr, b_val)
        self._copy(destination, self.unpack(fmt_char="hhh", source=b_val))

    def _read_offset(self):
        """считывает из датчика и записывает в массив несколько смещений!"""
        self._read_field(offset=True)

    @property
    def use_offset(self) -> bool:
        """если истина, то к Output Data X, Output Data Y, Output Data Z,
        будет прибавляться OFFX, OFFY, OFFZ соответственно!"""
        return self._use_offset

    @use_offset.setter
    def use_offset(self, value):
        self._use_offset = value

    def _read_reg(self, reg_addr: int, bytes_count: int = 1) -> bytes:
        """Считывает значение из регистра по адресу регистра 0..0x10. Смотри _get_reg_address"""
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def _write_reg(self, reg_addr: int, value: int, bytes_count: int = 1):
        """Записывает в регистр с адресом reg_addr значение value по шине."""
        bo = self._get_byteorder_as_str()[0]
        self.adapter.write_register(self.address, reg_addr, value, bytes_count, bo)

    def get_conversion_cycle_time(self) -> int:
        """Возвращает время преобразования сигнала измеряемой величины в значение,
        готовое к считыванию. В миллисекундах.
        Просьба не путать с update_rate!"""
        return 5    # 5 ms!

    def read_raw(self, axis: int) -> int:
        check_value(axis, range(3), f"Invalid axis value: {axis}")
        b_val = self._buf_2
        self.read_buf_from_mem(0x10 + 2 * axis, b_val)
        ret_val = self.unpack(fmt_char="h", source=b_val)[0]  # read as signed short
        if self.use_offset:
            ret_val += self.offset_drift_values[axis]
        return ret_val

    def _get_all_meas_result(self) -> tuple:
        """Для наибыстрейшего считывания за один вызов всех результатов измерений из датчика по
        относительно медленной шине! Для переопределения программистом!!!"""
        b_val = self._buf_6
        self.read_buf_from_mem(0x10, b_val)     # x, y, z. 6 bytes
        return self.unpack(fmt_char='hhh', source=b_val)

    def get_temperature(self) -> int:
        """Возвращает температуру корпуса датчика"""
        b_val = self._read_reg(0x31)
        return self.unpack("b", b_val)[0]  # read as signed char

    def get_id(self):
        """Должен возвратить 0x49"""
        return self._read_reg(0x0F)[0]

    def get_status(self) -> tuple:
        """Возвращает кортеж битов(номер бита): DRDY(6), DOR(5), FFU(2), TRDY(1)"""
        stat = self._read_reg(0x18)[0]
        drdy = bool(stat & 0b0100_0000)
        dor = bool(stat & 0b0010_0000)
        ffu = bool(stat & 0b0000_0100)
        trdy = bool(stat & 0b0000_0010)
        #      Data Ready Detection, Data Overrun Detection, FIFO full alarm,     Temperature ready
        return drdy, dor, ffu, trdy

    def _control_1(
            self,
            active_power_mode: [bool, None] = True,  # bit 7
            output_data_rate: [int, None] = 1,  # bit 4,3; 0 - .5 Hz, 1 - 10 Hz, 2 - 20 Hz, 3 - 100 Hz
            force_state: [bool, None] = True,  # bit 1
    ):
        """Control 1 Register (CTRL1)."""
        val = self._read_ctrl1()
        if active_power_mode is not None:
            val &= ~(1 << 7)  # mask
            val |= active_power_mode << 7
        if output_data_rate is not None:
            val &= ~(0b11 << 3)  # mask
            val |= output_data_rate << 3
        if force_state is not None:
            val &= ~(1 << 1)  # mask
            val |= force_state << 1
        self._write_reg(0x1B, val, 1)

    def _control_2(
            self,
            fco: [bool, None] = False,  # bit 6; Data storage method at FIFO. 0 = Direct, 1 = Comparison. Note:
            # Enabled if FIFO
            aor: [bool, None] = False,  # bit 5; Choice of method of data Comparison at FIFO. 0 = OR ,
            # 1 = AND.Enabled if FIFO
            fifo_enable: [bool, None] = False,  # bit 4; 0 = Disable, 1 = Enable
            den: [bool, None] = False,  # bit 3; Data Ready Function Control Enable. 0 = Disabled, 1 = Enabled
            data_ready_lvl_ctrl: [bool, None] = True  # bit 2; DRDY signal active level control, 0 = ACTIVE LOW,
            # 1 = ACTIVE HIGH
    ):
        """Control 2 Register (CTRL2).
        When a CTRL2 register value was changed during the measurement,
        The contents of the change are reflected after measurement."""
        val = self._read_reg(0x1C)[0]
        if fco is not None:
            val &= ~(1 << 6)  # mask
            val |= fco << 6
        if aor is not None:
            val &= ~(1 << 5)  # mask
            val |= aor << 5
        if fifo_enable is not None:
            val &= ~(1 << 4)  # mask
            val |= fifo_enable << 4
        if den is not None:
            val &= ~(1 << 3)  # mask
            val |= den << 3
        if data_ready_lvl_ctrl is not None:
            val &= ~(1 << 2)  # mask
            val |= data_ready_lvl_ctrl << 2
        self._write_reg(0x1C, val, 1)

    def _control_3(
            self,
            soft_reset: [bool, None] = False,  # bit 7; Soft Reset Control Enable. 0 = No Action, 1 = Soft Reset
            force_state: [bool, None] = False,  # bit 6; Start to Measure in Force State. 0 = No Action, 1 = Meas. Start
            self_test: [bool, None] = False,  # bit 4; Self Test Control Enable.
            # 0 = No Action, 1 = Set parameters to Self Test Response (STB) register.
            temp_measure: [bool, None] = False,  # bit 1; Start to Measure Temperature in Active Mode.
            # 0 = No Action, 1 = Measurement Start
            calibrate_offset: [bool, None] = False,  # bit 0; Start to Calibrate Offset in Active Mode.
            # 0 = No Action, 1 = Action
    ):
        """Control 3 Register (CTRL3).
        Bit control at the same time is prohibited.
        Priority of this register is MSB."""
        val = self._read_reg(0x1D)[0]
        if soft_reset is not None:
            val &= ~(1 << 7)    # mask
            val |= soft_reset << 7
        if force_state is not None:
            val &= ~(1 << 6)  # mask
            val |= force_state << 6
        if self_test is not None:
            val &= ~(1 << 4)  # mask
            val |= self_test << 4
        if temp_measure is not None:
            val &= ~(1 << 1)  # mask
            val |= temp_measure << 1
        if calibrate_offset is not None:
            val &= 0xFE  # mask
            val |= calibrate_offset
        self._write_reg(0x1D, val, 1)

    def _control_4(
            self,
            hi_dynamic_range: [bool, None] = False,  # bit 4; Set Dynamic range of output data.
            # 0 = 14 bit signed value (-8192 to +8191) (Default)
            # 1 = 15 bit signed value (-16384 to +16383)
    ):
        """Control 4 Register (CTRL4).
        When a CTRL4 register value was changed during the measurement,
        The contents of the change are reflected after measurement."""
        if hi_dynamic_range is None:
            return
        val = 0x80 | (hi_dynamic_range << 4)
        self._write_reg(0x1E, val, 1)

    def perform_self_test(self) -> bool:
        """Возвращает истина, если самопроверка пройдена!
        Не выполняйте проверку в режиме stand by!!! Только в режиме active_power_mode!!!"""
        val = self._read_reg(0x0C)[0]   # read STB reg
        if 0x55 != val:
            return False
        self._control_3(self_test=True)     # CTRL3.STC -> 1
        val = self._read_reg(0x0C)[0]  # read STB reg
        if 0xAA != val:
            return False
        return 0x55 == self._read_reg(0x0C)[0]  # read STB reg

    def soft_reset(self):
        """Выполняет програмный сброс датчика"""
        self._control_3(soft_reset=True)  # CTRL3.SRST -> 1

    def is_continuous_meas_mode(self) -> bool:
        return not self.is_single_meas_mode()

    def is_single_meas_mode(self) -> bool:
        tmp = 0x02 & self._read_ctrl1()  # FS bit. Force State
        return 0 != tmp

    def in_standby_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в состоянии stand by и Ложь, когда датчик включен!"""
        tmp = 0x80 & self._read_ctrl1()     # PC bit
        return 0 == tmp

    def set_dynamic_range(self, hi: bool):
        """устанавливает динамический диапазон данных датчика. Если hi Истина, то 15 bit, иначе 14 бит"""
        self._control_4(hi)

    def get_dynamic_range(self) -> bool:
        """Возвращает Истина, когда разрешение 15 бит, иначе разрешение 14 бит"""
        ctrl4 = self._read_reg(0x1E)[0]  # read CTRL4 reg
        return 0 != (ctrl4 & 0b0001_0000)

    @property
    def hi_dynamic_range(self) -> bool:
        return self.get_dynamic_range()

    @hi_dynamic_range.setter
    def hi_dynamic_range(self, value: bool):
        self.set_dynamic_range(value)

    def start_measure(self, continuous_mode: bool = True, update_rate: int = 1, active_pwr_mode: bool = True):
        """Запускает однократное или периодические измерение(я).
            active_pwr_mode - если Истина, то датчик включен, иначе в состоянии stand by.
            update_rate - частота измерений (0..3) при периодических(!) измерениях. 0 - 0.5 Hz; 1 - 10 Hz;
                                                                                    2 - 20 Hz; 3 - 100 Hz
            continuous_mode - если False, то каждое измерение нужно запускать вызовом start_measure,
                            иначе измерения запускаются автоматически с частотой data_rate
            update_rate - это не время преобразования(5 мс), а частота(Гц) обновления данных датчиком!
        """
        check_value(update_rate, range(4), f"Invalid update rate value: {update_rate}")
        self._control_1(active_pwr_mode, update_rate, not continuous_mode)
        if not continuous_mode:
            # Запускает однократное(!) измерение. Вызывается в режиме измерений по запросу(!)
            # Частота запросов, зависит от частоты вызова метода и пропускной способности шины! :-)
            # single meas mode
            self._control_3(force_state=True)  # CTRL3.FRC -> 1

    def enable_temp_meas(self, enable: bool = True):
        """управляет измерением температуры в активном режиме датчика"""
        self._control_3(temp_measure=enable)

    @property
    def offset_drift_values(self) -> tuple[int, int, int]:
        """Возвращает Offset Drift Values (OFFX, OFFY, OFFZ)"""
        return self._mag_field_offs[0], self._mag_field_offs[1], self._mag_field_offs[2]

    def set_offset_drift_values(self, offs_x: int = 0, offs_y: int = 0, offs_z: int = 0):
        """Запись значений смещений в регистры датчика.
        Значение (offs_*) не должны превышать от -8192 dec до +8191 dec"""
        t = offs_x, offs_y, offs_z
        ba = bytearray([0 for _ in range(2*3)])
        for index, value in enumerate(t):
            check_value(value, range(-8192, 8192), f"Invalid offset value: {value}")
            b = value.to_bytes(2, "little", True)
            ba[2 * index] = b[0]
            ba[2 * index + 1] = b[1]
            # запись начиная с адреса 0x20
        self.adapter.write_register(self.address, 0x20, ba, 0, "")

    def calibrate_offsets(self):
        """Выполняется калибровка каких-то смещений. Вызывать только в режиме измерений по запросу(!)
        Когда напряженность магнитного поля имеет дрейф смещения,
        значения выходных данных можно компенсировать путем записи в регистры значений смещения."""
        self._control_3(calibrate_offset=True)  # CTRL3.FRC -> 1, CTRL3.OCL -> 1
        while True:
            val = 0x01 & self._read_reg(0x1D)[0]   # read val CTRL3
            if not val:
                break   # калибровка завершилась!
            time.sleep_ms(10)   # ожидание
        # читаю смещения в self._mag_field_offs
        self._read_field(offset=True)

    def __iter__(self):
        return self

    def __next__(self):
        """возвращает результат только в периодическом режиме измерений!"""
        if self.is_continuous_meas_mode():
            return self.get_axis(-1)
