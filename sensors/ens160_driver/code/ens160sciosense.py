# micropython
# MIT license
# Copyright (c) 2022 Roman Shevchik   kolbasilyvasily@yandex.ru

from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import IBaseSensorEx, DeviceEx, IDentifier, Iterator, check_value

ens160_firmware_version = namedtuple("ens160_firmware_version", "major minor release")
# eCO2 - количество эквивалента углекислого газа
# TVOC - общие летучие органические соединения. Это термин, используемый для обозначения общей концентрации различных
#        летучих органических соединений в воздухе, которые могут присутствовать в помещении или в окружающей среде.
# AQI  - расчетный индекс качества воздуха в соответствии с UBA(UmweltBundesAmt – German Federal Environmental Agency)
ens160_air_params = namedtuple("ens160_air_params", "eco2 tvoc aqi")
# statas (bit 7) - High indicates that an OPMODE is running
# stater (bit 6) - High indicates that an error is detected. E.g. Invalid Operating Mode has been selected.
# validity_flag (bit 2, 3) - Status: 0 - normal operation; 1 - Warm-Up phase; 2 - Initial Start-Up phase; 3 - Invalid output;
# new_data (bit 1) - High indicates that a new data is available in the DATA_x registers. Cleared automatically at first DATA_x read.
# new_gpr (bit 0) - High indicates that a new data is available in the GPR_READx registers. Cleared automatically at first GPR_READx read.
ens160_status = namedtuple("ens160_status", "stat_as stat_error validity_flag new_data new_gpr")
# int_pol (bit 6) - INTn pin polarity: 0- Active low (Default); 1 - Active high
# int_cfg (bit 5) - INTn pin drive: 0 - Open drain; 1 - Push / Pull
# int_gpr (bit 3) - INTn pin asserted when new data is presented in the General Purpose Read Registers
# int_dat (bit 1) - INTn pin asserted when new data is presented in the DATA_XXX Registers
# int_en  (bit 0)- INTn pin is enabled for the functions above
ens160_config = namedtuple("ens160_config", "int_pol int_cfg int_gpr int_dat int_en")


#def _to_raw_status(st: ens160_status) -> int:
#    n_bits = 7, 6, 2, 1, 0
#    val_gen = (int(st[i]) << n_bits[i] for i in range(len(n_bits)))
#    _cfg = 0b1100_0011 & sum(map(lambda x: x, val_gen))
#    return _cfg | (st.validity_flag << 2)



class Ens160(IBaseSensorEx, IDentifier, Iterator):
    """Класс для работы с цифровым металоксидным мультигазовым датчиком ENS160."""
    _CRC_POLY = 0x1D

    @staticmethod
    def _to_raw_config(cfg: ens160_config) -> int:
        """Преобразует именованныый кортеж ens160_config в int"""
        n_bits = 6, 5, 3, 1, 0
        val_gen = (int(cfg[i]) << n_bits[i] for i in range(len(n_bits)))
        _cfg = sum(map(lambda x: x, val_gen))
        return _cfg

    @staticmethod
    def _to_config(raw_cfg: int) -> ens160_config:
        """Преобразует int в именованныый кортеж ens160_config"""
        n_bits = 6, 5, 3, 1, 0
        mask_gen = (1 << n_bit for n_bit in n_bits)
        bit_val_gen = (bool(next(mask_gen) & raw_cfg) for _ in n_bits)
        return ens160_config(int_pol=next(bit_val_gen), int_cfg=next(bit_val_gen), int_gpr=next(bit_val_gen),
                             int_dat=next(bit_val_gen), int_en=next(bit_val_gen))

    @staticmethod
    def _to_status(st: int) -> ens160_status:
        """Преобразует int в именованныый кортеж ens160_status"""
        n_bits = 7, 6, 1, 0
        mask_gen = (1 << n_bit for n_bit in n_bits)
        bit_val_gen = (bool(next(mask_gen) & st) for _ in n_bits)
        return ens160_status(stat_as=next(bit_val_gen), stat_error=next(bit_val_gen), validity_flag=(0b1100 & st) >> 2,
                             new_data=next(bit_val_gen), new_gpr=next(bit_val_gen))

    @staticmethod
    def _crc8(sequence, polynomial: int, init_value: int):
        """какое-то особое CRC8 от sciosense!
        Мало того, кто-то "очень" умный придумал читать CRC из датчика, вместо того,
        чтобы передать его вместе с результатами одним пакетом!"""
        crc = init_value & 0xFF
        for item in sequence:
            tmp = 0xFF & ((crc << 1) ^ item)
            if 0 == crc & 0x80:
                crc = tmp
            else:
                crc = tmp ^ polynomial
        return crc

    def __init__(self, adapter: bus_service.I2cAdapter, address: int = 0x52, check_crc: bool = True):
        """Адаптер шины, адрес на шине, проверять CRC или нет."""
        self._connector = DeviceEx(adapter=adapter, address=address, big_byte_order=False)
        self._check_crc = check_crc

    def _read_register(self, reg_addr, bytes_count=2) -> bytes:
        """считывает из регистра датчика значение.
        bytes_count - число считываемых байт, начиная с адреса reg_addr"""
        before = 0
        if self._check_crc:
            before = self._get_last_checksum()   # читаю crc с датчика
        conn = self._connector
        b = conn.read_reg(reg_addr, bytes_count)
        if self._check_crc:
            if 0 <= reg_addr < 0x38:
                crc = Ens160._crc8(b, Ens160._CRC_POLY, before)  # вычисляю crc из считанных данных
                after = self._get_last_checksum()   # читаю crc с датчика
                if crc != after:  # сравниваю рассчитанный crc и считанный с датчика
                    raise IOError(f"Input data broken! Bad CRC! Calculated crc8: {hex(crc)} != {hex(after)}")
                
        return b

    def __del__(self):
        # деструктор не вызывается MicroPython
        self._set_mode(0x00)     # уходим в deep sleep

    # Identifier
    def get_id(self) -> int:
        """Возвращает 'the part number' из датчика"""
        reg_val = self._read_register(0x00, 2)
        return self._connector.unpack("H", reg_val)[0]

    def soft_reset(self):
        """Програмный сброс датчика"""
        self._set_mode(0xF0)

    def _set_mode(self, new_mode: int):
        """Устанавливает режим работы датчика.
        см. 16.2.2 OPMODE (адрес 0x10) в официальной документации.
        Режим работы:
                7:0     Описание
                --------------------------------------------
                0x00:   Режим DEEP SLEEP (режим ожидания с низким энергопотреблением)
                0x01:   Режим IDLE (низкое энергопотребление)
                0x02:   СТАНДАРТНЫЙ режим обнаружения газа (нормальный режим)
                0xF0:   Програмный сброс"""
        nm = check_value(new_mode, (0, 1, 2, 0xF0), f"Invalid mode value: {new_mode}")
        self._connector.write_reg(0x10, nm, 1)

    def _get_mode(self) -> int:
        """Возвращает текущий режим работы датчика"""
        reg_val = self._read_register(0x10, 1)
        return reg_val[0]

    def get_config(self, raw: bool = True) -> [int, ens160_config]:
        """Возвращает текущие настройки датчика. Смотри таблицу 19 в официальной документации.
        если raw - в Истина, то возвращается int, иначе ens160_config."""
        raw_val = self._read_register(0x11, 1)[0]
        if raw:
            return raw_val
        return Ens160._to_config(raw_val)

    def set_config(self, new_config: [int, ens160_config]):
        """Настраивает датчик. Смотри таблицу 19 в официальной документации"""
        raw_cfg = 0
        if isinstance(new_config, int):
            raw_cfg = new_config
        if isinstance(new_config, ens160_config):
            raw_cfg = Ens160._to_raw_config(new_config)
        #
        self._connector.write_reg(0x11, raw_cfg, 1)

    def _exec_cmd(self, cmd: int) -> bytes:
        """Для внутреннего использования!
        0x00: ENS160_COMMAND_NOP;
        0x0E: ENS160_COMMAND_GET_APPVER – Get FW Version;
        0xCC: ENS160_COMMAND_CLRGPR Clears GPR Read Registers;"""
        check_value(cmd, (0x00, 0x0E, 0xCC), f"Invalid command code: {cmd}")
        self._connector.write_reg(0x12, cmd, 1)
        return self._read_register(0x48, 8)

    def set_ambient_temp(self, value_in_celsius: float):
        """Записывает в ENS160 датчик температуру окружающей среды, для компенсации!
        Значение в градусах Цельсия! Это значение должно быть считано с датчика температуры!
        Оно должно быть правильным и в допустимом диапазоне!"""
        t = int(64*(273.15+value_in_celsius))
        self._connector.write_reg(0x13, t, 2)

    def set_humidity(self, rel_hum: int):
        """Записывает в ENS160 датчик относительную влажность, для компенсации! значение в процентах!"""
        check_value(rel_hum, range(101), f"Invalid humidity value: {rel_hum}")
        self._connector.write_reg(0x15, rel_hum << 9, 2)

    def _get_status(self, raw: bool = True) -> [int, ens160_status]:
        """Возвращает текущее состояние ENS160 в виде байта
        Пожалуйста, прочтите Таблицу 26: Регистр DEVICE_STATUS из официальной документации!"""
        reg_val = self._read_register(0x20, 1)[0]
        if raw:
            return reg_val
        return Ens160._to_status(reg_val)

    def _get_aqi(self) -> int:
        """Возвращает расчетный индекс качества воздуха в соответствии с UBA. 1(прекрасно)..5(кошмар))
        Дополнительную информацию см. в разделе «AQI-UBA – Индекс качества воздуха UBA». Из официальной документации!"""
        reg_val = self._read_register(0x21, 1)
        return 0x07 & reg_val[0]

    def _get_tvoc(self) -> int:
        """Возвращает расчетную концентрацию Летучих Органических Соединений (ЛОС) в частях на миллион (ppm)
        Дополнительную информацию см. в разделе «TVOC – Общие летучие органические соединения». Из официальной документации!"""
        reg_val = self._read_register(0x22, 2)
        return self._connector.unpack("H", reg_val)[0]

    def _get_eco2(self) -> int:
        """Возвращает расчетную эквивалентную концентрацию CO2 в частях на миллион [ppm] на
        основе обнаруженных летучих органических соединений (ЛОС) и водорода.
        Дополнительную информацию см. в разделе «eCO2 – Эквивалент CO2». Из официальной документации!"""
        reg_val = self._read_register(0x24, 2)
        return self._connector.unpack("H", reg_val)[0]

    def _get_last_checksum(self) -> int:
        """Возвращает рассчитанную контрольную сумму предыдущей транзакции чтения n-байт.
        При необходимости её можно прочитать как отдельную транзакцию, чтобы проверить правильность предыдущей
        операции чтения. Значение следует сравнить с числом, рассчитанным хост-системой для входящих данных!"""
        # читаю 1 байт crc из датчика
        return self._connector.read_reg(0x38, 1)[0]

    def get_firmware_version(self) -> ens160_firmware_version:
        """Возвращает версию прошивки ENS160 в виде кортежа ens160_firmware_version"""
        b = self._exec_cmd(0x0E)
        return ens160_firmware_version(major=b[4], minor=b[5], release=b[6])

    # IBaseSensorEx
    def get_conversion_cycle_time(self) -> int:
        """Возвращает время в мс преобразования сигнала в цифровой код и готовности его для чтения по шине!
        Для текущих настроек датчика. При изменении настроек следует заново вызвать этот метод!"""
        return 1000

    def start_measurement(self, start: bool = True):
        """Настраивает параметры датчика и запускает процесс измерения.
        Если start в Истина, то датчик переводится в режим измерения, иначе датчик переводится в режим ожидания (IDLE)"""
        _mode = 2 if start else 1
        self._set_mode(_mode)

    def get_measurement_value(self, value_index: [int, None]) -> [int, ens160_air_params]:
        """Возвращает измеренное датчиком значение(значения) по его индексу/номеру.
        0 - eCO2;
        1 - TVOC;
        2 - AQI;
        None - кортеж ens160_air_params;"""
        if 0 == value_index:
            return self._get_eco2()
        if 1 == value_index:
            return self._get_tvoc()
        if 2 == value_index:
            return self._get_aqi()
        #
        if value_index is None:
            return ens160_air_params(eco2=self._get_eco2(), tvoc=self._get_tvoc(), aqi=self._get_aqi())

    def get_data_status(self, raw: bool = True) -> ens160_status:
        """Возвращает состояние готовности данных для считывания?
        Тип возвращаемого значения выбирайте сами!"""
        return self._get_status(raw=raw)

    def is_single_shot_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в режиме однократных измерений,
        каждое из которых запускается методом start_measurement"""
        return False

    def is_continuously_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в режиме многократных измерений,
        производимых автоматически. Процесс запускается методом start_measurement"""
        return 0x02 == self._get_mode()

    # Iterator
    def __next__(self) -> [None, ens160_air_params]:
        """Механизм итератора.
        ЛОС - Летучие Органические Соединения.
        Возвращает кортеж: CO2 [ppm], ЛОС[ppm], Индекс Качества Воздуха. 1(прекрасно)..5(кошмар)
        см. описание кортежа ens160_air_params выше."""
        if not self.is_continuously_mode():
            return None
        status = self.get_data_status(raw=False)
        if status.new_data: # новые данные готовы для чтения!
            return self.get_measurement_value(None)
