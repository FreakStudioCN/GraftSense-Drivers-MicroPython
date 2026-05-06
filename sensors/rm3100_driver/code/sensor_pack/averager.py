"""
MIT License
Copyright (c) 2022 Roman Shevchik

Усреднитель/Averager.
Хорошо подходит для усреденения физических величин, считанных с датчиков (температура, давление, влажность).
Well suited for averaging physical quantities read from sensors (temperature, pressure, humidity)."""
import array


class Averager:
    """класс для усреднения значений, поступающих методом put. спроектирован для MCU, с их ограниченными ресурсами.
    class for averaging the values coming from the put method. designed for the MCU, with their limited resources."""
    def __init__(self, items_count: int = 8, type_code: str = "b"):
        """items_count - количество значений, среднее арифметическое которых станет основой (после накопления)
        для расчета усредненного значения в дальнейшем.
        sum_count - the number of values whose arithmetic mean will become the basis (after accumulation) for
        calculating the average value in the future"""
        if type_code not in ("b", "B", "h", "H", "i", "I", "l", "L", "q", "Q"):     # , "f", "d"):
            raise ValueError(f"Invalid type_code value: {type_code}")
        self._max = items_count
        self._index = 0
        self._cnt = 0
        self.arr = array.array(type_code, [0 for _ in range(items_count)])

    def put(self, value: int) -> int:
        """Возвращает среднее арифметическое, основанное на сумме накопленных элементов.
        Returns the arithmetic mean based on the sum of the accumulated elements."""
        self.arr[self._index] = value
        if self._index < self._max - 1:
            self._index += 1
        else:
            self._index = 0
        ###
        if self._cnt < self._max:
            self._cnt += 1

        return sum(self.arr) // self._cnt
