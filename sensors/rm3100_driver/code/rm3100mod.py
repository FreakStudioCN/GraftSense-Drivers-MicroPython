"""MicroPython module for RM3100 Geomagnetic Sensor"""
import struct
import micropython

# MicroPython
# mail: goctaprog@gmail.com
# MIT license
from sensor_pack import bus_service, geosensmod
from sensor_pack.base_sensor import check_value, Iterator
import time


@micropython.native
def _axis_to_int(axis: [set, str]) -> int:
    """преобразует входное множество, содержащее 'X', 'Y', 'Z' в int от 0 до 7 включительно.
    '' - 0; 'X' - 1; 'X', 'Y' - 3; 'X', 'Y', 'Z' - 7"""
    _axis = 0
    _str_axis = 'XYZ'
    for index, axs in enumerate(_str_axis):
        if axs in axis or str.lower(axis) in axis:
            _axis += 2 ** index

    return _axis


@micropython.native
def _axis_name_to_int(axis_name: str) -> int:
    """Преобразует имя оси ('x', 'y', 'z', 'X', 'Y', 'Z') в число 0(X), 1(Y), 2(Z)"""
    an = axis_name.lower()
    check_value(ord(an[0]), range(120, 123), f"Invalid axis name: {axis_name}")
    return ord(an[0]) - 120  # 0, 1, 2


@micropython.native
def _int_to_axis_name(axis: int) -> str:
    """преобразует число в имя оси"""
    check_value(axis, range(3), f"Invalid axis: {axis}")
    a = 'x', 'y', 'z'
    return a[axis]


@micropython.native
def _axis_name_to_reg_addr(axis_name: str, offset: int, multiplier: int) -> int:
    """Преобразует имя оси ('x', 'y', 'z', 'X', 'Y', 'Z') в адрес соответствующего регистра"""
    return offset + multiplier * _axis_name_to_int(axis_name)


def _axis_name_to_ccr_addr(axis_name: str) -> int:
    """Преобразует имя оси ('x', 'y', 'z', 'X', 'Y', 'Z') в адрес соответствующего регистра CCR(Cycle Count Register)"""
    return _axis_name_to_reg_addr(axis_name, 4, 2)


def _axis_name_to_mxyz_addr(axis_name: str) -> int:
    """Преобразует имя оси ('x', 'y', 'z', 'X', 'Y', 'Z') в адрес соответствующего регистра CCR(Cycle Count Register)"""
    return _axis_name_to_reg_addr(axis_name, 0x24, 3)


def get_conversion_cycle_time(update_rate: int) -> int:
    """Возвращает время, в микросекундах(!), преобразования датчиком в зависимости от его настроек.
    Для режима периодических измерений, устанавливает частоту обновления значений величины магнитного поля
    update_rate должно быть в диапазоне от 0 до 13 включительно, что соответствует частотам:
    0 - 600 Hz; 1 - 300 Hz; 2 - 150 Hz; 3 - 75 Hz; 4 - 37 Hz; 5 - 18 Hz; ...; 13 - ~0.075 Hz"""
    check_value(update_rate, range(14), f"Invalid update rate: {update_rate}")
    return 1667 * (2 ** update_rate)


def _from_bytes(source: bytes, big_byte_order: bool = True, signed=False) -> int:
    order = tuple(reversed(source)) if big_byte_order else tuple(source)
    #
    n = sum(byte << 8 * index for index, byte in enumerate(order))
    if signed and order and (order[-1] & 0x80):
        n -= 1 << 8 * len(order)

    return n


def _to_str(source: bytes) -> str:
    res = ''
    for item in source:
        res += f"0x{item:x} "
    return res


class RM3100(geosensmod.GeoMagneticSensor, Iterator):
    """RM3100 Geomagnetic Sensor."""

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x20):
        self._buf_2 = bytearray((0 for _ in range(2)))  # для хранения
        self._buf_3 = bytearray((0 for _ in range(3)))  # для хранения
        self._buf_9 = bytearray((0 for _ in range(9)))  # для хранения
        self._update_rate = 6   # 9 Hz
        # адрес в диапазоне 0x20..0x23!
        check_value(address, range(0x20, 0x24), f"Invalid address value: {address}")
        super().__init__(adapter=adapter, address=address, big_byte_order=True)     # big endian
        self.setup()

    def _read_reg(self, reg_addr: int, bytes_count: int = 1) -> bytes:
        """Считывает значение из регистра по адресу регистра 0..0x10. Смотри _get_reg_address"""
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def read_buf_from_mem(self, mem_addr: int, buf: bytearray):
        """Читает из устройства с адресом address в буфер buf, начиная с адреса в устройстве mem_addr.
        Количество считываемых байт определяется длинной буфера buf."""
        return self.adapter.read_buf_from_mem(self.address, mem_addr, buf)  # 16 bit value (int16)

    def _write_reg(self, reg_addr: int, value: int, bytes_count: int = 1):
        """Записывает в регистр с адресом reg_addr значение value по шине."""
        bo = self._get_byteorder_as_str()[0]
        self.adapter.write_register(self.address, reg_addr, value, bytes_count, bo)

    def _set_update_rate(self, update_rate: int):
        """для режима периодических измерений, устанавливает частоту обновления значений величины магнитного поля
        update_rate должно быть в диапазоне от 0 до 13 включительно, что соответствует частотам:
        0 - 600 Hz; 1 - 300 Hz; 2 - 150 Hz; 3 - 75 Hz; 4 - 37 Hz; 5 - 18 Hz; ...; 13 - ~0.075 Hz"""
        check_value(update_rate, range(14), f"Invalid update rate: {update_rate}")
        # Setting the CMM Update Rate with TMRC (0x0B)
        self._write_reg(0x0B, 0x92 + update_rate)
        self._update_rate = update_rate

    def _get_update_rate(self) -> int:
        self._update_rate = self._read_reg(0x0B)[0] - 0x92
        return self._update_rate

    def _get_cmm(self) -> int:
        """Возвращает значение регистра CMM"""
        return self._read_reg(0x01)[0]

    def get_id(self):
        """Возвращает значение (REVID), которое не определено в документации, что странно!
        return MagI2C Revision Identification"""
        return self._read_reg(0x36)[0]

    def is_continuous_meas_mode(self):
        """Возвращает Истина, когда включен режим периодических измерений!"""
        return 0 != (0x01 & self._get_cmm())

    def is_single_meas_mode(self):
        """Возвращает Истина, когда включен режим однократных измерений (по запросу)!
        Для переопределения программистом!!!"""
        return 0 == (0x01 & self._get_cmm())

    def get_status(self) -> tuple:
        """Возвращает кортеж битов(номер бита): DRDY(7), """
        stat = self._read_reg(0x34)[0]
        return 0 != (stat & 0x80),

    def is_data_ready(self) -> bool:
        return self.get_status()[0]

    def perform_self_test(self) -> tuple:
        """Возвращает кортеж результатов самопроверки!"""
        bist_addr = 0x33
        poll_addr = 0x00
        cmm_addr = 0x00
        hshake_addr = 0x35
        try:
            self._write_reg(reg_addr=cmm_addr, value=0x70)
            self._write_reg(reg_addr=hshake_addr, value=0x08)

            self._write_reg(bist_addr, 0x8F)      # start the built-in self test
            self._write_reg(poll_addr, 0x70)  # запускаю измерение по всем трем осям
            counter = 0
            while True:
                time.sleep_ms(10)
                if counter > 3 or self.get_status()[0]:
                    break   # The end of the built-in self test sequence
                counter += 1
            bist = self._read_reg(bist_addr)[0]
            #       Z axis OK,   Y axis OK,   X axis OK,    Timeout Period,     LR Periods
            return 0 != bist & 0x40, 0 != bist & 0x20, 0 != bist & 0x10, (bist & 0b1100) >> 2, bist & 0b11
        finally:
            self._write_reg(reg_addr=bist_addr, value=0x00)  # disable self-test mode, clear STE bit

    def soft_reset(self):
        """Выполняет програмный сброс датчика"""
        pass

    def start_measure(self, axis: [set, str], update_rate: int = 6,
                      single_mode: bool = True, full_meas_seq: bool = True):
        """Запускает однократное или периодические измерение(я).
        axis - множество, которое должно содержать строки имен осей,
        по которым нужно измерить магнитное поле 'X', 'Y', 'Z';
        update_rate - коэффициент частоты обновления: 0 - 600 Hz, 1 - 300 Hz, 2 - 150 Hz, .. , 13 - ~0.075 Hz;
        single_mode - если истина, то запускает однократное измерение, иначе запускает периодические измерения!;
        Если full_meas_seq Истина, то вывод DRDY установится в 1 после завершения ПОЛНОЙ последовательности измерений,
        как установлено осями в axis!,
        иначе вывод DRDY установится в 1 после завершения измерения по любой ОДНОЙ оси!!;"""
        _axis = _axis_to_int(axis=axis)
        _axis <<= 4  # в CMM и POLL оси занимают с 4 бита по 6!
        data_ready_mode = 0
        if not full_meas_seq:
            data_ready_mode = 1

        if not single_mode:     # Continuous Measurement Mode!
            self._set_update_rate(update_rate)
            self._write_reg(reg_addr=0x01, value=_axis | (data_ready_mode << 2) | 0x01)
        else:                   # single mode
            self._write_reg(reg_addr=0x01, value=0)     # Continuous Measurement Mode disabled
            self._write_reg(reg_addr=0x00, value=_axis)  # запускаю однократное измерение

    def set_axis_cycle_count(self, axis_name: str, value: int):
        """Устанавливает количество циклов для измерения магнитного поля по оси axis_name!
        Значения по умолчанию для регистров счетчика циклов: 0xC8 (200).
        Это значение по умолчанию обеспечивает хороший компромисс между временем измерения и его точностью,
        но в пользу точности!
        Если пользователя больше интересует низкое энергопотребление или работа на высоких скоростях передачи данных,
        более подходящим будет более низкое значение счетчика циклов (например, 50 или 100).
        Допустимым диапазоном значений счетчика циклов является диапазон от 30 до 400.
        В Table 3-1: Geomagnetic Sensor Performance, посмотрите строки в столбце Cycle Counts!"""
        addr = _axis_name_to_ccr_addr(axis_name)
        bo_t = self._get_byteorder_as_str()
        bts = struct.pack(bo_t[1]+"H", value)
        self.adapter.write_register(self.address, addr, bts, 0, '')

    def get_axis_cycle_count(self, axis_name: str) -> int:
        """Возвращает количество циклов для измерения магнитного поля по оси axis_name!"""
        addr = _axis_name_to_ccr_addr(axis_name)
        #bts = self._read_reg(addr, 2)
        bts = self._buf_2
        self.read_buf_from_mem(addr, bts)
        return self.unpack(fmt_char="H", source=bts)[0]

    def read_raw(self, axis_name: int) -> int:
        addr = _axis_name_to_mxyz_addr(_int_to_axis_name(axis_name))
        #bts = self._read_reg(reg_addr=addr, bytes_count=3)  # 24 bit value (int24)
        bts = self._buf_3
        self.read_buf_from_mem(addr, bts)
        return _from_bytes(source=bts, big_byte_order=True, signed=True)

    def _get_all_meas_result(self) -> tuple:
        """Для наибыстрейшего считывания за один вызов всех результатов измерений из датчика по
        относительно медленной шине! Для переопределения программистом!!!"""
        #bts = self._read_reg(reg_addr=0x24, bytes_count=9)  # 24 bit value (int24)
        bts = self._buf_9
        self.read_buf_from_mem(0x24, bts)
        t = (_from_bytes(source=bts[3 * index:3 * (index+1)], big_byte_order=True, signed=True) for index in range(3))
        return tuple(t)

    def setup(self):
        """Настройка режима работы датчика.
            active_pwr_mode - если Истина, то датчик включен, иначе в состоянии stand by.
            data_rate - частота измерений (0..3) при периодических(!) измерениях.
            single_mode - если Истина, то каждое измерение нужно запускать вызовом start_measure,
                            иначе измерения запускаются автоматически с частотой data_rate
        """
        # DRC0 = 0, DRC1 = 1
        self._write_reg(reg_addr=0x35, value=0x0A)
        pass

    def __iter__(self):
        return self

    def __next__(self):
        """возвращает результат только в режиме периодических измерений!"""
        if self.is_continuous_meas_mode and self.is_data_ready():
            return self.get_axis(-1)
        return None
