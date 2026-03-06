# This is a sample Python script.
from machine import I2C, Pin
import bmp390mod
import time
from sensor_pack_2.bus_service import I2cAdapter


def pa_mmhg(value: float) -> float:
    """Перевод атмосферного давления из Па в мм рт.ст.
    Convert air pressure from Pa to mm Hg."""
    return 7.50062E-3 * value


if __name__ == '__main__':
    # пожалуйста установите выводы scl и sda в конструкторе I2C, для вашей платы, иначе ничего не заработает!
    # please set scl and sda pins for your board, otherwise nothing will work!
    # https://docs.micropython.org/en/latest/library/machine.I2C.html#machine-i2c
    # bus =  I2C(scl=Pin(4), sda=Pin(5), freq=100000)   # на esp8266    !
    # i2c = I2C(id=0, scl=Pin(13), sda=Pin(12), freq=400_000)  # on Arduino Nano RP2040 Connect
    i2c = I2C(id=1, scl=Pin(7), sda=Pin(6), freq=400_000)   # on Raspberry Pi Pico
    adaptor = I2cAdapter(i2c)
    # ps - pressure sensor
    ps = bmp390mod.Bmp390(adaptor)
    res = ps.get_id()
    print(f"chip_id: {res}")
    # если я не вызывал этот метод, то датчик не входил в режим
    # однократных измерений и был все время в режиме периодических измерений!!!
    # я не знаю, что это за глюк! Поэтому перед вызовом start_measurement(..) вызывайте soft_reset()!!
    ps.soft_reset()
    print(f"pwr mode: {ps.get_power_mode()}")

    calibration_data = [ps.get_calibration_coefficient(index) for index in range(14)]
    print(f"Calibration data: {calibration_data}")

    print(f"Event: {ps.get_event()}; Int status: {ps.get_int_status()}; FIFO length: {ps.get_fifo_length()}")
    #
    delay_func = time.sleep_ms
    #
    ps.set_oversampling(pressure_oversampling=2, temperature_oversampling=3)
    ps.set_sampling_period(5)
    ps.set_iir_filter(2)

    print("Режим однократных измерений по запросу!")
    print(f"pwr mode: {ps.get_power_mode()}")
    print(f"время преобразования в [мкс]: {ps.get_conversion_cycle_time()}")
    for _ in range(20):
        ps.start_measurement(enable_press=True, enable_temp=True, mode=1)
        delay_func(300)
        temperature_ready, pressure_ready, cmd_ready = ps.get_data_status()
        if cmd_ready and pressure_ready:
            t, p = ps.get_temperature(), ps.get_pressure()
            pm = ps.get_power_mode()
            print(f"Temperature: {t} \xB0C; pressure: {p} hPa ({pa_mmhg(p)} mm Hg); pwr_mode: {pm} ")
        else:
            print(f"Data ready: temp {temperature_ready}, press {pressure_ready}")
    #
    print("Режим непрерывных периодических измерений!")
    ps.start_measurement(enable_press=True, enable_temp=True, mode=2)
    print(f"pwr mode: {ps.get_power_mode()}")
    for values in ps:
        delay_func(300)
        d_status = ps.get_data_status()
        if d_status.cmd_decoder_ready and d_status.press_ready:
            t, p, tme = values.T, values.P, ps.get_sensor_time()
            pm = ps.get_power_mode()
            print(f"Temperature: {t} \xB0C; pressure: {p} hPa ({pa_mmhg(p)} mm Hg); pwr_mode: {pm}")
        else:
            print(f"Data ready: temp {d_status.temp_ready}, press {d_status.press_ready}")
