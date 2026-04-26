import time
# import sys
from machine import I2C
from sensor_pack_2.bus_service import I2cAdapter
import ina_ti

def show_header(info: str, width: int = 32):
    print(width * "-")
    print(info)
    print(width * "-")

if __name__ == '__main__':
    # пожалуйста установите выводы scl и sda в конструкторе для вашей платы, иначе ничего не заработает!
    # please set scl and sda pins for your board, otherwise nothing will work!
    # https://docs.micropython.org/en/latest/library/machine.I2C.html#machine-i2c
    # i2c = I2C(0, scl=Pin(13), sda=Pin(12), freq=400_000) # для примера
    # bus =  I2C(scl=Pin(4), sda=Pin(5), freq=100000)   # на esp8266    !
    # Внимание!!!
    # Замените id=1 на id=0, если пользуетесь первым портом I2C !!!
    # Warning!!!
    # Replace id=1 with id=0 if you are using the first I2C port !!!
    cycles_count = 10
    i2c = I2C(id=1, freq=400_000)  # on Arduino Nano RP2040 Connect tested
    adaptor = I2cAdapter(i2c)

    show_header("INA219Simple. Настроек нет. Автоматический режим измерений. Напряжение на шине до 26 В, напряжение на шунте до 0.32 В.")
    ina219 = ina_ti.INA219Simple(adaptor)
    # print(f"\tshunt voltage: {ina219.get_shunt_voltage()}")
    # print(f"\tbus voltage: {ina219.get_voltage()}")
    wait_time_us = ina219.get_conversion_cycle_time()
    print(f"wait_time_us: {wait_time_us} мкс.")
    for _ in range(cycles_count):
        shunt_v, t = ina219.get_shunt_voltage(), ina219.get_voltage()
        print(f"Shunt: {shunt_v} V;\tBus: {t}")
        time.sleep_us(wait_time_us)
        # дополнительная задержка, чтобы не зависала IDE
        time.sleep_ms(100)
    del ina219

    # класс с настройками
    ina219 = ina_ti.INA219(adapter=adaptor, address=0x40, shunt_resistance=0.1)
    ina219.bus_voltage_range = False    # 16 V
    ina219.shunt_voltage_enabled = True
    ina219.bus_adc_resolution = 0x03
    ina219.shunt_adc_resolution = 0x03
    ina219.max_expected_current = 1.0 # Ампер

    show_header("INA219. Настройки! Ручной режим измерений")
    ina219.start_measurement(continuous=False, enable_calibration=True)
    print(f"configuration: {ina219.get_config()}")
    wait_time_us = ina219.get_conversion_cycle_time()
    print(f"wait_time_us: {wait_time_us} мкс.")
    for _ in range(cycles_count):
        time.sleep_ms(100)
        time.sleep_us(wait_time_us)
        shunt_v, bus_v, curr, pwr = ina219.get_shunt_voltage(), ina219.get_voltage(), ina219.get_current(), ina219.get_power()
        print(f"Shunt: {shunt_v} V;\tBus: {bus_v}\tCurrent: {curr}\tpower: {pwr}")
        # запрещаю калибровку, многократная калибровка не нужна! Команда на каждое измерение выдается вручную!
        ina219.start_measurement(continuous=False, enable_calibration=False)

    show_header("INA219. Настройки! Автоматический(!) режим измерений")
    ina219.start_measurement(continuous=True, enable_calibration=True)
    print(f"configuration: {ina219.get_config()}")
    for data in ina219:
        time.sleep_us(wait_time_us)
        print(f"data: {data}")
        time.sleep_ms(100)
