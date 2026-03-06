# micropython
# mail: goctaprog@gmail.com
# MIT license
import micropython
import array

from collections import namedtuple
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import IBaseSensorEx, Iterator, IDentifier, DeviceEx, check_value

# ВНИМАНИЕ: не подключайте питание датчика к 5В, иначе датчик выйдет из строя! Только 3.3В!!!
# WARNING: do not connect "+" to 5V or the sensor will be damaged!

@micropython.native
def _calibration_regs_addr() -> iter:
    """возвращает кортеж из адреса регистра, размера значения в байтах, типа значения (u-unsigned, s-signed)"""
    start_addr = 0x31
    tpl = ('1b', '2h', '2H')
    # возвращает итератор с адресами внутренних регистров датчика, хранящих калибровочные коэффициенты
    val_type = "22011002200100"
    for item in val_type:
        v_size, v_type = tpl[int(item)]
        yield int(start_addr), int(v_size), v_type
        start_addr += int(v_size)

serial_number_bmp390 = namedtuple("sn_bmp390", "chip_id rev_id")
measured_values_bmp390 = namedtuple("meas_vals_bmp390", "T P")
data_status_bmp390 = namedtuple("data_status_bmp390", "temp_ready press_ready cmd_decoder_ready")
int_status_bmp390 = namedtuple("int_status_bmp390", "data_ready fifo_is_full fifo_watermark")
event_bmp390 = namedtuple("event__bmp390", "itf_act_pt por_detected")


class Bmp390(IBaseSensorEx, IDentifier, Iterator):
    """Class for work with Bosh BMP180 pressure sensor"""

    def __init__(self, adapter: bus_service.BusAdapter, address=0x77,
                 oversample_temp=0b11, oversample_press=0b11, iir_filter=0):
        """i2c - объект класса I2C; baseline_pressure - давление на уровне моря в Pa в твоей(!) местности;;
        oversample_settings (0..5) - точность измерения 0-грубо но быстро, 5-медленно, но точно;
        address - адрес датчика;
        iir_filter=0..7; 0 - off, 7 - max value

        i2c is an object of the I2C class; baseline_pressure - sea level pressure in Pa in your(!) area;
        oversample_settings (0..5) - measurement reliability 0-coarse but fast, 5-slow but accurate;"""
        # super().__init__(adapter, address, False)
        self._connection = DeviceEx(adapter=adapter, address=address, big_byte_order=False)
        self._buf_2 = bytearray(2)  # для _read_buf_from_mem
        self._buf_3 = bytearray(3)  # для _read_buf_from_mem
        self._t_lin = None  # for pressure calculation
        # for temperature only!
        self._oss_t = check_value(oversample_temp, range(6),
                                   f"Invalid temperature oversample value: {oversample_temp}")
        self._oss_p = check_value(oversample_press, range(6),
                                   f"Invalid pressure oversample value: {oversample_press}")
        self._adapter = adapter
        self._IIR = check_value(iir_filter, range(8),
                                 f"Invalid iir_filter value: {iir_filter}")
        self._mode = 0  # sleep mode
        self._enable_pressure = False
        self._enable_temperature = False
        self._sampling_period = 0x02  # 1.28 sec
        # массив, хранящий калибровочные коэффициенты (14 штук)
        self._cfa = array.array("l", [0 for _ in range(14)])  # signed long elements
        # считываю калибровочные коэффициенты
        self._read_calibration_data()
        # предварительный расчет
        self._precalculate()

    def __del__(self):
        del self._cfa
        del self._buf_3
        del self._buf_2

    def get_calibration_coefficient(self, index: int) -> int:
        """возвращает калибровочный коэффициент по его индексу (0..13).
        returns the calibration coefficient by its index (0..13)"""
        check_value(index, range(14), f"Invalid index value: {index}")
        return self._cfa[index]

    @micropython.native
    def _precalculate(self):
        """предварительно вычисленные значения"""
        get_calibr_coeff = self.get_calibration_coefficient
        # для расчета температуры
        self.par_t1 = get_calibr_coeff(0) * 2 ** 8  #
        self.par_t2 = get_calibr_coeff(1) / 2 ** 30  #
        self.par_t3 = get_calibr_coeff(2) / 2 ** 48  #
        # для расчета давления
        self.par_p1 = (get_calibr_coeff(3) - 2 ** 14) / 2 ** 20
        self.par_p2 = (get_calibr_coeff(4) - 2 ** 14) / 2 ** 29
        self.par_p3 = get_calibr_coeff(5) / 2 ** 32
        self.par_p4 = get_calibr_coeff(6) / 2 ** 37
        self.par_p5 = 8 * get_calibr_coeff(7)
        self.par_p6 = get_calibr_coeff(8) / 2 ** 6
        self.par_p7 = get_calibr_coeff(9) / 2 ** 8
        self.par_p8 = get_calibr_coeff(10) / 2 ** 15
        self.par_p9 = get_calibr_coeff(11) / 2 ** 48
        self.par_p10 = get_calibr_coeff(12) / 2 ** 48
        self.par_p11 = get_calibr_coeff(13) / 2 ** 65

    def _read_calibration_data(self) -> int:
        """Читает калибровочные значение из датчика.
        read calibration values from sensor.
        return count read values"""
        if any(self._cfa):
            raise ValueError(f"calibration data array already filled!")
        _conn = self._connection
        index = 0
        for v_addr, v_size, v_type in _calibration_regs_addr():
            # print(v_addr, v_size, v_type)
            reg_val = _conn.read_reg(reg_addr=v_addr, bytes_count=v_size)
            rv = _conn.unpack(fmt_char=f"{v_type}", source=reg_val)[0]
            # check
            if rv == 0x00 or rv == 0xFFFF:
                raise ValueError(f"Invalid register addr: {v_addr} value: {hex(rv)}")
            self._cfa[index] = rv
            index += 1
        return len(self._cfa)

    # IDentifier
    def get_id(self) -> serial_number_bmp390:
        """Возвращает идентификатор датчика и его revision ID.
        Returns the ID and revision ID of the sensor."""
        buf = self._buf_2
        # self._read_buf_from_mem(0x00, buf)
        self._connection.read_buf_from_mem(address=0x00, buf=buf, address_size=1)
        # chip id, rev_id
        return serial_number_bmp390(chip_id=buf[0], rev_id=buf[1])

    def soft_reset(self, reset_or_flush: bool = True):
        """программный сброс датчика.
        software reset of the sensor"""
        value = 0xB6 if reset_or_flush else 0xB0
        self._connection.write_reg(reg_addr=0x7E, value=value, bytes_count=1)

    def get_error(self) -> int:
        """Возвращает три бита состояния ошибок.
        Bit 0 - fatal_err Fatal error
        Bit 1 - Command execution failed. Cleared on read.
        Bit 2 conf_err sensor configuration error detected (only working in normal mode). Cleared on read.
        """
        err = self._connection.read_reg(reg_addr=0x02, bytes_count=1)[0]
        return err & 0x07

    def get_data_status(self) -> data_status_bmp390:
        """Возвращает три бита состояния датчика как кортеж
        Data ready for temperature, Data ready for pressure, CMD decoder status
        бит 0 - CMD decoder status (0: Command in progress; 1: Command decoder is ready to accept a new command)
        бит 1 - Data ready for pressure. (It gets reset, when one pressure DATA register is read out)
        бит 2 - Data ready for temperature sensor. (It gets reset, when one temperature DATA register is read out)
        """
        val = self._connection.read_reg(0x03, 1)[0]
        i = 0x07 & (val >> 4)
        drdy_temp, drdy_press, cmd_rdy = 0x04 & i, 0x02 & i, 0x01 & i
        return data_status_bmp390(temp_ready=drdy_temp, press_ready=drdy_press, cmd_decoder_ready=cmd_rdy)

    @micropython.native
    def _get_pressure_raw(self) -> int:
        # трех байтовое значение
        buf = self._buf_3
        l, m, h = self._connection.read_buf_from_mem(address=0x04, buf=buf, address_size=1)
        return (h << 16) | (m << 8) | l

    def get_pressure(self) -> float:
        """Return pressure in Pascal [Pa].
        Call get_temperature() before call get_pressure() !!!"""
        uncompensated = self._get_pressure_raw()
        #
        t_lin = self._t_lin
        t_lin2 = t_lin * t_lin
        t_lin3 = t_lin * t_lin * t_lin
        #
        partial_data1 = self.par_p6 * t_lin
        partial_data2 = self.par_p7 * t_lin2
        partial_data3 = self.par_p8 * t_lin3
        partial_out1 = self.par_p5 + partial_data1 + partial_data2 + partial_data3
        #
        partial_data1 = self.par_p2 * t_lin
        partial_data2 = self.par_p3 * t_lin2
        partial_data3 = self.par_p4 * t_lin3
        partial_out2 = uncompensated * (self.par_p1 + partial_data1 + partial_data2 + partial_data3)
        #
        partial_data1 = uncompensated * uncompensated
        partial_data2 = self.par_p9 + self.par_p10 * t_lin
        partial_data3 = partial_data1 * partial_data2
        partial_data4 = partial_data3 + (uncompensated * uncompensated * uncompensated) * self.par_p11
        #
        return partial_out1 + partial_out2 + partial_data4

    @micropython.native
    def _get_temperature_raw(self) -> int:
        # трех байтовое значение
        buf = self._buf_3
        l, m, h = self._connection.read_buf_from_mem(address=0x07, buf=buf, address_size=1)
        return (h << 16) | (m << 8) | l

    def get_temperature(self) -> float:
        """Return temperature in Celsius"""
        uncompensated = self._get_temperature_raw()
        partial_data1 = uncompensated - self.par_t1
        partial_data2 = partial_data1 * self.par_t2
        # Update the compensated temperature since this is needed for pressure calculation !!!
        self._t_lin = partial_data2 + (partial_data1 * partial_data1) * self.par_t3
        return self._t_lin

    @micropython.native
    def get_sensor_time(self) -> int:
        # трех байтовое значение
        buf = self._buf_3
        l, m, h = self._connection.read_buf_from_mem(address=0x0C, buf=buf, address_size=1)
        return (h << 16) | (m << 8) | l

    def get_event(self) -> event_bmp390:
        """Bit 0 por_detected ‘1’ after device power up or softreset. Clear-on-read
        Bit 1 itf_act_pt ‘1’ when a serial interface transaction occurs during a
        pressure or temperature conversion. Clear-on-read"""
        _evt = 0b11 & self._connection.read_reg(reg_addr=0x10, bytes_count=1)[0]
        return event_bmp390(itf_act_pt=bool(0b10 & _evt), por_detected=bool(0b01 & _evt))

    def get_int_status(self) -> int_status_bmp390:
        """Bit 0 fwm_int FIFO Watermark Interrupt
        Bit 1 full_int FIFO Full Interrupt
        Bit 3 drdy data ready interrupt"""
        int_stat = 0b1011 & self._connection.read_reg(reg_addr=0x11, bytes_count=1)[0]
        return int_status_bmp390(data_ready=bool(0b1000 & int_stat),
                                 fifo_is_full=bool(0b010 & int_stat),
                                 fifo_watermark=bool(0b0001 & int_stat))

    def get_fifo_length(self) -> int:
        """The FIFO byte counter indicates the current fill level of the FIFO buffer."""
        buf = self._buf_2
        self._connection.read_buf_from_mem(address=0x12, buf=buf, address_size=1)
        return self._connection.unpack(fmt_char="H", source=buf)[0]

    def start_measurement(self, enable_press: bool = True, enable_temp: bool = True, mode: int = 2):
        """ # mode: 0 - sleep, 1-forced, 2-normal (continuously)"""
        if not mode in range(3):
            raise ValueError(f"Invalid mode value: {mode}")
        tmp = 0
        if enable_press:
            tmp |= 0b01
        else:
            tmp &= ~0b01

        if enable_temp:
            tmp |= 0b10
        else:
            tmp &= ~0b10

        # обнуляю биты 4 и 5
        tmp &= ~0b0011_0000
        if 0 == mode:
            pass  # sleep mode
        if 1 == mode:
            tmp |= 0b0001_0000  # forced mode (режим однократных измерений)
        if 2 == mode:
            tmp |= 0b0011_0000  # continuous mode (режим непрерывных периодических измерений)
        # save
        self._connection.write_reg(reg_addr=0x1B, value=tmp, bytes_count=1)
        self._mode = mode
        self._enable_pressure = enable_press
        self._enable_temperature = enable_temp

    def get_power_mode(self) -> int:
        """Возвращает текущий режим работы датчика:
        0 - сон
        1 или 2 - однократное измерение
        3 - периодические измерения"""
        tmp = self._connection.read_reg(reg_addr=0x1B, bytes_count=1)[0]
        return (0b11_0000 & tmp) >> 4

    def is_single_shot_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в режиме однократных измерений,
        каждое из которых запускается методом start_measurement"""
        _pm = self.get_power_mode()
        return 2 == _pm or 1 == _pm

    def is_continuously_mode(self) -> bool:
        """Возвращает Истина, когда датчик находится в режиме многократных измерений,
        производимых автоматически. Процесс запускается методом start_measurement"""
        return 3 == self.get_power_mode()

    def set_oversampling(self, pressure_oversampling: int, temperature_oversampling: int):
        tmp = 0
        po = check_value(pressure_oversampling, range(6),
                          f"Invalid value pressure_oversampling: {pressure_oversampling}")
        to = check_value(temperature_oversampling, range(6),
                          f"Invalid value temperature_oversampling: {temperature_oversampling}")
        tmp |= po
        tmp |= to << 3
        self._connection.write_reg(reg_addr=0x1C, value=tmp, bytes_count=1)
        self._oss_t = temperature_oversampling
        self._oss_p = pressure_oversampling

    def set_sampling_period(self, period: int):
        p = check_value(period, range(18),
                         f"Invalid value output data rates: {period}")
        self._connection.write_reg(reg_addr=0x1D, value=p, bytes_count=1)
        self._sampling_period = period

    def set_iir_filter(self, value):
        """Коэффициент IIR-фильтра"""
        p = check_value(value, range(8),
                         f"Invalid value iir_filter: {value}")
        self._connection.write_reg(reg_addr=0x1F, value=p, bytes_count=1)
        self._IIR = value

    @micropython.native
    def get_conversion_cycle_time(self) -> int:
        """возвращает время преобразования в [мкс] датчиком температуры или давления в зависимости от его настроек"""
        k = 2020
        temp_us = 163 + k * 2 ** self._oss_t
        total = 234 + temp_us
        if self._enable_pressure:
            press_us = 392 + k * 2 ** self._oss_p
            total += press_us
        return total

    # Iterator
    def __next__(self) -> None | float | measured_values_bmp390:
        if not self.is_continuously_mode():
            return
        temperature = self.get_temperature()
        if self._enable_temperature and not self._enable_pressure:
            return measured_values_bmp390(T=temperature, P=None)
        if self._enable_pressure and not self._enable_temperature:
            return measured_values_bmp390(T=None, P=self.get_pressure())
        return measured_values_bmp390(T=temperature, P=self.get_pressure())
