"""Regressions from the complete PR119 review; real methods, injected buses.

Host tests verify control flow and source parity. They do not replace electrical
timing or board validation. tests/micropython_pr119_smoke.py checks VM semantics.
"""
import ast
import __future__
import asyncio
import importlib
import importlib.machinery
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

import test_async_regressions as env

ROOT = env.ROOT


def annotation_ignoring_code(loader, name):
    """MicroPython ignores annotations; do not diagnose CPython-only names."""
    return compile(loader.get_data(loader.path), loader.path, 'exec',
                   flags=__future__.annotations.compiler_flag, dont_inherit=True)


class Pin(env.MachinePin):
    pins = {}

    def __init__(self, number=None, mode=None, value=1):
        self.number, self.mode, self.state = number, mode, value
        self.events = [(value, time.monotonic())]
        self.mode_events = [(mode, time.monotonic())]
        self.handler = None
        self.pins[number] = self

    def value(self, value=None):
        if value is not None:
            self.state = value
            self.events.append((value, time.monotonic()))
        return self.state

    def init(self, mode=None, **kwargs):
        self.mode = mode
        self.mode_events.append((mode, time.monotonic()))

    def irq(self, handler=None, **kwargs):
        self.handler = handler

    def on(self): self.value(1)
    def off(self): self.value(0)


class Registers(env.Bus, env.machine.I2C):
    def __init__(self, chip=0x6c, stuck=False):
        super().__init__()
        self.registers = {0x0f: chip}
        self.busy_reads, self.stuck = 0, stuck

    def readfrom_mem(self, address, reg, count):
        self.events.append(('read', address, reg, count))
        if reg == 0x12 and self.registers.get(reg, 0) & 1:
            if self.busy_reads:
                self.busy_reads -= 1
            elif not self.stuck:
                self.registers[reg] &= ~1
        return bytes(self.registers.get(reg + i, 0) for i in range(count))

    def writeto_mem(self, address, reg, data):
        super().writeto_mem(address, reg, data)
        for i, value in enumerate(data): self.registers[reg+i] = value
        if reg == 0x12 and data[0] & 1: self.busy_reads = 2


async def cancel_after(coroutine, delay=0, twice=False):
    task = asyncio.create_task(coroutine)
    await asyncio.sleep(delay)
    task.cancel()
    if twice:
        await asyncio.sleep(.002)
        task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        return
    raise AssertionError('cancellation was swallowed')


class InstalledImports(unittest.TestCase):
    def test_only_manifest_payload_is_required_for_corrected_imports(self):
        for package, module in [
            ('sensors/dps310_async_driver', 'dps310_async'),
            ('sensors/icp10111_async_driver', 'icp10111_async'),
            ('sensors/tmp117_async_driver', 'i2c_helpers_async'),
            ('input/ft6x06_async_driver', 'ft6x06_async'),
        ]:
            with self.subTest(package=package), tempfile.TemporaryDirectory() as folder:
                pkg = ROOT/package
                for destination, source in json.loads((pkg/'package.json').read_text('utf-8'))['urls']:
                    target = Path(folder)/destination
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(pkg/source, target)
                program = (
                    'import sys,importlib;sys.path.insert(0,sys.argv[1]);'
                    'import test_async_regressions;'
                    'from test_pr119_review_fixes import annotation_ignoring_code;'
                    'importlib.machinery.SourceFileLoader.get_code=annotation_ignoring_code;'
                    'sys.path.insert(0,sys.argv[2]);'
                    'importlib.import_module(sys.argv[3])'
                )
                p = subprocess.run([sys.executable, '-c', program, str(ROOT/'tests'), folder, module], capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, p.stderr)


class ReviewedAsyncFixes(unittest.IsolatedAsyncioTestCase):
    async def test_mpu9250_factory_and_start_keep_runtime_state(self):
        m = env.load('sensors/mpu9250_async_driver', 'ak8963_async')
        bus = Registers()
        bus.registers.update({0x75:0x71,0x10:128,0x11:128,0x12:128})
        with (patch.object(m.MPU6500, '__init__', side_effect=AssertionError('sync startup')),
              patch.object(m.AK8963, '__init__', side_effect=AssertionError('sync startup'))):
            sensor = await m.MPU9250Async.create_async(bus)
            self.assertIs(sensor._i2c, bus)
            self.assertIsInstance(sensor.mpu6500, m.MPU6500Async)
            self.assertIsInstance(sensor.ak8963, m.AK8963Async)
            self.assertEqual(await sensor.acceleration_async(), sensor.acceleration)
            await sensor.start_async()
            await sensor.aclose()

    async def test_deferred_state_construction_keeps_source_methods(self):
        si = env.load('signal_generation/si5351_async_driver', 'silicon5351_async')
        bus = env.Bus()
        with patch.object(si.SI5351_I2C, '__init__', side_effect=AssertionError('sync startup')):
            sensor = si.SI5351_I2CAsync(bus,25000000)
        self.assertEqual(bus.events, [])
        await sensor.initialize_async()
        original = env.load_source('signal_generation/si5351_driver', 'silicon5351')
        reference = env.Bus()
        original.SI5351_I2C(reference,25000000)
        self.assertEqual(bus.events, reference.events)
        processor = types.SimpleNamespace(read_and_parse=lambda: [], build_and_send_frame=lambda *args: None)
        for name in ('r60afd1','r60amp1'):
            module = env.load('sensors/'+name+'_async_driver',name+'_async')
            base = getattr(module,name.upper())
            with patch.object(base,'__init__',side_effect=AssertionError('sync startup')):
                sensor = getattr(module,name.upper()+'Async')(processor)
            self.assertIsInstance(sensor._state,base)
            self.assertFalse(sensor._state._initialization_complete)
            await sensor.start()
            await asyncio.sleep(0)
            await sensor.aclose()

    async def test_lsm6dsox_source_order_and_cooperative_startup(self):
        m = env.load('sensors/lsm6dsox_async_driver', 'lsm6dsox_async')
        bus = Registers()
        sensor = m.LSM6DSOXAsync(bus)
        self.assertEqual(bus.events, [])
        with self.assertRaises(RuntimeError): await sensor.read_acceleration_async()
        baseline_bus = Registers()
        with patch.object(sys.modules[m.LSM6DSOX.__module__], 'sleep', lambda _: None):
            baseline = m.LSM6DSOX(baseline_bus)
        _, beats = await env.heartbeat_during(lambda: sensor.initialize_async())
        writes = lambda b: [event for event in b.events if event[0] == 'write']
        self.assertEqual(writes(bus), writes(baseline_bus))
        self.assertGreater(beats, 1)
        self.assertEqual(sensor._cached_acceleration_range, baseline._cached_acceleration_range)
        self.assertEqual(sensor._cached_gyro_range, baseline._cached_gyro_range)
        self.assertEqual(await sensor.read_acceleration_async(), baseline.acceleration)
        self.assertEqual(await sensor.read_gyro_async(), baseline.gyro)
        previous = len(bus.events)
        await sensor.initialize_async()
        self.assertEqual(len(bus.events), previous)
        await sensor.aclose()
        previous = len(bus.events)
        await sensor.aclose()
        self.assertEqual(len(bus.events), previous)

    async def test_lsm6dsox_reset_timeout_cancel_and_identity_failure(self):
        m = env.load('sensors/lsm6dsox_async_driver', 'lsm6dsox_async')
        sensor = m.LSM6DSOXAsync(Registers(stuck=True))
        started = time.monotonic()
        with self.assertRaises(TimeoutError): await sensor.reset_async(5)
        self.assertLess(time.monotonic()-started, .5)
        await cancel_after(sensor.initialize_async(), .002)
        self.assertFalse(sensor._initialized)
        self.assertEqual(sensor._i2c.registers[0x10] & 0xf0, 0)
        with patch.object(m.LSM6DSOX, 'deinit', side_effect=OSError('bus disconnected')):
            await cancel_after(sensor.initialize_async(), .002)
        self.assertFalse(sensor._initialized)
        bad_bus = Registers(chip=0)
        with self.assertRaises(RuntimeError): await m.LSM6DSOXAsync(bad_bus).initialize_async()
        self.assertFalse(any(event[0]=='write' for event in bad_bus.events))

    async def test_lis3dh_adc_channels_and_source_validation(self):
        m = env.load('sensors/ls3hd_async_driver', 'lis3dh_async')
        obj = m.LIS3DH_I2CAsync.__new__(m.LIS3DH_I2CAsync)
        obj._i2c, obj._address = Registers(), 0x18
        for adc in (1, 2, 3):
            self.assertEqual(await obj.read_adc_raw_async(adc), obj.read_adc_raw(adc))
            self.assertEqual(await obj.read_adc_mV_async(adc), obj.read_adc_mV(adc))
        for adc in (0, 4):
            with self.assertRaises(ValueError): await obj.read_adc_raw_async(adc)

    async def test_magnetometer_close_owns_no_bus(self):
        for name in ('lis2mdl', 'lis3mdl'):
            with patch.object(importlib.machinery.SourceFileLoader, 'get_code', annotation_ignoring_code):
                m = env.load('sensors/'+name+'_async_driver', '_gs_'+name+'_micropython_'+name+'.'+name+'_async')
            cls = getattr(m, name.upper()+'Async')
            sensor = cls.__new__(cls)
            sensor._i2c = object()
            await sensor.aclose()
            await sensor.aclose()
            self.assertIsNotNone(sensor._i2c)

    async def test_sim7600_commands_equal_trusted_source(self):
        m = env.load('communication/sim7600_async_driver', 'sim7600_async')
        loc = env.load('communication/sim7600_async_driver', '_gs_sim7600_sim7600.location')
        http = env.load('communication/sim7600_async_driver', '_gs_sim7600_sim7600.http')
        for base, adapter, method in [(loc.GPS,m.GPSAsync,'set_satellite_beidou'), (loc.GPS,m.GPSAsync,'start_search_satellite'), (http.HTTP,m.HTTPAsync,'get_ip')]:
            commands = []
            def send(command, *args, **kwargs): commands.append(command); return 'OK'
            async def command(command, *args, **kwargs): commands.append(command); return 'OK'
            modem = types.SimpleNamespace(send_command=send, command_async=command)
            source = base.__new__(base); source.sim7600 = modem
            expected = getattr(source, method)()
            actual = await getattr(adapter(modem), method+'_async')()
            self.assertEqual(commands[0], commands[1])
            self.assertEqual(actual, expected)

    async def test_gt911_cancel_at_each_reset_phase_restores_pins(self):
        m = env.load('input/gt911_async_driver', 'gt911_async')
        for delay in (0, .02, .08):
            with self.subTest(delay=delay), patch.object(m, 'Pin', Pin):
                sensor = m.GT911Async(env.Bus(), 8, 9)
                await cancel_after(sensor.reset_async(), delay, twice=True)
                self.assertEqual(sensor.rst_pin.state, 1)
                self.assertEqual(sensor.int_pin.mode, Pin.IN)
                rise = next(at for value, at in sensor.rst_pin.events if value == 1)
                low = sensor.rst_pin.events[0][1]
                input_at = sensor.int_pin.mode_events[-1][1]
                self.assertGreaterEqual(rise-low, .010)
                self.assertGreaterEqual(input_at-rise, .054)
                await sensor.aclose()
                await sensor.aclose()

    async def test_sx1276_cancel_releases_reset_and_close_repeats(self):
        m = env.load('communication/sx1276_async_driver', 'sx1276_async')
        for delay in (0, .012):
            spi = types.SimpleNamespace(write=lambda data: None, read=lambda count,*args: bytes(count))
            reset = Pin()
            obj = m.SX1276Async(spi, Pin(), reset, Pin(), Pin(), 1, [433000000])
            await cancel_after(obj.initialize_async(), delay, twice=True)
            self.assertEqual(reset.state, 1)
            low = next(at for value, at in reset.events if value == 0)
            rise = next(at for value, at in reset.events if value == 1 and at > low)
            self.assertGreaterEqual(rise-low, .009)
            await obj.aclose()
            await obj.aclose()

    async def test_relay_cancel_finishes_pulse_and_serializes_output(self):
        m = env.load('misc/relay_async_driver', 'relay_async')
        with patch.object(m, 'Pin', Pin):
            for state in (True, False):
                obj = m.RelayControllerAsync('latching', 1, 2)
                await cancel_after(obj.on_async() if state else obj.off_async(), .002, twice=True)
                self.assertEqual([obj.pin1.state,obj.pin2.state], [0,0])
                active = obj.pin1 if state else obj.pin2
                high = next(at for value,at in active.events[2:] if value == 1)
                low = next(at for value,at in active.events if value == 0 and at > high)
                self.assertGreaterEqual(low-high, .049)
                self.assertEqual(await obj.get_state_async(), state)
                await obj.aclose(); await obj.aclose()
            obj = m.RelayControllerAsync('latching', 1, 2)
            await asyncio.gather(obj.on_async(), obj.off_async())
            events = sorted([(at,1,value) for value,at in obj.pin1.events[2:]]+[(at,2,value) for value,at in obj.pin2.events[2:]])
            levels = {1:0,2:0}
            for _,pin,value in events:
                levels[pin]=value
                self.assertLessEqual(sum(levels.values()),1)

    async def test_lora_cancel_restores_ocp_and_preserves_original_failure(self):
        m = env.load('communication/lora_async_driver', 'e22_900m22s_async')
        for fail_cleanup in (False, True):
            obj = m.E22_900M22SAsync.__new__(m.E22_900M22SAsync)
            ocp = m.SX126X_REG_OCP_CONFIGURATION
            values = {ocp:b'\x12'}
            started = asyncio.Event()
            async def read(reg, size, timeout): return values.get(reg,b'\x00')
            async def write(reg, value):
                if reg == ocp and fail_cleanup: raise m.SX126XError('cleanup failed')
                values[reg]=value
            async def command(opcode, data, operation):
                if operation == 'SetPaConfig':
                    values[ocp]=b'\x38'; started.set(); await asyncio.sleep(60)
            obj._radio = types.SimpleNamespace(_busy_timeout_ms=100,read_register_async=read)
            obj._write_register_async=write; obj._command_async=command
            task = asyncio.create_task(obj._configure_output_power_async(14))
            await started.wait(); task.cancel()
            with self.assertRaises(asyncio.CancelledError): await task
            if not fail_cleanup: self.assertEqual(values[ocp],b'\x12')

    async def test_pcf8574_irq_dispatch_in_task_context(self):
        m = env.load('input/pcf8574_io8_async_driver', 'pcf8574_async')
        class Bus(Registers):
            def readfrom_into(self,address,buffer): self.events.append(('port',)); buffer[0]=0x3a
        calls=[]; bus=Bus()
        obj=m.PCF8574Async(bus,callback=lambda value:calls.append(value))
        obj._scheduled_handler(None)
        self.assertEqual(bus.events,[]); self.assertEqual(calls,[])
        self.assertTrue(await obj.dispatch_pending_async())
        self.assertEqual(calls,[0x3a])
        self.assertFalse(await obj.dispatch_pending_async())
        obj._irq_dropped=True
        self.assertTrue(await obj.dispatch_pending_async())
        self.assertEqual(calls,[0x3a,0x3a])
        await obj.aclose(); await obj.aclose()

    async def test_sync_native_and_micropython_style_callbacks_execute_once(self):
        pcf = env.load('input/pcf8575_async_driver','pcf8575_async')
        joy = env.load('input/ps2_joystick_async_driver','joystick_async')
        wheel = env.load('input/wheelswitch_async_driver','encoder_wheel_switch_async')
        ads = env.load('signal_acquisition/ads1115_async_driver','ads1115_async')
        for kind in ('sync','async','generator'):
            for device in ('pcf','joy','wheel','ads'):
                with self.subTest(kind=kind,device=device):
                    calls=[]
                    def completed(*args):
                        calls.append(args)
                        if device=='joy': obj._running=False
                    async def native(*args): completed(*args)
                    @types.coroutine
                    def generator(*args):
                        completed(*args)
                        if False: yield None
                    callback={'sync':completed,'async':native,'generator':generator}[kind]
                    if device=='pcf':
                        obj=pcf.PCF8575Async.__new__(pcf.PCF8575Async)
                        obj._event_pending=True; obj._async_callback=callback
                        await obj.dispatch_pending_async()
                    elif device=='joy':
                        adc=types.SimpleNamespace(read_u16=lambda:0)
                        obj=joy.JoystickAsync(adc,adc,callback=callback)
                        obj._running=True
                        await asyncio.wait_for(obj._sample_loop(),.2)
                    elif device=='wheel':
                        up,down=Pin(),Pin()
                        obj=wheel.EncoderWheelSwitchAsync(up,down,debounce_ms=1,callback_up=callback)
                        up.value(0); obj._up_pending=True
                        await obj.dispatch_pending_async()
                    else:
                        obj=ads.ADS1115Async.__new__(ads.ADS1115Async)
                        obj._alert_pending=True; obj._alert_pin=Pin(); obj._alert_callback=callback
                        await obj.wait_alert_async(10)
                    self.assertEqual(len(calls),1)

    async def test_bh1750_explicit_async_iterator_keeps_waits_and_values(self):
        m=env.load('sensors/BH1750_async_driver','bh_1750_async')
        sensor=m.BH1750Async.__new__(m.BH1750Async)
        sensor._measurement_mode=m.BH1750.MEASUREMENT_MODE_CONTINUOUSLY
        sensor._measurement_time=m.BH1750.MEASUREMENT_TIME_DEFAULT
        async def measure(timeout): return 123.0
        sensor.measurement_async=measure
        stream=sensor.measurements_async(250)
        self.assertIs(stream.__aiter__(),stream)
        started=time.monotonic(); values=[]
        async for value in stream:
            values.append(value)
            if len(values)==2: break
        self.assertEqual(values,[123.0,123.0])
        self.assertGreaterEqual(time.monotonic()-started,.119)
        stream=sensor.measurements_async(1)
        self.assertEqual(await stream.__anext__(),123.0)
        with self.assertRaises(TimeoutError): await stream.__anext__()


if __name__=='__main__': unittest.main()
