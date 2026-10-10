# MicroPython
# mail: goctaprog@gmail.com
# MIT license

from sensor_pack.base_sensor import BaseSensor


def _axis_to_int(axis: [set, str]) -> int:
    """преобразует входное множество, содержащее 'X', 'Y', 'Z' в int от 0 до 7 включительно.
    '' - 0; 'X' - 1; 'X', 'Y' - 3; 'X', 'Y', 'Z' - 7"""
    _axis = 0
    _str_axis = 'XYZ'
    for index, axs in enumerate(_str_axis):
        if axs in axis or str.lower(axis) in axis:
            _axis += 2 ** index

    return _axis


def _axis_name_to_int(axis_name: str) -> int:
    """Преобразует имя оси ('x', 'y', 'z', 'X', 'Y', 'Z') в число 0(X), 1(Y), 2(Z)"""
    an = axis_name.lower()
    if not ord(an[0]) in range(120, 123):
        raise ValueError(f"Invalid axis name: {axis_name}")
    return ord(an[0]) - 120  # 0, 1, 2


def check_axis_value(axis: int):
    """Проверяет числовое значение оси. Оно должно быть 0(X), 1(Y), 2(Z)"""
    if axis not in range(3):
        raise ValueError(f"Invalid axis name: {axis}")


def _axis_number_to_str(axis: int) -> str:
    """Преобразует номер оси 0(x), 1(Y), 2(Z) в строку 'x', 'y', 'z'"""
    check_axis_value(axis)
    an = "x", "y", "z"
    return an[axis]


def axis_name_to_reg_addr(axis_name: int, offset: int, multiplier: int) -> int:
    """Преобразует имя оси 0('x'), 1('y'), 2('z')) в адрес соответствующего регистра"""
    return offset + multiplier * axis_name


class GeoMagneticSensor(BaseSensor):
    """Методы для датчика магнитного поля (Земли в том числе :-) )"""
    def get_axis(self, axis: [int, str]) -> [int, tuple]:
        """Возвращает X(axis==0), Y(axis==1) или Z(axis==2) составляющую магнитного поля.
        Returns the X(axis==0), Y(axis==1) or Z(axis==2) component of the magnetic field.
        Если axis = -1, то метод возвращает все составляющие в виде кортежа: X, Y, Z"""
        if isinstance(axis, int) and -1 == axis:
            return self._get_all_meas_result()
        return self.get_meas_result(axis)

    def _get_all_meas_result(self) -> tuple:
        """Для наибыстрейшего считывания за один вызов всех результатов измерений из датчика по
        относительно медленной шине! Для переопределения программистом!!!"""
        raise NotImplementedError

    def is_data_ready(self) -> bool:
        """возвращает Истина, когда данные готовы для считывания методом get_meas_result
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def is_continuous_meas_mode(self):
        """Возвращает Истина, когда включен режим периодических измерений!
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def is_single_meas_mode(self):
        """Возвращает Истина, когда включен режим однократных измерений (по запросу)!
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def in_standby_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в режиме ожидания(низкое потребление мощности)!
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def perform_self_test(self):
        """Выполняет самотестирование датчика
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def get_conversion_cycle_time(self) -> int:
        """Возвращает время преобразования сигнала измеряемой величины в значение, готовое к считыванию.
        Это могут быть миллисекунды или микросекунды.
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def get_meas_result(self, axis_name: [str, int]) -> int:
        """Возвращает измеренное значение по оси axis_name в 'сырых'/инженерных единицах"""
        _axis = axis_name if isinstance(axis_name, int) else _axis_name_to_int(axis_name)
        return self.read_raw(_axis)

    def read_raw(self, axis: int) -> int:
        """Что бы никогда не трогать метод get_meas_result.
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def get_status(self):
        """Возвращает состояние датчика.
        Для переопределения программистом!!!"""
        raise NotImplementedError

    def start_measure(self):
        """Запускает однократное или периодические измерение(я).
        Для переопределения программистом!!!"""
        raise NotImplementedError
