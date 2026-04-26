# micropython
# mail: goctaprog@gmail.com
# MIT license
# import struct
import array

from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, Iterator, check_value, all_none
import micropython
# from micropython import const
# from struct import pack_into


def _check_integration_time(integr_time: int):
    """Проверяет параметр integr_time (0..5) на правильность
    Соответствие параметр integr_time и времени интегрирования в мс
    0 - 40 мс
    1 - 80 мс
    2 - 160 мс
    3 - 320 мс
    4 - 640 мс
    5 - 1280 мс"""
    check_value(integr_time, range(6), f"Неверное значение параметра integration_time: {integr_time}")


def get_g_max_lux(integr_time: int) -> tuple[float, float]:
    """Возвращает G_SENSITIVITY и MAX. DETECTABLE LUX по коэффициенту времени интеграции 0..5,
    (G_SENSITIVITY, MAX. DETECTABLE LUX)"""
    _check_integration_time(integr_time)
    k = 1 / (1 << integr_time)
    return 0.25168 * k, 16496 * k


class VEML6040(DeviceEx, Iterator):
    """Класс, управляющий RGBW датчиком цвета, VEML6040 от Vishay"""

    def __init__(self, adapter: bus_service.BusAdapter, address=0x10):
        """i2c - объект класса I2C; address - адрес датчика на шине. Он не изменяется!"""
        # check_value(address, range(0x40, 0x80), f"Неверное значение адреса I2C устройства: {address:x}")
        super().__init__(adapter, address, False)
        # включаю внутреннее тактирование, автоинкремент адреса, нормальный рабочий режим
        # self._mode_1(None, False, True, False)
        self._integration_time = self._trig = self._auto = self._shutdown = None
        self._buf_4 = array.array("H", [0 for _ in range(4)])  # беззнаковый двух байтные элементы
        self._get_settings()    # читаю настройки из датчика

    def _get_settings(self):
        """Возвращает текущие настройки датчика в поля класса"""
        _conf = self._settings()     # читаю два байта, но только один байт используется под настройки
        #           integration time,       trig,               auto/manual,         shutdown
        result = (0b0111_0000 & _conf) >> 4, 0 != (0b100 & _conf), 0 == (0b10 & _conf), 0b01 & _conf
        self._integration_time, self._trig, self._auto, self._shutdown = result

    @micropython.native
    def get_conversion_cycle_time(self) -> int:
        """возвращает время преобразования в [мc] датчиком данных цвета"""
        _check_integration_time(self._integration_time)
        return 40 * (1 << self._integration_time)

    def _settings(self,
                  it: [int, None] = None,   # bit 6..4,
                  trig: [bool, None] = None,   # bit 3, 0 = no trigger, 1 = trigger one time detect cycle
                  af: [bool, None] = None,   # bit 2, 0 = auto mode, 1 = force mode
                  sd: [bool, None] = None,   # bit 1, 0 = enable color sensor, 1 - disable color sensor
                  ):
        """Регистр CONF. Если все параметры в None, возвращает содержимое регистра"""
        val = self.read_reg(0x00, 2)[0]
        if all_none(it, trig, af, sd):
            # print(f"DBG _settings before: 0x{val:x}")
            return val
        if it is not None:
            val &= ~0b0111_0000  # mask
            val |= it << 4
        if trig is not None:
            val &= ~(1 << 2)  # mask
            val |= trig << 2
        if af is not None:
            val &= ~(1 << 1)  # mask
            val |= af << 1
        if sd is not None:
            val &= 0xFE  # mask
            val |= sd
        # print(f"DBG _settings after: 0x{val:x}")
        self.write_reg(0x00, val, 2)

    def get_colors(self) -> tuple:
        """Возвращает данные 4-х цветовых каналов: red(красный), green(зеленый), blue(синий), white(белый)"""
        buf = self._buf_4
        for index in range(len(buf)):
            buf[index] = self.unpack(fmt_char="H", source=self.read_reg(0x08 + index, 2))[0]
        return tuple(buf)

    def start_measurement(self, integr_time: int, auto_mode: bool):
        """Запускает процесс измерения в автоматическом (auto_mode == True) или однократном (auto_mode == False)
        integr_time = 0..5
        0 - 40 мс
        1 - 80 мс
        2 - 160 мс
        3 - 320 мс
        4 - 640 мс
        5 - 1280 мс"""
        _check_integration_time(integr_time)
        self._settings(it=integr_time, trig=not auto_mode, af=not auto_mode)
        self._get_settings()    # обновляю настройки

    @property
    def integration_time(self) -> int:
        return self._integration_time

    @property
    def auto_mode(self) -> bool:
        return 0 != self._auto

    @property
    def shutdown(self) -> bool:
        return 0 != self._shutdown

    @shutdown.setter
    def shutdown(self, value: bool = True):
        """ВКлючает датчик, value = False. ВЫКлючает датчик, value = True."""
        self._settings(None, None, None, value)
        self._shutdown = value

    # Iterator
    def __next__(self) -> [tuple, None]:
        """Часть протокола итератора"""
        if self.shutdown or not self.auto_mode:
            return None
        return self.get_colors()
