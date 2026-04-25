"""INAxxx Texas Instruments sensors module.

Внимание! для долговременной непрерывной работы токового шунта, не допускайте выделения на нем более половины(!) от его
максимальной рассеиваемой мощности! Если установка будет работать 24/7, то допускайте(!) выделения на нем не более 1/3 от его
максимальной рассеиваемой мощности!!!
Мощность, выделяемая на любом сопротивлении (постоянный ток), рассчитывается по формуле: P=I**2 * R
где: I - ток в Амперах; R - сопротивление в Омах.

Attention! for long-term continuous operation of the current shunt, do not allow more than half(!) of its maximum
dissipated power to be allocated on it!!
The power dissipated on any resistance (direct current) is calculated by the formula: P=I**2 * R
where: I - current in Amperes; R - resistance in ohms"""
import math
# from select import select

from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import BaseSensorEx, IBaseSensorEx, Iterator, check_value

from collections import namedtuple
from sensor_pack_2.bitfield import bit_field_info
from sensor_pack_2.bitfield import BitFields

def get_exponent(value: float) -> int:
    """Возвращает десятичную степень числа.
    Returns the decimal power of a number"""
    return int(math.floor(math.log10(abs(value)))) if 0 != value else 0


# расшифровка поля MODE, регистра конфигурации
# Если continuous в Истина, то измерения проводятся автоматически, иначе их нужно запускать принудительно!
#  Если bus_voltage_enabled в Истина, то измерения входного НАПРЯЖЕНИЯ производятся! Иначе не производятся!
#  Если shunt_voltage_enabled в Истина, то измерения входного ТОКА производятся! Иначе не производятся!
ina219_operation_mode = namedtuple("ina219_operation_mode", "continuous bus_voltage_enabled shunt_voltage_enabled")
# имена полей регистра конфигурации
#   Бит         Имя         Описание
#   13          BRNG        Диапазон напряжения для АЦП напряжения на шине (входное напряжение)
#   11..12      PGA         Диапазоны напряжения для АЦП токового шунта
#   7..10       BADC        Разрешение/Усреднение АЦП шины
#   3..6        SADC        Разрешение/Усреднение АЦП токового шунта
#   2           CNTNS       Непрерывный режим работы(1)/однократный режим работы(0)
#   1           BADC_EN     АЦП напряжения на шине (входное напряжение) включен (1)
#   0           SADC_EN     АЦП напряжения на токовом шунте включен (1)
config_ina219 = namedtuple("config_ina219", "BRNG PGA BADC SADC CNTNS BADC_EN SADC_EN")
# для метода get_voltage
voltage_ina219 = namedtuple("voltage_ina219", "bus_voltage data_ready overflow")

def _get_conv_time(value: int) -> int:
    """Возвращает время из полей SADC, BADC в микросекундах"""
    _conv_time = 84, 148, 276, 532
    if value < 8:
        value &= 0x3  # 0..3
        return _conv_time[value]
    # 0x8..0xF. Усреднение по 2, 4, 8, 16, 32, 64, 128 отсчетам
    value -= 0x08  # 0..7
    coefficient = 2 ** value
    return 532 * coefficient

class INABase(BaseSensorEx):
    """Базовый класс измерителей тока и напряжения от TI.
    Base class for INA current/voltage monitor."""

    def __init__(self, adapter: bus_service.BusAdapter, address: int):
        """"""
        super().__init__(adapter, address, True)

    def get_16bit_reg(self, address: int, format_char: str) -> int:
        _raw = self.read_reg(address, 2)
        return self.unpack(format_char, _raw)[0]

    def set_16bit_reg(self, address: int, value: int):
        self.write_reg(address, value, 2)

    # BaseSensor
    def set_cfg_reg(self, value: int) -> int:
        """Установить сырую конфигурацию в регистре. Set raw configuration in register."""
        return self.write_reg(0x00, value, 2)

    def get_cfg_reg(self) -> int:
        """Возвращает сырую конфигурацию из регистра. Get raw configuration from register"""
        return self.get_16bit_reg(0x00, "H")

    def get_shunt_reg(self) -> int:
        """возвращает содержимое регистра напряжения шунта"""
        return self.get_16bit_reg(0x01, "h")

    def get_bus_reg(self) -> int:
        """возвращает содержимое регистра напряжения шины"""
        return self.get_16bit_reg(0x02, "H")

    def get_shunt_lsb(self) -> float:
        """Возвращает цену наименьшего младшего разряда АЦП напряжения на шунте в вольтах"""
        raise NotImplemented

    def get_bus_lsb(self) -> float:
        """Возвращает цену наименьшего младшего разряда АЦП напряжения на шине в вольтах"""
        raise NotImplemented

    def get_shunt_voltage(self) -> float:
        """Возвращает напряжение на шунте в вольтах, которое образуется при протекании тока в нагрузке"""
        # print(f"DBG: shunt_lsb: {self.get_shunt_lsb()}\tshunt_raw: {self.get_shunt_reg()}")
        return self.get_shunt_lsb() * self.get_shunt_reg()

    def get_voltage(self):
        """Возвращает напряжение на шине(BUS) в вольтах.
        Тип возвращаемого значения может изменятся в наследниках."""
        raise NotImplemented


class INA219Simple(INABase):
    """Класс для работы с датчиком TI INA219 без какой либо настройки!
    Диапазон измерения входного напряжения: 0..26 Вольт. Рекомендую 0..24 Вольта,
    дополнительно защита от выбросов напряжения!!!
    Диапазон измерения напряжения на токоизмерительном шунте: ±320 милливольт.
    Никаких настроек нет!
    ---------------------
    A class for working with a TI INA219 sensor without any configuration!
    Input voltage measurement range: 0-26 Volts.
    Voltage measurement range on the current measuring shunt: ±320 millivolts.
    There are no settings!"""

    # для вычислений
    # предельное напряжение на шунте: 0.32768 В. lsb = желаемое предельное напряжение на шунте поделить на 2 ** 15
    _lsb_shunt_voltage = 1E-5   # 10 uV
    _lsb_bus_voltage = 4E-3     # 4 mV

    def get_shunt_lsb(self)->float:
        """Возвращает цену младшего разряда АЦП токового шунта. Не изменяется при изменении разрядности, что странно!"""
        return INA219Simple._lsb_shunt_voltage

    def get_bus_lsb(self)->float:
        """Возвращает цену младшего разряда АЦП напряжения на шине. Не изменяется при изменении разрядности, что странно!"""
        return INA219Simple._lsb_bus_voltage

    def __init__(self, adapter: bus_service.BusAdapter, address=0x40):
        super().__init__(adapter, address)
        # 0x399F    настройка по умолчанию, простое считывание двух напряжений (входное-на шине и токового шунта).
        # Входного напряжения и напряжения на токовом шунте. Непрерывное произведение измерений.
        # Bus Voltage Range:    32 V    ("Senses Bus Voltages from 0 to 26 V". From page 1 of datasheet.)
        # Shunt Voltage Range:  ±320 mV
        # Bus ADC Resolution:   12 bit
        # Shunt ADC Resolution: 12 bit
        # Conversion Time:      532 us
        # Mode:                 Shunt and bus, continuous
        self.set_cfg_reg(0b0011_1001_1001_1111)

    def soft_reset(self):
        """Производит програмный сброс ИС. Возвращение состояния ИС к состоянию как после Power On Reset (POR)."""
        self.set_cfg_reg(0b11100110011111)

    def get_conversion_cycle_time(self) -> int:
        """Возвращает время в мкс(!) преобразования сигнала в цифровой код и готовности его для чтения по шине!
        Для текущих настроек датчика. При изменении настроек следует заново вызвать этот метод!"""
        return 532

    def get_voltage(self) -> voltage_ina219:
        """Возвращает кортеж из входного измеряемого напряжения, флага готовности данных, флага математического переполнения (OVF).
        Флаг математического переполнения (OVF) устанавливается, когда расчеты мощности или тока выходят за допустимые
        пределы. Это указывает на то, что данные о токе и мощности могут быть бессмысленными!
        ------------------------------------------------------------------------------
        Хотя данные последнего преобразования могут быть прочитаны в любое время, бит готовности к преобразованию указывает,
        когда  доступны данные преобразования в регистрах вывода данных. Бит готовности данных устанавливается после завершения всех(!) преобразований,
        усреднения и умножения. Он сбрасывается при следующих событиях:
            1) Запись нового режима в биты режима работы в регистре конфигурации (за исключением отключения или отключения питания).
            2) Чтение регистра мощности

        Бит готовности (CNVR) к преобразованию устанавливается после завершения всех(!) операций преобразования, усреднения и умножения!
        ------------------------------------------------------------------------------
        Returns a tuple of input measured voltage, data ready flag, math overflow flag (OVF).
        The Math Overflow Flag (OVF) is set when power or current calculations are out of range.
        This indicates that current and power data may be meaningless!"""
        # DC ACCURACY:  ADC basic resolution: 12 bit;    Bus voltage, 1 LSB step size: 4 mV
        _raw = self.get_bus_reg()
        return voltage_ina219(bus_voltage=self.get_bus_lsb() * (_raw >> 3), data_ready=bool(_raw & 0x02),
                              overflow=bool(_raw & 0x01))

ina_voltage = namedtuple("ina_voltage", "shunt bus")

class INABaseEx(INABase):
    """Чтобы не перегружать InaBase ненужным функционалом"""
    def get_pwr_reg(self) -> int:
        """Возвращает содержимое регистра мощности"""
        return self.get_16bit_reg(0x03, 'H')

    def get_curr_reg(self) -> int:
        """Возвращает содержимое регистра тока. Значение со знаком!"""
        return self.get_16bit_reg(0x04, 'h')

    def get_current_lsb(self) -> float:
        """Цена наименьшего значащего бита регистра тока.
        До вызова метода установи значение поля self.max_expected_current!
        Можно переопределить в случае необходимости."""
        return self.max_expected_current / 2 ** 15

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """Вычисляет цену наименьшего младшего разряда регистра мощности по цене
        наименьшего значащего бита регистра тока.
        Для переопределения в классах-наследниках!"""
        raise NotImplemented

    def set_clbr_reg(self, value: int):
        """Запись в регистр калибровки"""
        return self.set_16bit_reg(address=0x05, value=value)

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """Возвращает диапазон напряжения на шунте в 'сыром' виде,
        который будет записан в регистр конфигурации.
        Запоминает его в поле экземпляра класса.
        Для переопределения в классах-наследниках!"""
        raise NotImplemented

    def calibrate(self, max_expected_current: float, shunt_resistance: float) -> int:
        """Производит калибровку значений в регистре калибровки по максимальному току в Амперах
        и сопротивлению шунта в Омах"""
        _max_shunt_vltg = max_expected_current * shunt_resistance
        if _max_shunt_vltg > self.max_shunt_voltage or _max_shunt_vltg <= 0 or max_expected_current <= 0:
            raise ValueError(f"Неверная комбинация входных параметров! {max_expected_current}\t{shunt_resistance}")
        #
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)
        _cal_val = int(self._internal_fix_val / (self._current_lsb * shunt_resistance))  # волшебная формула из документации
        #
        self.choose_shunt_voltage_range(_max_shunt_vltg)
        #
        # запись в регистр калибровки. младший бит недоступен для записи!
        self.set_clbr_reg(_cal_val)
        return _cal_val

    def __init__(self, adapter: bus_service.BusAdapter, address: int, max_shunt_voltage: float,
                 shunt_resistance: float, fields_info: tuple[bit_field_info, ...], internal_fixed_value: float):
        super().__init__(adapter, address)
        # для удобства работы с настройками
        self._bit_fields = BitFields(fields_info=fields_info)   # информация о полях регистра конфигурации устройства
        # сопротивление токового шунта в Омах!
        self._shunt_resistance = shunt_resistance
        # предельное напряжение на шунте, по модулю, в Вольтах. Которое допускает АЦП!
        self._max_shunt_voltage = max_shunt_voltage
        self._max_expected_curr = None  # для метода calibrate
        self._current_lsb = None        # для метода calibrate
        self._power_lsb = None          # для метода calibrate
        self._internal_fix_val = internal_fixed_value   # для метода calibrate. Значение из документации!
        #
        self.max_expected_current = max_shunt_voltage / shunt_resistance
        self._current_lsb = self.get_current_lsb()
        self._power_lsb = self.get_pwr_lsb(self._current_lsb)

    def get_current_config_hr(self) -> tuple:
        """Преобразует текущую конфигурацию датчика в человеко-читаемую (Human Readable).
        Для переопределения в классах-наследниках!"""
        raise NotImplemented

    def get_cct(self, shunt: bool) -> int:
        """Возвращает время в мкс(!) преобразования сигнала в цифровой код и готовности его для чтения по шине!
        Get Current Conversion Time (CCT).
        Если shunt is True, то возвращается время преобразования напряжения на шУнте, иначе
        возвращается время преобразования напряжения на шИне!
        Для переопределения в наследниках"""
        raise NotImplemented

    def get_config(self) -> tuple:
        """Возврат текущей конфигурации датчика в виде кортежа.
        Вызовите этот метод, когда считаете, что нужно обновить конфигурацию в полях класса!!!"""
        raw = self.get_cfg_reg()
        self.set_config_field(raw)
        return self.get_current_config_hr()

    def get_config_field(self, field_name: [str, None] = None) -> [int, bool]:
        """Возвращает значение поля по его имени, field_name, из сохраненной конфигурации.
        Если field_name is None, будут возвращены все поля конфигурации в виде int"""
        bf = self._bit_fields
        if field_name is None:
            return bf.source
        return bf[field_name]

    def set_config_field(self, value: int, field_name: [str, None] = None):
        """Устанавливает значение поля, value, по его имени, field_name, в сохраненной конфигурации.
        Если field_name is None, будут установлены значения всех полей конфигурации."""
        bf = self._bit_fields
        if field_name is None:
            bf.source = value
            return
        bf[field_name] = value

    def set_config(self) -> int:
        """Настраивает датчик в соответствии с настройками. Возвращает значение настроек в сыром(!) виде"""
        _cfg = self.get_config_field()
        self.set_cfg_reg(_cfg)
        return _cfg

    @property
    def max_expected_current(self) -> float:
        """Возвращает расчетный максимальный ожидаемый ток в Амперах"""
        return self._max_expected_curr

    @max_expected_current.setter
    def max_expected_current(self, value: float):
        if .1 <= value <= 100:
            self._max_expected_curr = value
            return
        raise ValueError(f"Неверное значение тока: {value}")

    @property
    def max_shunt_voltage(self) -> float:
        """Возвращает максимальное(!) напряжение на шунте, которое измеряет АЦП"""
        return self._max_shunt_voltage

    @property
    def shunt_resistance(self) -> float:
        """Возвращает сопротивление токового шунта в Омах."""
        return self._shunt_resistance

    @shunt_resistance.setter
    def shunt_resistance(self, value: float):
        """Метод устанавливает сопротивление шунта в пределах 0.01..10 Ом"""
        if .001 <= value <= 10:
            self._shunt_resistance = value
            return
        raise ValueError(f"Неверное значение сопротивления шунта: {value}")

    @property
    def shunt_adc_enabled(self) -> bool:
        """Если Истина, то АЦП напряжения на токовом шунте включен!
        Един для INA219, INA226."""
        return self.get_config_field('SADC_EN')

    @property
    def bus_adc_enabled(self) -> bool:
        """Если Истина, то АЦП напряжения на шине включен!
        Един для INA219, INA226."""
        return self.get_config_field('BADC_EN')

    # для INA226 и INA219
    def is_single_shot_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в режиме однократных измерений,
        каждое из которых запускается методом start_measurement."""
        return not self.is_continuously_mode()

    def is_continuously_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в режиме многократных измерений,
        производимых автоматически. Процесс запускается методом start_measurement."""
        return self.get_config_field('CNTNS')

    def get_conversion_cycle_time(self) -> int:
        """Возвращает время в мс или мкс преобразования сигнала в цифровой код и готовности его для чтения по шине!
        Для текущих настроек датчика. При изменении настроек следует заново вызвать этот метод!
        Общий для 219 и 226"""
        _t0, _t1 = 0, 0
        #
        if self.shunt_adc_enabled:
            _t0 = self.get_cct(shunt=True)

        if self.bus_adc_enabled:
            _t1 = self.get_cct(shunt=False)
        # возвращаю наибольшее значение, поскольку измерения производятся параллельно, как утверждает документация
        return max(_t0, _t1)

    def start_measurement(self, continuous: bool = True, enable_calibration: bool = False,
                          enable_shunt_adc: bool = True, enable_bus_adc: bool = True):
        """Настраивает параметры датчика и запускает процесс измерения.
        continuous - если Истина, то новое измерение запускается автоматически после завершения предидущего;
        enable_calibration - если Истина, то происходит калибровка под заданное сопротивление шунта и ток в нагрузке;
        enable_shunt_adc - включить измерение напряжения на токовом шунте;
        enable_bus_adc - включить измерение напряжения на шине;
        Настраивайте параметры датчика ДО вызова этого метода, за исключением:
             - continuous, enable_shunt_adc, enable_bus_adc"""
        self.set_config_field(enable_bus_adc, 'BADC_EN')
        self.set_config_field(enable_shunt_adc, 'SADC_EN')
        self.set_config_field(continuous, 'CNTNS')
        if enable_calibration:
            self.calibrate(self.max_expected_current, self.shunt_resistance)

        self.set_config()


    @property
    def continuous(self) -> bool:
        """Возвратит Истина, если датчик находится в автоматическом режиме измерений"""
        return self.is_continuously_mode()

    def get_power(self) -> float:
        """Возвращает мощность в Ваттах в нагрузке"""
        return self._power_lsb * self.get_pwr_reg()

    def get_current(self) -> float:
        """Возвращает ток в нагрузке в Амперах"""
        _raw = self.get_curr_reg()
        # print(f"DBG: raw_curr: {_raw}\tlsb:{self._current_lsb}")
        return self._current_lsb * _raw

    def __iter__(self):
        return self

    def __next__(self) -> ina_voltage:
        """Возвращает измеренные значения. кортеж, число."""
        _shunt, _bus = None, None
        if self.shunt_adc_enabled:
            _shunt = self.get_shunt_voltage()
        if self.bus_adc_enabled:
            _bus = self.get_voltage()

        return ina_voltage(shunt=_shunt, bus=_bus)




ina219_data_status = namedtuple("ina219_data_status", "conversion_ready math_overflow")

class INA219(INABaseEx, IBaseSensorEx, Iterator):   # INA219Simple
    """Class for work with TI INA219 sensor"""

    # предел напряжения на шунте из документации, Вольт
    # shunt voltage limit, Volt
    _shunt_voltage_limit = 0.32768
    _lsb_shunt_voltage = 1E-5   # 10 uV
    _lsb_bus_voltage = 4E-3     # 4 mV
    # разрешенные значения для полей BADC, SADC
    _vval = tuple(i for i in range(0x10) if i not in range(4, 8))
    # описание регистра конфигурации
    _config_reg_ina219 = (bit_field_info(name='RST', position=range(15, 16), valid_values=None, description="Сбрасывает все регистры в значениям по умолчанию."),    # Reset Bit
                          # Bus Voltage Range, 0 - 16 V; 1 - 32 V
                          bit_field_info(name='BRNG', position=range(13, 14), valid_values=None, description="Переключатель диапазонов измеряемого напряжения на шине."),
                          # PGA (Current Shunt Voltage Only). 0 - +/-40 mV; 1 - +/-80 mV; 2 - +/-160 mV; 3 - +/-320 mV;
                          bit_field_info(name='PGA', position=range(11, 13), valid_values=range(4), description="Переключатель диапазонов напряжения на токовом шунте."),
                          # Bus ADC Resolution/Averaging. These bits adjust the Bus ADC resolution (9-, 10-, 11-, or 12-bit) or set the number of samples used when averaging results for the Bus Voltage Register (02h).
                          bit_field_info(name='BADC', position=range(7, 11), valid_values=_vval, description="Биты регулируют разрешение АЦП шины или устанавливают количество выборок для усреднении результатов."),
                          # Shunt ADC Resolution/Averaging. These bits adjust the Shunt ADC resolution (9-, 10-, 11-, or 12-bit) or set the number of samples used when averaging results for the Shunt Voltage Register (01h).
                          bit_field_info(name='SADC', position=range(3, 7), valid_values=_vval, description="Биты регулируют разрешение АЦП токового шунта или устанавливают количество выборок для усреднения результатов."),
                          # Operating Mode. Selects continuous, triggered, or power-down mode of operation. These bits default to continuous shunt and bus measurement mode.
                          # bit_field_info(name='MODE', position=range(3), valid_values=tuple(i for i in range(8) if 4 != i), description="Непрерывный, однократный режим работы или режим пониженного энергопотребления."),
                          bit_field_info(name='CNTNS', position=range(2, 3), valid_values=None, description='1 - Непрерывный режим работы датчика, 0 - по запросу'),
                          # Внимание хотя бы один(!) АЦП должен быть ВКЛЮЧЕН в непрерывном режиме измерений! Смотри "Table 6. Mode Settings"
                          bit_field_info(name='BADC_EN', position=range(1, 2), valid_values=None, description='1 - АЦП напряжения на шине включен, 0 - выключен'),
                          bit_field_info(name='SADC_EN', position=range(0, 1), valid_values=None, description='1 - АЦП напряжения на токовом шунте включен, 0 - выключен'),
                          )

#   функция описана в строке 47 этого файла
#    @staticmethod
#    def _get_conv_time(value: int) -> int:
#        """Возвращает время из полей SADC, BADC в миллисекундах"""
#        _conv_time = 84, 148, 276, 532
#        if value < 8:
#            value &= 0x3  # 0..3
#            return _conv_time[value]
#        # 0x8..0xF. Усреднение по 2, 4, 8, 16, 32, 64, 128 отсчетам
#        value -= 0x08  # 0..7
#        coefficient = 2 ** value
#        return 532 * coefficient

    def __init__(self, adapter: bus_service.BusAdapter, address=0x40, shunt_resistance: float = 0.1):
        """shunt_resistance - сопротивление шунта, [Ом].
        max_shunt_voltage - предельное напряжение на шунте, по модулю, в Вольтах. Которое допускает АЦП."""
        super().__init__(adapter=adapter, address=address, max_shunt_voltage=INA219._shunt_voltage_limit,
                         shunt_resistance=shunt_resistance, fields_info=INA219._config_reg_ina219, internal_fixed_value=0.04096)

    def soft_reset(self):
        self.set_cfg_reg(0b1011_1001_1001_1111)

    def get_shunt_lsb(self)->float:
        """Возвращает цену младшего разряда АЦП токового шунта. Не изменяется при изменении разрядности, что странно!"""
        return INA219._lsb_shunt_voltage

    def get_bus_lsb(self)->float:
        """Возвращает цену младшего разряда АЦП напряжения на шине. Не изменяется при изменении разрядности, что странно!"""
        return INA219._lsb_bus_voltage

    @staticmethod
    def shunt_voltage_range_to_volt(index: int) -> float:
        """Преобразует индекс диапазона напряжения токового шунта в напряжение, Вольт.
        index = 0 +/- 40 mV, 1 +/- 80 mV, 2 +/- 160 mV, 3 +/- 320 mV"""
        check_value(index, range(4),f"Неверный индекс диапазона напряжения токового шунта: {index}")
        return 0.040 * (2 ** index)

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        return 20 * curr_lsb

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """Возвращает 0..3, сырой диапазон напряжений на шунте по макс. току и сопротивлению шунта.
        Запоминает его в поле экземпляра класса"""
        _volt = abs(voltage)
        rng = range(4)
        for index in rng:
            _v_range = INA219.shunt_voltage_range_to_volt(index)
            # print(f"DBG: {_volt}\t{_v_range}")
            if _volt < _v_range:
                # установлю диапазон
                self.current_shunt_voltage_range = index
                return index
        # raise ValueError(f"Не удалось подобрать диапазон напряжения на шунте для напряжения {voltage} Вольт!")
        return rng.stop - 1

    def get_current_config_hr(self) -> tuple:
        return config_ina219(BRNG=self.bus_voltage_range, PGA=self.current_shunt_voltage_range,
                            BADC=self.bus_adc_resolution, SADC=self.shunt_adc_resolution,
                            CNTNS=self.continuous, BADC_EN=self.bus_adc_enabled,
                            SADC_EN=self.shunt_adc_enabled,
                            )
    def get_cct(self, shunt: bool) -> int:
        """Возвращает время в мкс(!) преобразования сигнала в цифровой код и готовности его для чтения по шине!
        Get Current Conversion Time (CCT).
        Если shunt is True, то возвращается время преобразования напряжения на шУнте, иначе
        возвращается время преобразования напряжения на шИне!"""
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            adc_field = self.shunt_adc_resolution
            result = _get_conv_time(adc_field)
            return result
        # BUS
        if not self.bus_adc_enabled:
            return result
        adc_field = self.bus_adc_resolution
        result = _get_conv_time(adc_field)
        return result

#    def start_measurement(self, continuous: bool = True, enable_calibration: bool = False,
#                          enable_shunt_adc: bool = True, enable_bus_adc: bool = True):
#        """Настраивает параметры датчика и запускает процесс измерения.
#        continuous - если Истина, то новое измерение запускается автоматически после завершения предидущего;
#        enable_calibration - если Истина, то происходит калибровка под заданное сопротивление шунта и ток в нагрузке;
#        enable_shunt_adc - включить измерение напряжения на токовом шунте;
#        enable_bus_adc - включить измерение напряжения на шине;
#        Настраивайте параметры датчика ДО вызова этого метода, за исключением:
#             - continuous, enable_shunt_adc, enable_bus_adc"""
#        self.set_config_field(enable_bus_adc, 'BADC_EN')
#        self.set_config_field(enable_shunt_adc, 'SADC_EN')
#        self.set_config_field(continuous, 'CNTNS')
#        if enable_calibration:
#            self.calibrate(self.max_expected_current, self.shunt_resistance)

#        self.set_config()

    @property
    def bus_voltage_range(self) -> bool:
        """Возвращает измеряемый диапазон напряжений на шине. Если Истина то диапазон 0..25 Вольт, иначе 0..16 Вольт."""
        return self.get_config_field('BRNG')

    @bus_voltage_range.setter
    def bus_voltage_range(self, value: bool):
        self.set_config_field(value, 'BRNG')

    @property
    def current_shunt_voltage_range(self) -> int:
        """Возвращает установленный диапазон напряжения на шунте."""
        return self.get_config_field('PGA')

    @current_shunt_voltage_range.setter
    def current_shunt_voltage_range(self, value):
        """Устанавливает диапазон напряжения на шунте 0..3.
        # value     range, mV
        # 0         ±40 mV
        # 1         ±80 mV
        # 2         ±160 mV
        # 3         ±320 mV"""
        self.set_config_field(value, 'PGA')

    @property
    def bus_adc_resolution(self) -> int:
        """Разрешение АЦП на шине в сыром виде.
        0 - 9 бит
        1 - 10 бит
        2 - 11 бит
        3 - 12 бит
        8 - 12 бит
        9..15 - количество отсчетов, которое используется для усреднения результата. 9 - 2 отсчета; 15 - 128 отсчетов,
        смотри 'Table 5. ADC Settings'"""
        return self.get_config_field('BADC')

    @bus_adc_resolution.setter
    def bus_adc_resolution(self, value: int):
        self.set_config_field(value, 'BADC')

    @property
    def shunt_adc_resolution(self) -> int:
        """Разрешение АЦП напряжения на токовом шунте.
        0 - 9 бит
        1 - 10 бит
        2 - 11 бит
        3 - 12 бит
        4, 8 - 12 бит
        9..15 - количество отсчетов, которое используется для усреднения результата. 9 - 2 отсчета; 15 - 128 отсчетов,
        смотри 'Table 5. ADC Settings'"""
        return self.get_config_field('SADC')

    @shunt_adc_resolution.setter
    def shunt_adc_resolution(self, value: int):
        self.set_config_field(value, 'SADC')

    def get_data_status(self) -> ina219_data_status:
        """Возвращает состояние готовности данных, доступны ли данные для считывания?
        Тип возвращаемого значения выбирайте сами!"""
        breg_val = self.get_bus_reg()
        return ina219_data_status(conversion_ready=bool(breg_val & 0x02), math_overflow=bool(breg_val & 0x01))

    def get_voltage(self) -> float:
        _raw = self.get_bus_reg()
        return self.get_bus_lsb() * (_raw >> 3)


ina226_id = namedtuple("ina226_id", "manufacturer_id die_id")
config_ina226 = namedtuple("config_ina226", "AVG VBUSCT VSHCT CNTNS BADC_EN SADC_EN")
voltage_status = namedtuple("voltage_status", "over_voltage under_voltage")
ina226_data_status = namedtuple("ina226_data_status", "shunt_ov shunt_uv bus_ov bus_uv pwr_lim conv_ready alert_ff conv_ready_flag math_overflow alert_pol latch_en")

class INA226(INABaseEx, IBaseSensorEx, Iterator):   # INA219Simple
    """Class for work with TI INA226 sensor"""

    # предел напряжения на шунте из документации, Вольт
    # shunt voltage limit, Volt
    _shunt_voltage_limit = 0.08192
    _lsb_shunt_voltage = 2.5E-6   # 2.5 uV
    _lsb_bus_voltage = 1.25E-3     # 1.25 mV
    # описание регистра конфигурации
    _config_reg_ina226 = (bit_field_info(name='RST', position=range(15, 16), valid_values=None, description="Сбрасывает все регистры в значениям по умолчанию."),    # Reset Bit
                          bit_field_info(name='AVG', position=range(9, 12), valid_values=None, description="Режим усреднения."),
                          bit_field_info(name='VBUSCT', position=range(6, 9), valid_values=None, description="Время преобразования напряжения на шине."),
                          bit_field_info(name='VSHCT', position=range(3, 6), valid_values=None, description="Время преобразования напряжения на токовом шунте."),
                          bit_field_info(name='CNTNS', position=range(2, 3), valid_values=None, description='1 - Непрерывный режим работы датчика, 0 - по запросу'),
                          # Смотри "Table 9. Mode Settings [2:0] Combinations"
                          bit_field_info(name='BADC_EN', position=range(1, 2), valid_values=None,
                                         description='1 - АЦП напряжения на шине включен, 0 - выключен'),
                          bit_field_info(name='SADC_EN', position=range(0, 1), valid_values=None,
                                         description='1 - АЦП напряжения на токовом шунте включен, 0 - выключен'),
                          )

    @staticmethod
    def get_conv_time(value: int = 0) -> int:
        """Возвращает время преобразования в мкс(!)"""
        check_value(value, range(8), f"Неверное значение поля VBUSCT/VSHCT: {value}")
        val = 0.14, 0.204, 0.332, 0.558, 1.1, 2.16, 4.156, 8.244
        return int(1000 * val[value])

    def __init__(self, adapter: bus_service.BusAdapter, address=0x40, shunt_resistance: float = 0.01):
        """shunt_resistance - сопротивление шунта, [Ом].
        max_shunt_voltage - предельное напряжение на шунте, по модулю, в Вольтах. Которое допускает АЦП."""
        super().__init__(adapter=adapter, address=address, max_shunt_voltage=INA226._shunt_voltage_limit,
                         shunt_resistance=shunt_resistance, fields_info=INA226._config_reg_ina226, internal_fixed_value=0.00512)

    @property
    def averaging_mode(self) -> int:
        return self.get_config_field("AVG")

    @property
    def bus_voltage_conv(self) -> int:
        """Возвращает значение (0..7), соответствующее определенному времени преобразования.
        Смотри таблицы 7 и 8 в документации на INA226!"""
        return self.get_config_field("VBUSCT")

    @property
    def shunt_voltage_conv(self) -> int:
        """Возвращает значение (0..7), соответствующее определенному времени преобразования.
        Смотри таблицы 7 и 8 в документации на INA226!"""
        return self.get_config_field("VSHCT")

    def get_current_config_hr(self) -> tuple:
        return config_ina226(AVG=self.averaging_mode, VBUSCT=self.bus_voltage_conv,
                            VSHCT=self.shunt_voltage_conv, CNTNS=self.continuous,
                            BADC_EN=self.bus_adc_enabled, SADC_EN=self.shunt_adc_enabled,
                            )

    def get_shunt_lsb(self)->float:
        """Возвращает цену младшего разряда АЦП токового шунта. Не изменяется при изменении разрядности, что странно!"""
        return INA226._lsb_shunt_voltage

    def get_bus_lsb(self)->float:
        """Возвращает цену младшего разряда АЦП напряжения на шине. Не изменяется при изменении разрядности, что странно!"""
        return INA226._lsb_bus_voltage

    def get_pwr_lsb(self, curr_lsb: float) -> float:
        """Вычисляет цену наименьшего младшего разряда регистра мощности по цене
        наименьшего значащего бита регистра тока"""
        return 25 * curr_lsb

    def get_mask_enable(self) -> int:
        """Возвращает содержимое регистра Mask/Enable."""
        return self.get_16bit_reg(0x06, "H")

    def choose_shunt_voltage_range(self, voltage: float) -> int:
        """Заглушка. Работа не требуется, так как у INA226 один(!) диапазон напряжения на шунте!"""
        pass

    def get_cct(self, shunt: bool) -> int:
        """Возвращает время в мкс(!) преобразования сигнала в цифровой код и готовности его для чтения по шине!
        Get Current Conversion Time (CCT).
        Если shunt is True, то возвращается время преобразования напряжения на шУнте, иначе
        возвращается время преобразования напряжения на шИне!"""
        result = 0
        if shunt:
            if not self.shunt_adc_enabled:
                return result
            result = INA226.get_conv_time(self.shunt_voltage_conv)
            return result
        # BUS
        if not self.bus_adc_enabled:
            return result
        result = INA226.get_conv_time(self.bus_voltage_conv)
        return result

    # BaseSensorEx
    def get_id(self) -> ina226_id:
        man_id, die_id = self.get_16bit_reg(0xFE, 'H'), self.get_16bit_reg(0xFF, 'H')
        return ina226_id(manufacturer_id=man_id, die_id=die_id)

    def soft_reset(self):
        self.set_cfg_reg(0b1100_0001_0010_0111)

    def get_data_status(self) -> ina226_data_status:
        """Возвращает именованный кортеж, состояния данных."""
        me_reg = self.get_mask_enable()
        # print(f"DBG: me_reg: 0x{me_reg:x}")
        # print(f"conv_ready_flag: {me_reg & 0x08}")
        # генератор масок. в обратном(!) порядке в соответствии с расположением полей в конструкторе
        g_masks = (1 << i for i in range(15, -1, -1) if i not in range(5, 10))
        # генератор значений для именованного кортежа (named tuple)
        g_nt_vals = (bool(me_reg & mask) for mask in g_masks)
        # в micropython у namedtuple отсутствует классовый метод _make, поэтому придется страдать ! :-(
        # "shunt_ov shunt_uv bus_ov bus_uv pwr_lim conv_ready alert_ff conv_ready_flag math_overflow alert_pol latch_en"
        return ina226_data_status(shunt_ov=next(g_nt_vals), shunt_uv=next(g_nt_vals), bus_ov=next(g_nt_vals), bus_uv=next(g_nt_vals),
                                  pwr_lim=next(g_nt_vals), conv_ready=next(g_nt_vals), alert_ff=next(g_nt_vals),
                                  conv_ready_flag=next(g_nt_vals), math_overflow=next(g_nt_vals), alert_pol=next(g_nt_vals),
                                  latch_en=next(g_nt_vals))

    def get_voltage(self) -> float:
        return self.get_bus_lsb() * self.get_bus_reg()

    # IBaseSensorEx
    def get_measurement_value(self, value_index: int = 0):
        """Возвращает измеренное датчиком значение(значения).
        Если 0 == value_index, то возвращает напряжение на шунте.
        Если 1 == value_index, то возвращает напряжение на шине питания."""
        if 0 == value_index:
            return self.get_shunt_voltage()
        if 1 == value_index:
            return self.get_voltage()
