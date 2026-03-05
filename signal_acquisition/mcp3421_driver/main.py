import sys
from machine import I2C, Pin
from sensor_pack_2.bus_service import I2cAdapter
import mcp3421mod
import time


if __name__ == '__main__':
    i2c = I2C(id=1, scl=Pin(7), sda=Pin(6), freq=400_000)  # on Raspberry Pi Pico
    adapter = I2cAdapter(i2c)

    adc = mcp3421mod.Mcp342X(adapter)

    print("---Одиночный режим измерения---")
    my_gain = 0
    my_data_rate = 2
    adc.start_measurement(single_shot=True, data_rate_raw=my_data_rate, gain_raw=my_gain,
                          channel=0, differential_channel=True)
    print("---Основные 'сырые' настройки датчика---")
    gp = adc.get_general_raw_props()
    print(gp)
    print(16 * "--")
    td = adc.get_conversion_cycle_time()
    print(f"Время преобразования [мкс]: {td}")
    print(f"Бит в отсчете: {adc.current_resolution}")
    print(f"PGA: {adc.gain}")
    print(16 * "--")
    for _ in range(33):
        time.sleep_us(td)
        # print(f"value: {adc.value}; raw: {adc.get_value(raw=True)}")
        val = adc.get_value(raw=False)
        # lsb = adc.get_lsb()
        # print(f"value: {val};\tLSB [Вольт]: {lsb}")
        # val = adc.get_raw_value_ex()
        print(f"Напряжение: {val} Вольт")
        adc.start_measurement(single_shot=True, data_rate_raw=my_data_rate, gain_raw=my_gain,
                              channel=0, differential_channel=True)

    print(16 * "--")
    print("Автоматический режим измерений АЦП")
    print(16 * "--")
    adc.start_measurement(single_shot=False, data_rate_raw=my_data_rate, gain_raw=my_gain,
                          channel=0, differential_channel=True)
    td = adc.get_conversion_cycle_time()
    time.sleep_us(td)
    print(f"Время преобразования [мкс]: {td}")
    print(f"Бит в отсчете: {adc.current_resolution}")
    _cnt, _max = 0, 333333
    for voltage in adc:
        print(f"Напряжение: {voltage} Вольт")
        if _cnt > _max:
            sys.exit(0)
        time.sleep_us(td)
        _cnt += 1
