"""
MicroPython SPG4X sensor 'driver'
"""
# micropython
# MIT license
# Copyright (c) 2025 Roman Shevchik   kolbasilyvasily@yandex.ru

# from micropython import const
from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, IDentifier, Iterator, check_value
from sensor_pack_2.crc_mod import crc8
import time

# номер датчика от производителя
serial_number_sgp4x = namedtuple("serial_number_sgp4x", "word_0 word_1 word_2")
# данные, полученные от датчика:
# VOC - индекс летучих органических соединений;
# NOx - индекс оксидов азота;
# raw - если Истина, то поля VOX (летучие органические вещества) и NOx (оксиды азота (NO и NO2), образующиеся при горении) содержат сырые(!) данные,
# которые требуется обработать c помощью Sensirion’s Gas Index Algorithm (https://pypi.org/project/sensirion-gas-index-algorithm/);
measured_values_sgp4x = namedtuple("measured_values_sgp4x", "VOC NOx")


# IBaseSensorEx
class SGP4X(IDentifier, Iterator):
    """Программное представление SGP4X - цифровых датчиков качества воздуха.
     Измеряет летучие органические соединения (ЛОС) и оксиды азота (NOx, только SGP41)."""
    # для SGP41!; Эта команда запускает кондиционирование, то есть пиксель VOC будет работать при той же температуре,
    # что и при вызове команды sgp41_measure_raw_signals, в то время как пиксель NOx будет работать при другой температуре
    # для кондиционирования. Ответ от датчика 3 байта. Время ожидания x/50 мс.
    _cmd_execute_conditioning = 0x2612
    # Эта команда запускает/продолжает режим измерения VOC, и возвращает измеренный необработанный сигнал RAW_VOC
    # в виде 2 байтов (+ 1 байт CRC). Ответ от датчика 3 байта. Время ожидания 30/50 мс.
    _cmd_measure_raw_signal = 0x260F
    # Эта команда запускает встроенную самопроверку целостности как нагревателя, так и MOX-материала.
    # Ответ от датчика 3 (для SGP40) или 6 (для SGP41) байт. Время ожидания 320 мс.
    _cmd_execute_self_test = 0x280E
    # Эта команда выключает нагреватель и останавливает измерение. Датчик переходит в режим ожидания.
    # Ответ от датчика 0 байт. Время ожидания 1 мс.
    _cmd_turn_heater_off = 0x3615
    # Эта команда выдает десятичный серийный номер датчика.
    # Ответ от датчика 9 байт. Время ожидания 1 мс.
    _cmd_get_serial_number = 0x3682
    # параметры ответа от датчика
    answer_params_sgp4x = namedtuple("answer_params_sgp4x", "length wait_time")

    @staticmethod
    def _calc_crc(sequence: bytes) -> int:
        """Обертка для короткого вызова."""
        return crc8(sequence, polynomial=0x31, init_value=0xFF)


    def __init__(self, adapter: bus_service.BusAdapter, address=0x59, sensor_id: int = 0, check_crc: bool = True):
        """
        address - адрес на шине I2C;
        sensor_id - идентификатор датчика:
            0 - SGP40;
            1 - SGP41;
        check_crc - если Истина, то ответ от датчика проверяется путем подсчета CRC и их сравнения."""
        check_value(address, range(0x59, 0x5A), f"Неверный адрес устройства: {address}")
        check_value(sensor_id, range(2), f"Неверный sensor id: {sensor_id}")
        self._connector = DeviceEx(adapter=adapter, address=address, big_byte_order=True)
        #
        self._check_crc = check_crc
        # 0 - SGP40; 1 - SGP41
        self._sensor_id = sensor_id
        self._last_cmd_code = None
        # сохраняю, чтобы не вызывать 125 раз
        self._byte_order = self._connector._get_byteorder_as_str()
        # для пересылки по шине
        self._buf_3 = bytearray(3)
        self._buf_6 = bytearray(6)
        self._cmd_buf = bytearray(8)
        self._buf_9 = bytearray(9)

    def get_last_cmd_code(self) -> int:
        """Возвращает последний код команды, переданный по шине данных в датчик"""
        return self._last_cmd_code

    @staticmethod
    def _get_answer_params(cmd_code: int, sensor_id: int = 0) -> answer_params_sgp4x:
        """Возвращает параметры ответа от датчика по коду команды cmd_code и id датчика. 0 - SGP40, 1 - SGP41, ... ."""
        _wt, _l = None, None

        if SGP4X._cmd_turn_heater_off == cmd_code:
            _l = 0
            _wt = 1
        if SGP4X._cmd_execute_self_test == cmd_code:
            _l = 3
            _wt = 320
        if 1 == sensor_id and SGP4X._cmd_execute_conditioning == cmd_code:
            _l = 3  # SGP41
            _wt = 50
        if SGP4X._cmd_measure_raw_signal == cmd_code:
            if 0 == sensor_id:
                _l = 3  # для SGP40
                _wt = 30
            else:
                _l = 6  # для SGP4Х
                _wt = 50
        if SGP4X._cmd_get_serial_number == cmd_code:
            _l = 9
            _wt = 1

        if _wt is None or _l is None:
            raise ValueError(f"Неверный код команды: {cmd_code} или sensor id: {sensor_id}!")
        return SGP4X.answer_params_sgp4x(length=_l, wait_time=_wt)

    @staticmethod
    def _get_data_place(answ_length: int, data: bool = True) -> [None, iter]:
        """Возвращает диапазон индексов байт в буфере с ответом от датчика,
        содержащих данные (data is True) или CRC (data is False)."""
        check_value(answ_length, (0, 3, 6, 9), f"Неверная длина ответа в байтах: {answ_length}!")
        if 0 == answ_length:
            return None
        # answ_length = 0, 3, 6
        for index in range(answ_length // 3):
            _start = 3 * index
            if data:  # (0, 2), (3, 5), (6, 8) - индексы данных
                yield range(_start, 2 + _start)
            else:  # (2, 3), (5, 6), (8, 9)  - индексы CRC
                yield range(2 + _start, 3 + _start)

    @staticmethod
    def _check_answer_length(answ_length: int):
        check_value(value=answ_length, valid_range=(0, 3, 6, 9),
                    error_msg=f"Неверная длина ответа в байтах: {answ_length}!")

    @staticmethod
    def _check_rh_temp(rh: [None, int], temp: [None, int]):
        """Проверяет относительную влажность (rh в %) и температуру (temp в гр. Цельсия)
        на принадлежность к верному диапазону 0..100 и -45..130 соответственно."""
        _val, _valid_rng = None, None
        _err_msg = f"Значение {_val} вне допустимого диапазона {_valid_rng}!"
        if rh:
            _val, _valid_rng = rh, range(101)
        if temp:
            _val, _valid_rng = temp, range(-45, 131)
        #
        check_value(_val, _valid_rng, _err_msg)

    @staticmethod
    def _get_raw_relhum(rel_hum: int) -> int:
        """Возвращает сырое значение относительной влажности.
        rel_hum - значение относительной влажности в %;"""
        SGP4X._check_rh_temp(rh=rel_hum, temp=None)
        return round(65.35 * rel_hum)

    @staticmethod
    def _get_raw_temp(temperature: int) -> int:
        """Возвращает сырое значение температуры.
        temperature - значение температуры в градусах Цельсия;"""
        SGP4X._check_rh_temp(rh=None, temp=temperature)
        return round(374.4857142857 * (45 + temperature))

    def _get_buf_by_answ_length(self, answ_length: int) -> [None, bytes]:
        """Возвращает буфер по длине ответа от датчика в байтах - answ_length."""
        SGP4X._check_answer_length(answ_length)
        #
        if 0 == answ_length:
            return None
        if 3 == answ_length:
            return self._buf_3
        if 6 == answ_length:
            return self._buf_6
        if 9 == answ_length:
            return self._buf_9
        raise ValueError(f"Неверная длина буфера: {answ_length}!")

    @staticmethod
    def _check_answer(answer: bytes, answ_length: int) -> bool:
        """Проверяет ответ от датчика путем сравнения рассчитанной и полученной из ответа CRC.
        Возвращет Истина, когда ответ от датчика верен!
        answer - байтовый массив ответа от датчика.
        answ_length - длина ответа от датчика в байтах."""
        SGP4X._check_answer_length(answ_length)
        for data_place in SGP4X._get_data_place(answ_length):
            calculated_crc = SGP4X._calc_crc(answer[data_place.start:data_place.stop])
            crc_from_buf = answer[data_place.stop]
            if calculated_crc != crc_from_buf:
                raise ValueError(
                    f"Неверная CRC! Вычислено: {calculated_crc}. CRC из буфера: {crc_from_buf}; Длина буфера: {len(answer)} байт.")
        return True

    def _read_answer(self) -> [bytes, None]:
        """Читает ответ на команду, переданную методом _send_command.
        Возвращает ссылку на буфер с принятыми данными.
        Проверяет CRC"""
        _cmd = self.get_last_cmd_code()
        _ap = SGP4X._get_answer_params(_cmd, self.get_sensor_id())
        _al = _ap.length
        if 0 == _al:
            return None
        _buf = self._get_buf_by_answ_length(_al)
        self._connector.read_to_buf(_buf)
        # ответ считан
        if self._check_crc:
            SGP4X._check_answer(_buf, _al)
        return _buf

    def _send_command_and_read_answer(self, cmd_code: int, unpack_format: str, with_params: bool = False,
                                      rel_hum: int = None, temperature: int = None):
        if with_params:
            SGP4X._check_rh_temp(rel_hum, temperature)
            raw_temp = SGP4X._get_raw_temp(temperature)
            raw_rh = SGP4X._get_raw_relhum(rel_hum)
            self._send_command(cmd_code, raw_rh, raw_temp)
        else:
            self._send_command(cmd_code)
        _ap = SGP4X._get_answer_params(cmd_code, self.get_sensor_id())
        time.sleep_ms(_ap.wait_time)
        _buf = self._read_answer()
        return self._connector.unpack(unpack_format, _buf)

    def get_sensor_id(self) -> int:
        """Возвращает идентификатор датчика:
            0 - SGP40;
            1 - SGP41;"""
        return self._sensor_id

    def get_id(self) -> serial_number_sgp4x:
        """Возвращает серийный номер датчика. Три двухбайтных слова."""
        _t = self._send_command_and_read_answer(cmd_code=SGP4X._cmd_get_serial_number, unpack_format="HBHBH")
        return serial_number_sgp4x(word_0=_t[0], word_1=_t[2], word_2=_t[4])

    def turn_heater_off(self):
        """Отключает нагреватель датчика."""
        self._send_command(SGP4X._cmd_turn_heater_off)

    def execute_self_test(self) -> int:
        """Команда execute_self_test выполняет встроенное самотестирование датчика SGP4X, проверяя целостность нагревательной
        пластины и MOX-материала. После выполнения теста датчик возвращает результат в виде 2-байтового значения:
            0xD400 — все тесты пройдены успешно
            0x4B00 — один или несколько тестов завершились с ошибкой.

        Если команда вызывается в режиме ожидания (idle mode), датчик после теста вернется в этот же режим.
        При вызове во время режима измерения VOC нагреватель останется включенным"""
        _t = self._send_command_and_read_answer(cmd_code=SGP4X._cmd_execute_self_test, unpack_format="HB")
        return _t[0]

    def execute_conditioning(self, rel_hum: int = 50, temperature: int = 25) -> measured_values_sgp4x:
        """Отправка команд sgp41_execute_conditioning и sgp41_measure_raw_signals переводит датчик в режим непрерывной работы.
        В течение 5 мс после отправки любой из двух команд, ток потребления возрастает на 20%!
        Рекомендуется выполнять эту команду в течение 10 с,
        однако нельзя превышать это время, чтобы избежать повреждения датчика!"""
        t = self._send_command_and_read_answer(cmd_code=SGP4X._cmd_execute_conditioning, unpack_format="HB",
                                               with_params=True, rel_hum=rel_hum, temperature=temperature)
        return measured_values_sgp4x(VOC=t[0], NOx=None)

    def measure_raw_signal(self, rel_hum: int = 50, temperature: int = 25) -> measured_values_sgp4x:
        """Команда запускает/продолжает режим измерения VOC. Она запускает одно измерение необработанного сигнала (SRAW_VOC),
        которое возвращается через 30 мс. Необработанное значение сигнала в тактах предоставляется в виде одного 16-битного слова,
        за которым следует один байт CRC. Необработанный сигнал в тактах пропорционален логарифму сопротивления датчика.
        Этот сигнал используется в качестве входного сигнала для алгоритма газового индекса Sensirion для получения обработанного индекса VOC.
        Обычно измерение выполняется каждую секунду путем повторного вызова команды sgp40_measure_raw_signal каждую секунду
        без выключения нагревателя. Для выхода из режима измерения VOC, ведущее устройство вызывает команду sgp4x_turn_heater_off,
        которая отключает нагревательную пластину и переводит датчик в режим ожидания.
        ---
        Отправка команд sgp41_execute_conditioning и sgp41_measure_raw_signals переводит датчик в режим непрерывной работы.
        В течение 5 мс после отправки любой из двух команд, ток потребления возрастает на 20%!"""
        sen_id = self.get_sensor_id()
        fmt = "HBHB" if sen_id else "HB"
        _t = self._send_command_and_read_answer(cmd_code=SGP4X._cmd_measure_raw_signal, unpack_format=fmt,
                                                with_params=True, rel_hum=rel_hum, temperature=temperature)
        _NOx = _t[2] if sen_id else None
        return measured_values_sgp4x(VOC=_t[0], NOx=_NOx)

    def _send_command(self, cmd_code: int, raw_rel_hum: [None, int] = None, raw_temp: [None, int] = None):
        """Передает команду датчику по шине.
        cmd_code - код команды;
        raw_rel_hum - сырое значение относительной влажности;
        raw_temp - сырое значение температуры воздуха;"""
        _cmd_buf = None
        _cmd_with_params = all((raw_rel_hum, raw_temp))
        _bo = self._byte_order[0]
        if _cmd_with_params:
            # Должны быть заданы и температура и отн. влажность!
            _cmd_buf = self._cmd_buf
            _cmd_buf[0:2] = cmd_code.to_bytes(2, _bo)
            _cmd_buf[2:4] = raw_rel_hum.to_bytes(2, _bo)
            _cmd_buf[5:7] = raw_temp.to_bytes(2, _bo)
            #
            _cmd_buf[4] = SGP4X._calc_crc(_cmd_buf[2:4])
            _cmd_buf[7] = SGP4X._calc_crc(_cmd_buf[5:7])
        else:
            _cmd_buf = cmd_code.to_bytes(2, _bo)
        #
        self._connector.write(_cmd_buf)
        self._last_cmd_code = cmd_code
