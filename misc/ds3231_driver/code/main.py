from machine import I2C
from ds3231maxim import DS3221
from sensor_pack.bus_service import I2cAdapter
import utime

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # Внимание!!!
    # Замените id=1 на id=0, если пользуетесь первым портом I2C !!!
    # Warning!!!
    # Replace id=1 with id=0 if you are using the first I2C port !!!
    i2c = I2C(id=1, freq=400_000)  # on Arduino Nano RP2040 Connect tested
    adaptor = I2cAdapter(i2c)
    clock = DS3221(adapter=adaptor)

    tr = utime.localtime()
    print(f"set time to actual value: {tr}")
    clock.set_time(tr)
    
    print(f"Call get_time() method")
    tr = clock.get_time()
    print(f"Local time: {tr}")
    
    tmp = clock.get_temperature()
    stat = clock.get_status()
    ctrl = clock.get_control()
    ao = clock.get_aging_offset()
    print(f"Temperature: {tmp}\tstatus: {hex(stat)}\tcontrol: {hex(ctrl)}\ttaging offset: {hex(ao)}")

    print("Alarm times:")
    print("get_alarm(0):", clock.get_alarm(0))
    print("get_alarm(1):", clock.get_alarm(1))

    at = (00, 10, 11, 12)
    k = 0   # Alarm when seconds match (every minute)
    print(f"Call: set_alarm({at}, {k})")
    clock.set_alarm(at, k, k)
    print(f"get_alarm({k}):", clock.get_alarm(k))
    k = 1
    clock.set_alarm(at, k, k)   # Alarm when hours and minutes match
    print(f"get_alarm({k}):", clock.get_alarm(k))

    print(f"Using iterator...")
    for ltime in clock:
        f = clock.get_alarm_flags()
        print(f"Local time: {ltime}\talarm flags: {f}")
        utime.sleep_ms(1000)
