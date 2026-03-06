# micropython
# mail: goctaprog@gmail.com
# MIT license
# import struct

from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, Iterator, check_value, get_error_str   # all_none
from sensor_pack_2.adcmod import ADC, adc_init_props    # , raw_value_ex
# import micropython
# from micropython import const
from collections import namedtuple
from sensor_pack_2.bitfield import bit_field_info
from sensor_pack_2.bitfield import BitFields

_model_3421 = 'mcp3421'
_model_3422 = 'mcp3422'
_model_3424 = 'mcp3424'


def get_init_props(model: str) -> adc_init_props:
    """Возвращает параметры для инициализации АЦП в виде именованного кортежа по имени модели АЦП."""
    if _model_3421 == model.lower():
        return adc_init_props(reference_voltage=2.048, max_resolution=18, channels=0,
                              differential_channels=1, differential_mode=True)
    if _model_3422 == model.lower():
        return adc_init_props(reference_voltage=2.048, max_resolution=18, channels=0,
                              differential_channels=2, differential_mode=True)
    if _model_3424 == model.lower():
        return adc_init_props(reference_voltage=2.048, max_resolution=18, channels=0,
                              differential_channels=4, differential_mode=True)
    raise ValueError(f"Неизвестная модель АЦП!")


class Mcp342X(DeviceEx, ADC, Iterator):
    """18-битный аналого-цифровой преобразователь с интерфейсом I2C и встроенным ИОН.
    18-Bit Analog-to-Digital Converter with I2C Interface and On-Board Reference"""

    _config_reg_mcp3421 = (bit_field_info(name='RDY', position=range(7, 8), valid_values=None, description=None),           # Этот бит является флагом готовности данных. В режиме чтения этот бит указывает, был ли выходной регистр обновлен новым преобразованием. В режиме однократного преобразования запись этого бита в «1» инициирует новое преобразование.
                           bit_field_info(name='CH', position=range(5, 7), valid_values=None, description=None),            # (channel) Это биты выбора канала, но они не используются в MCP3421.
                           bit_field_info(name='CCM', position=range(4, 5), valid_values=range(6) , description=None),      # (continue conversion mode) Бит режима преобразования. 1 - режим непрерывного преобразования. 0 - режим однократного преобразования.
                           bit_field_info(name='SampleRate', position=range(2, 4), valid_values=None, description=None),    # Бит выбора частоты дискретизации. 0 - 240 SPS (12 bit); 1 - 60 SPS (14 bit); 2 - 15 SPS (16 bit); 3 - 3.75 SPS (18 bit)
                           bit_field_info(name='PGA', position=range(2), valid_values=None, description=None),              # Биты выбора усиления PGA. 0 - 1; 1 - 1/2; 2 - 1/4; 3 - 1/8
                           )
    # ответ от АЦП
    _mcp3421_raw_data = namedtuple("_mcp3421_raw_data", "b0 b1 b2 config")

    def get_resolution(self, raw_data_rate: int) -> int:
        """Преобразует сырое значение частоты обновления данных в кол-во бит в отсчете АЦП.
        У многих АЦП кол-во бит в отсчете зависит(!) от частоты преобразования."""
        return 12 + 2 * raw_data_rate

    def __init__(self, adapter: bus_service.BusAdapter, model: str = 'mcp3421', address=0x68):
        # MCP3421 имеет фиксированный адрес 0x68, но АЦП MCP342Х имеют адреса в диапазоне 0x68..0x6F
        check_value(address, range(0x68, 0x70), f"Неверное значение адреса I2C устройства: 0x{address:x}")
        DeviceEx.__init__(self, adapter, address, True)
        ADC.__init__(self, get_init_props(model), model=model)
        # print("DBG:__init__")
        # для удобства работы с настройками АЦП
        self._bit_fields = BitFields(fields_info=Mcp342X._config_reg_mcp3421)
        # буфер на 4 байта
        self._buf_4 = bytearray((0 for _ in range(4)))
        # последнее считанное из АЦП значение
        self._last_raw_value = None
        self._differential_mode = True      # дифференциальный АЦП. для get_lsb
        # Этот бит является флагом готовности данных. В режиме чтения этот бит указывает, был ли выходной регистр
        # обновлен новым преобразованием (0).
        # В режиме однократного преобразования запись этого бита в «1» инициирует новое преобразование.
        self._data_ready = None
        # Внимание, важный вызов(!)
        # читаю config АЦП и обновляю поля класса
        _raw_cfg = self.get_raw_config()
        self.raw_config_to_adc_properties(_raw_cfg)

#    def _read_raw_data(self) -> _mcp3421_raw_data:
#        """Считывает из АЦП информацию о результате преобразования и текущие 'сырые' настройки"""
#        buf = self._buf_4
#        self.read_to_buf(buf)
#        b0, b1, b2, cfg = self.unpack(fmt_char=len(buf)*"B", source=buf)
#        return Mcp3421._mcp3421_raw_data(b0=b0, b1=b1, b2=b2, config=cfg)

    def get_raw_config(self) -> int:
        """Возвращает(считывает) текущие настройки датчика из регистров(конфигурации) в виде числа."""
        # raw = self._read_raw_data()
        buf = self._buf_4
        self.read_to_buf(buf)
        # последний байт в ответе АЦП это конфигурация(!)
        return buf[-1]

    def set_raw_config(self, value: int):
        """Записывает настройки(value) во внутреннюю память/регистр датчика."""
        self.write(value.to_bytes(1, 'big'))

    def raw_config_to_adc_properties(self, raw_config: int):
        """Возвращает текущие настройки датчика из числа, возвращенного get_raw_config(!), в поля(!) класса.
        raw_config -> adc_properties"""
        # вызывать только после вызова get_raw_config!!!
        bf = self._bit_fields
        bf.source = raw_config
        # 0 - в бите DRY, означает, что данные были обновлены АЦП
        self._data_ready = not bf['RDY']
        self._curr_channel = bf['CH']
        self._single_shot_mode = not bf['CCM']
        self._curr_raw_gain = bf['PGA']
        self._curr_raw_data_rate = bf['SampleRate']


    def get_raw_value(self) -> int:
        """Возвращает 'сырое' значение отсчета АЦП. Переопределяется в классах - наследниках!"""
        # вызывать только после вызова get_raw_config и raw_config_to_adc_properties!!!
        # print("DBG:get_raw_value")
        cfg = self.get_raw_config()
        # print(f"DBG:get_raw_value. config: 0x{cfg:x}")
        self.raw_config_to_adc_properties(raw_config=cfg)
        if self.data_ready:
            if self._curr_raw_data_rate < 3:
                # два байта на отсчет, 12, 14, 16 бит
                return self.unpack(fmt_char='h', source=self._buf_4)[0]
            b0, b1, b2 = self.unpack(fmt_char='bBB', source=self._buf_4)    # 18 бит на отсчет
            return 65536*b0 + 256*b1 + b2
        # print(f"DBG:get_raw_value. data not ready! config: 0x{cfg:x}")

    def raw_sample_rate_to_real(self, raw_sample_rate: int) -> float:
        """Преобразует сырое значение частоты преобразования в частоту [Гц]."""
        sps = 240, 60, 15, 3.75
        return sps[raw_sample_rate]

    def gain_raw_to_real(self, raw_gain: int) -> float:
        """Преобразует 'сырое' значение усиления в 'настоящее'"""
        return 2 ** raw_gain

    def get_conversion_cycle_time(self) -> int:
        """возвращает время преобразования в [мкс] аналогового значения в цифровое в зависимости от
        текущих настроек АЦП. Переопредели для каждого АЦП!"""
        # вызывать только после вызова get_raw_config и raw_config_to_adc_properties!!!
        return 1 + int(1_000_000 / self.sample_rate)

    def check_gain_raw(self, gain_raw: int) -> int:
        """Проверяет сырое усиление на правильность. В случае ошибки выброси исключение!
        Возвращает значение gain_raw в случае успеха! Для переопределения в классе-наследнике."""
        r4 = range(4)
        return check_value(gain_raw, r4, get_error_str("gain_raw", gain_raw, r4))

    def check_data_rate_raw(self, data_rate_raw: int) -> int:
        """Проверяет сырое data_rate на правильность. В случае ошибки выброси исключение!
        Возвращает data_rate_raw в случае успеха! Для переопределения в классе-наследнике."""
        r4 = range(4)
        return check_value(data_rate_raw, r4, get_error_str("data_rate_raw", data_rate_raw, r4))

    def adc_properties_to_raw_config(self) -> int:
        """Преобразует свойства АЦП из полей класса в 'сырую' конфигурацию АЦП.
        adc_properties -> raw_config"""
        # print("DBG:adc_properties_to_raw_config")
        _cfg = self.get_raw_config()
        bf = self._bit_fields
        bf.source = _cfg
        # *
        bf['CH'] = not self._curr_channel
        bf['CCM'] = not self.single_shot_mode
        bf['RDY'] = self.single_shot_mode
        bf['SampleRate'] = self.current_sample_rate
        bf['PGA'] = self.current_raw_gain
        # print(f"DBG:adc_properties_to_raw_config: 0x{bf.source:x}")

        return bf.source

    @property
    def data_ready(self) -> bool:
        if self.single_shot_mode:
            return self._data_ready
        else:   # автоматический режим измерений
            if 3 == self.current_sample_rate:
                return self._data_ready
        # В автоматическом режиме измерений, при data_rate меньше трех, не выставлялся бит готовности данных.
        # Причину не нашел! Пришлось делать это!
        # Вот что сказано в документации:
        # The MCP3421 device performs a Continuous Conversion if the O/C bit is set to logic “high”. Once the
        # conversion is completed, the result is placed at the output data register. The device immediately begins
        # another conversion and overwrites the output data register with the most recent data.
        #
        # The device also clears the data ready flag (RDY bit = 0) when the conversion is completed. The device sets the
        # ready flag bit (RDY bit = 1), if the latest conversion result has been read by the Master.
        return True

    # Iterator
    def __iter__(self):
        return self

    def __next__(self) -> [int, None]:
        if not self.single_shot_mode:
            # режим непрерывного преобразования!
            return self.value
        return None
