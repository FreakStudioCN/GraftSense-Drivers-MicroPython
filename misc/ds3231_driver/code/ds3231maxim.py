import micropython

from sensor_pack import bus_service, base_sensor
from sensor_pack.base_sensor import Device, Iterator

import sys


@micropython.native
def bcd_to_int(bcd) -> int:
    """convert bcd to int"""
    mask = 0x0F
    result = bcd & mask
    mask = mask << 4
    result += 10 * ((bcd & mask) >> 4)
    return result


def int_to_bcd(value: int) -> int:
    """convert int to bcd"""
    return int(str(value), 16)


class DS3221(Device, Iterator):
    """Class for work with DS3231 clock from Maxim Integrated или как эта фирма сейчас называется!?
    Please read DS3231 datasheet!"""
    #           alarm 1 register masks            alarm 2 register masks
    _mask_alarms = (0x0E, 0x0C, 0x08, 0x00, 0x10), (0x06, 0x04, 0x00, 0x08)

    @staticmethod
    def _get_alarm_mask(alarm_id: int):
        return DS3221._mask_alarms[alarm_id]

    @staticmethod
    def _convert_hours(hour_byte: int) -> int:
        # print(f"hour_byte: {hex(hour_byte)}")
        # In the 24-hour mode, bit 5 is the 20-hour bit (20–23 hours)
        hour = bcd_to_int(hour_byte & 0x3F)
        if hour_byte & 0x40:    # When high, 12-hour mode is selected
            hour = bcd_to_int(hour_byte & 0x1F)
            if hour_byte & 0x20:    # AM/PM bit with logic-high being PM
                hour = 12 + hour_byte
        return hour

    @staticmethod
    def _get_day_or_date(value: int) -> int:
        """return day of week or day of month by value"""
        if 0x40 & value:
            return bcd_to_int(0x0F & value)     # day of week
        else:
            return bcd_to_int(0x3F & value)     # day of month

    def __init__(self, adapter: bus_service.BusAdapter, address: int = 0x68):
        super().__init__(adapter, address, False)
        self._tbuf = bytearray(7)
        self._alarm_buf = bytearray(4)
        # off alarm interrupt
        self.control_alarm_interrupt()

    def _read_register(self, reg_addr, bytes_count=2) -> bytes:
        """считывает из регистра датчика значение.
        bytes_count - размер значения в байтах"""
        return self.adapter.read_register(self.address, reg_addr, bytes_count)

    def _write_register(self, reg_addr, value: int, bytes_count=2) -> int:
        """записывает данные value в датчик, по адресу reg_addr.
        bytes_count - кол-во записываемых данных"""
        byte_order = self._get_byteorder_as_str()[0]
        return self.adapter.write_register(self.address, reg_addr, value, bytes_count, byte_order)

    """№ bit                Description
    ----------------------------------------------------
        Bit 7:              Oscillator Stop Flag (OSF)
        Bit 3:              Enable 32kHz Output
        Bit 1:              Alarm 2 Flag (A2F)
        Bit 0:              Alarm 1 Flag (A1F)
    """
    def get_status(self) -> int:
        """Чтение 8 bit регистра состояния 0x0F"""
        return self._read_register(0x0F, 1)[0]

    """№ bit                Description
    ----------------------------------------------------
        Bit 7:              Enable Oscillator (EOSC)
        Bit 6:              Battery-Backed Square-Wave Enable (BBSQW)
        Bit 5:              Convert Temperature (CONV)
        Bits 4 and 3:       Rate Select (RS2 and RS1)
        Bit 2:              Interrupt Control (INTCN)
        Bit 1:              Alarm 2 Interrupt Enable (A2IE)
        Bit 0:              Alarm 1 Interrupt Enable (A1IE)
    """
    def set_status(self, new_value: int) -> int:
        """Only three bits are available for writing in the status register. EN32kHz, A2F, A1F"""
        return self._write_register(0x0F, new_value, 1)
    
    def get_alarm_flags(self, clear: bool = True) -> tuple:
        """Return two clock alarms flag (alarm_id_1, alarm_id_0) and clear it, if clear is true!"""
        s = self.get_status()
        a2, a1 = bool(s & 0x02), bool(s & 0x01)
        if clear:
            s &= 0xFC
        self.set_status(s)
        return a2, a1

    def get_control(self) -> int:
        """Возвращает байт регистра управления.
        Returns the control register byte."""
        return self._read_register(0x0E, 1)[0]

    def set_control(self, value: int) -> int:
        """Записывает байт value в регистр управления.
        Читайте документацию на микросхему (Control Register (0Eh))!
        Writes the value byte to the control register.
        Read the documentation for the chip (Control Register (0Eh))!"""
        return self._write_register(0x0E, value, 1)

    def get_temperature(self) -> float:
        """возвращает температуру микросхемы часов в градусах Цельсия"""
        hi, low = self._read_register(0x11, 2)
        return self.unpack("b", hi.to_bytes(1, sys.byteorder))[0] + 0.25 * (low >> 6)

    def get_aging_offset(self) -> int:
        return self._read_register(0x10, 1)[0]
    
    def get_time(self) -> tuple:
        """возвращает время, как в виде кортежа (как localtime())
        (year, month, mday, hour, minute, second, weekday, yearday)"""
        buf, mask = self._tbuf, 0x1f
        self.adapter.read_buf_from_mem(self.address, 0, buf)
        for i, val in enumerate(buf):
            if i in (0, 1, 4, 6):
                buf[i] = bcd_to_int(val)
            if 2 == i:  # hours
                buf[i] = DS3221._convert_hours(val)
            if 5 == i:  # month
                buf[i] = bcd_to_int(val & mask)
        # -----       YY       MM      DD      HH      MM      SS    WDAY    no year day
        # WDAY in range [0, 6], Monday is 0
        return 2_000+buf[6], buf[5], buf[4], buf[2], buf[1], buf[0], buf[3]-1, -1,  
    
    def set_time(self, local_time):
        """      YYYY, MM, DD, HH, MM, SS, day of week, year day
                 ГГГГ, ММ, ДД, ЧЧ, ММ, СС, день недели, день года
        index:    0     1   2   3   4   5       6
        это формат времени, возвращаемого функцией localtime().
        this is the time format returned by the localtime() function"""
        k = 5, 4, 3, 6, 2, 1, 0
        v = 3, 5, 6
        value = 0
        for ind in range(7):
            if ind not in v:
                value = int_to_bcd(local_time[k[ind]])
            else:
                if 3 == ind:   # WDAY start value in chip start from 1!
                    value = int_to_bcd(local_time[k[ind]] + 1)
                if 5 == ind:   # MONTH
                    value = 0x80 + int_to_bcd(local_time[k[ind]])
                if 6 == ind:   # YEAR
                    value = int_to_bcd(local_time[k[ind]] - 2_000)
        
            self.adapter.write_buf_to_mem(self.address, ind, value.to_bytes(1, sys.byteorder))

    def get_alarm(self, alarm_id: int = 0) -> tuple:
        """return alarm time as tuple: (seconds, minutes, hour, day, match_value)
        alarm_id must be 0 or 1!
        match_value description pls see in set_alarm method below!"""
        base_sensor.check_value(alarm_id, (0, 1), f"Invalid alarm_id parameter: {alarm_id}")

        mask7 = 0x80
        mask6 = 0x40
        mask7f = 0x7F

        a_buf = self._alarm_buf
        alarm_addr, seconds = 7, 0
        if alarm_id > 0:
            alarm_addr += 4

        self.adapter.read_buf_from_mem(self.address, alarm_addr, a_buf)
        if 0 == alarm_id:
            # sec   min     hour    day
            t = bcd_to_int(mask7f & a_buf[0]), \
                bcd_to_int(mask7f & a_buf[1]), \
                DS3221._convert_hours(a_buf[2]), \
                self._get_day_or_date(a_buf[3])
        else:   # min     hour    day
            t = bcd_to_int(mask7f & a_buf[0]), \
                DS3221._convert_hours(a_buf[1]), \
                self._get_day_or_date(a_buf[2])

        # alarm bitmask
        alarm_byte = 0
        _max = 4
        if alarm_id > 0:
            _max -= 1
        for i in range(_max):   # AxM1, AxM2, AxM3, AxM4 bits
            if mask7 & a_buf[i]:
                alarm_byte |= 1 << i
        
        if mask6 & a_buf[_max - 1]:    # DY_DT bit
            alarm_byte |= mask6

        tt = self._get_alarm_mask(alarm_id)
        # print(tt, hex(alarm_byte))
        if alarm_byte in tt:
            alarm_byte = tt.index(alarm_byte)     # match mode
        else:
            alarm_byte = None        # no match mode
        
        return t, alarm_byte

    #   alarm_time - tuple (second, minute, hour, day)
    #   match_value - int
    #        alarm_id == 0
    #           0:  Alarm when seconds match
    #           1:  Alarm when minutes and seconds match    (first is True)
    #           2:  Alarm when hours, minutes, and seconds match    (first is True)
    #           3:  Alarm when date_of_month, hours, minutes, and seconds match (first is True)
    #           4:  Alarm when day_of week, hours, minutes, and seconds match (first is True)
    #
    #        alarm_id == 1
    #           0:  Alarm when minutes match
    #           1:  Alarm when hours and minutes match
    #           2:  Alarm when date_of_month, hours, and minutes match
    #           3:  Alarm when day_of week, hours, and minutes match

    def set_alarm(self, alarm_time: tuple, match_value: int = 2, alarm_id: int = 0):
        """Set alarm time. Alarm_id must be 0 or 1!"""
        base_sensor.check_value(alarm_id, (0, 1), f"Invalid alarm_id parameter: {alarm_id}")
        base_sensor.check_value(match_value,
                                range(5 if 0 == alarm_id else 4),
                                f"Invalid match_value parameter: {match_value}")
        a_buf = self._alarm_buf
        alarm_addr = 7
        if alarm_id > 0:
            alarm_addr += 4

        cnt, offs = 4, 0
        if alarm_id > 0:
            cnt, offs = 3, 1

        am = self._get_alarm_mask(alarm_id)[match_value]
        mask = 0
        for i in range(cnt):
            if am & (1 << i):
                mask = 0x80
            if i == cnt - 1:
                # последний бит DY/DT
                mask |= am & (1 << cnt)

            a_buf[i] = mask | int_to_bcd(alarm_time[i + offs])

        byte_order = self._get_byteorder_as_str()[0]
        self.adapter.write_register(self.address,
                                    alarm_addr,
                                    a_buf,
                                    cnt,
                                    byte_order
                                    )

    def control_alarm_interrupt(self, irq_alarm_1_enable: bool = False, irq_alarm_0_enable: bool = False):
        """Включает или отключает прерывание от будильников (два) на выводе микросхемы INT/SQW.
        Если вы не используете прерывание, вы должны вызвать метод get_alarm_flags в цикле для обнаружения
        срабатывания будильника!
        Enable or disable two clock alarms interrupt on chip pin INT/SQW.
        If you dont use interrupt, you must call get_alarm_flags method in cycle for detect clock alarm!"""
        cr = self.get_control()
        cr &= 0xB8  # BBSQW = INTCN = A2IE = A1IE = 0
        if irq_alarm_1_enable:
            cr |= 0x06  # INTCN = A2IE = 1
        if irq_alarm_0_enable:
            cr |= 0x05  # INTCN = A1IE = 1
        self.set_control(cr)

    def __next__(self) -> tuple:
        """For support iterating."""
        return self.get_time()
