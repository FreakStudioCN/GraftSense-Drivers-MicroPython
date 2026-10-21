"""Run with MicroPython 1.23, not CPython, against injected peripherals.

micropython -X heapsize=32M tests/micropython_pr119_smoke.py REPO_ROOT
If asyncio is not frozen, add the official extmod directory as a second argument.
This validates VM semantics and driver control flow, not electrical hardware.
"""
import sys
import time

ROOT = sys.argv[1].replace('\\', '/')
if len(sys.argv) > 2:
    sys.path.append(sys.argv[2].replace('\\', '/'))
import asyncio
import json
import micropython

# The Windows port reserves a static 256-byte emergency exception buffer.
# Embedded ports expose this allocator instead; keep the real const/compiler.
if not hasattr(micropython, 'alloc_emergency_exception_buf'):
    class MicroPythonPort:
        def __getattr__(self, name): return getattr(micropython, name)
        def alloc_emergency_exception_buf(self, size): pass
    sys.modules['micropython'] = MicroPythonPort()


class Pin:
    IN, OUT, PULL_UP, IRQ_FALLING, IRQ_RISING = range(5)

    def __init__(self, number=None, mode=None, value=1, **kwargs):
        self.state, self.mode, self.handler = value, mode, None

    def value(self, value=None):
        if value is not None: self.state = value
        return self.state

    __call__ = value
    def on(self): self.value(1)
    def off(self): self.value(0)
    def init(self, mode=None, **kwargs): self.mode = mode
    def irq(self, handler=None, **kwargs): self.handler = handler


class Bus:
    def __init__(self, registers=None):
        self.registers = registers or {}
        self.writes = []

    def scan(self): return list(range(128))
    def readfrom_mem(self, address, reg, count, **kwargs):
        if reg == 0x12 and self.registers.get(reg, 0) & 1:
            self.registers[reg] &= ~1
        return bytes(self.registers.get(reg+i, 0) for i in range(count))
    def readfrom_mem_into(self, address, reg, buffer, **kwargs):
        buffer[:] = self.readfrom_mem(address, reg, len(buffer))
    def writeto_mem(self, address, reg, data, **kwargs):
        self.writes.append((address, reg, bytes(data)))
        for i, value in enumerate(data): self.registers[reg+i] = value
    def writeto(self, address, data, *args): return len(data)
    def readfrom_into(self, address, buffer, *args): buffer[:] = bytes(len(buffer))


class Machine:
    I2C = SoftI2C = Bus
    Pin = Pin
    SPI = UART = Timer = object
    @staticmethod
    def disable_irq(): return 0
    @staticmethod
    def enable_irq(state): pass


sys.modules['machine'] = Machine
sys.modules['uasyncio'] = asyncio
loaded = []


def load(package, name):
    sys.path.insert(0, ROOT+'/'+package+'/code')
    try:
        module = __import__(name)
        for part in name.split('.')[1:]: module = getattr(module, part)
        loaded.append(name)
        return module
    finally:
        sys.path.pop(0)


def blank(cls):
    """Inject state without relying on CPython's object.__new__ helper."""
    class Blank(cls):
        def __init__(self): pass
    return Blank()


async def cancel_after_first_yield(operation):
    task = asyncio.create_task(operation)
    await asyncio.sleep_ms(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        return
    raise AssertionError('cancellation was swallowed')


async def main():
    assert sys.implementation.name == 'micropython'
    load('sensors/dps310_async_driver', 'dps310_async')
    load('sensors/icp10111_async_driver', 'icp10111_async')
    load('sensors/tmp117_async_driver', '_gs_tmp117_i2c_helpers_async')

    ft = load('input/ft6x06_async_driver', 'ft6x06_async')
    assert not hasattr(sys.modules['_gs_ft6x06_ft6x06'], '_REG_TD_STATUS')
    sensor = blank(ft.FT6x06Async)
    sensor.i2c, sensor.i2c_addr = Bus({2: 1}), 0x38
    assert await sensor.get_touch_count_async() == 1

    ft = load('input/ft5336_async_driver', 'ft5336_async')
    sensor = blank(ft.FT5336Async)
    sensor.i2c, sensor.i2c_addr = Bus({2:1,3:0,4:18,5:0,6:52}), 0x38
    sensor._read_buffer = bytearray(33)
    sensor.max_touches = 5
    sensor._touch_x, sensor._touch_y, sensor._touch_id = [0]*5, [0]*5, [0]*5
    sensor._invert_x = sensor._invert_y = sensor._swap_xy = False
    assert await sensor.touched_async() == 1
    assert await sensor.touches_async() == [(18,52,1)]

    drv = load('motor_drivers/drv2605l_async_driver', 'drv2605l_async')
    class Effects:
        def _write_u8(self, reg, value): assert reg == 12 and value == 1
        def _read_u8(self, reg): assert reg == 12; return 0
    sensor = blank(drv.DRV2605Async)
    sensor._driver = Effects()
    assert await sensor.play_effect_async()

    mpu = load('sensors/mpu9250_async_driver', 'ak8963_async')
    sensor = await mpu.MPU9250Async.create_async(Bus({0:0x48,0x75:0x71,0x10:128,0x11:128,0x12:128}))
    await sensor.acceleration_async()
    await sensor.aclose()

    lsm = load('sensors/lsm6dsox_async_driver', 'lsm6dsox_async')
    sensor = lsm.LSM6DSOXAsync(Bus({0x0f:0x6c}))
    assert sensor._i2c.writes == []
    await sensor.initialize_async()
    await sensor.read_acceleration_async()
    await sensor.aclose(); await sensor.aclose()

    lis = load('sensors/ls3hd_async_driver', 'lis3dh_async')
    sensor = blank(lis.LIS3DH_I2CAsync)
    sensor._i2c, sensor._address = Bus(), 0x18
    for adc in (1,2,3):
        assert await sensor.read_adc_raw_async(adc) == sensor.read_adc_raw(adc)
        assert await sensor.read_adc_mV_async(adc) == sensor.read_adc_mV(adc)

    for name in ('lis2mdl','lis3mdl'):
        module = load('sensors/'+name+'_async_driver', '_gs_'+name+'_micropython_'+name+'.'+name+'_async')
        cls = getattr(module, name.upper()+'Async')
        sensor = blank(cls)
        await sensor.aclose(); await sensor.aclose()

    pcf = load('input/pcf8574_io8_async_driver', 'pcf8574_async')
    calls = []
    sensor = pcf.PCF8574Async(Bus(), callback=lambda value:calls.append(value))
    sensor._scheduled_handler(None)
    assert calls == []
    await sensor.dispatch_pending_async()
    assert calls == [0]
    await sensor.aclose()

    gt = load('input/gt911_async_driver','gt911_async')
    sensor = gt.GT911Async(Bus(),8,9)
    await cancel_after_first_yield(sensor.reset_async())
    assert sensor.rst_pin.value() == 1 and sensor.int_pin.mode == Pin.IN
    await sensor.aclose()

    sx = load('communication/sx1276_async_driver','sx1276_async')
    class SPI:
        def write(self, data): pass
        def read(self, count, *args): return bytes(count)
    reset = Pin()
    sensor = sx.SX1276Async(SPI(),Pin(),reset,Pin(),Pin(),1,[433000000])
    await cancel_after_first_yield(sensor.initialize_async())
    assert reset.value() == 1
    await sensor.aclose(); await sensor.aclose()

    relay = load('misc/relay_async_driver','relay_async')
    sensor = relay.RelayControllerAsync('latching',1,2)
    await cancel_after_first_yield(sensor.on_async())
    assert sensor.pin1.value() == sensor.pin2.value() == 0
    await sensor.aclose(); await sensor.aclose()

    radio = load('communication/lora_async_driver','e22_900m22s_async')
    ocp = radio.SX126X_REG_OCP_CONFIGURATION
    class Radio:
        _busy_timeout_ms = 100
        async def read_register_async(self, reg, count, timeout): return b'\x12' if reg==ocp else b'\x00'
    sensor = blank(radio.E22_900M22SAsync)
    sensor._radio = Radio()
    restored = []
    async def write(reg,value):
        if reg == ocp: restored.append(value)
    async def command(opcode,data,operation):
        if operation == 'SetPaConfig': await asyncio.sleep_ms(1000)
    sensor._write_register_async, sensor._command_async = write, command
    await cancel_after_first_yield(sensor._configure_output_power_async(14))
    assert restored == [b'\x12']

    sim = load('communication/sim7600_async_driver','sim7600_async')
    commands = []
    class Modem:
        async def command_async(self,command,*args): commands.append(command); return 'OK'
    modem = Modem()
    await sim.GPSAsync(modem).set_satellite_beidou_async()
    await sim.GPSAsync(modem).start_search_satellite_async()
    await sim.HTTPAsync(modem).get_ip_async()
    assert commands == ['AT+CGPSNMEA=196608','AT+CGPSFTM=1','AT+CGCONTRDP']

    bh = load('sensors/BH1750_async_driver','bh_1750_async')
    sensor = bh.BH1750Async(0x23,Bus())
    values = []
    async for lux in sensor.measurements_async():
        values.append(lux)
        if len(values)==2: break
    assert values == [0.0,0.0]

    pcf = load('input/pcf8575_async_driver','pcf8575_async')
    joy = load('input/ps2_joystick_async_driver','joystick_async')
    wheel = load('input/wheelswitch_async_driver','encoder_wheel_switch_async')
    ads = load('signal_acquisition/ads1115_async_driver','ads1115_async')
    counts = []
    async def callback(*args): counts.append(1)
    probe = callback()
    assert not hasattr(probe,'__await__')
    await probe
    counts.clear()
    sensor = blank(pcf.PCF8575Async)
    sensor._event_pending, sensor._async_callback = True, callback
    await sensor.dispatch_pending_async()
    class ADC:
        def read_u16(self): return 0
    sensor = joy.JoystickAsync(ADC(),ADC())
    async def sampled(*args): counts.append(1); sensor._running=False
    sensor.callback, sensor._running = sampled, True
    await sensor._sample_loop()
    up,down = Pin(),Pin()
    sensor = wheel.EncoderWheelSwitchAsync(up,down,debounce_ms=1,callback_up=callback)
    up.value(0); sensor._up_pending=True
    await sensor.dispatch_pending_async()
    sensor = blank(ads.ADS1115Async)
    sensor._alert_pending, sensor._alert_callback, sensor._alert_pin = True, callback, Pin()
    await sensor.wait_alert_async()
    assert len(counts)==4

    si = load('signal_generation/si5351_async_driver','silicon5351_async')
    bus = Bus()
    sensor = si.SI5351_I2CAsync(bus,25000000)
    assert bus.writes == []
    await sensor.initialize_async()
    assert sensor._initialized
    await sensor.aclose()
    class Processor:
        def read_and_parse(self): return []
        def build_and_send_frame(self, *args): pass
    for name in ('r60afd1','r60amp1'):
        module = load('sensors/'+name+'_async_driver',name+'_async')
        sensor = getattr(module,name.upper()+'Async')(Processor())
        assert not sensor._state._initialization_complete
        await sensor.start()
        await asyncio.sleep_ms(0)
        await sensor.aclose()
    print(json.dumps({'runtime':sys.version,'packages':len(loaded),'passed':True,'hardware_tested':False}))


if __name__ == '__main__':
    asyncio.run(main())
