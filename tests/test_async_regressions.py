"""Host control-flow regressions; GPIO timing and real devices need board tests.

Run with CPython 3.10+: python -m unittest discover -s tests -v
"""
import asyncio
import binascii
import builtins
import collections
import importlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
time.sleep_ms = lambda ms: time.sleep(ms / 1000)
time.ticks_ms = lambda: int(time.monotonic() * 1000)
time.ticks_diff = lambda a, b: a - b
time.ticks_add = lambda a, b: a + b
asyncio.sleep_ms = lambda ms: asyncio.sleep(ms / 1000)
# Some unchanged source modules expect MicroPython's const in builtins.
builtins.const = lambda value: value
micro = types.ModuleType('micropython')
micro.const = builtins.const
micro.native = micro.viper = lambda fn: fn
micro.alloc_emergency_exception_buf = lambda size: None
sys.modules['micropython'] = micro
machine = types.ModuleType('machine')
class MachinePin:
    IN, OUT, PULL_UP, IRQ_FALLING, IRQ_RISING = range(5)
machine.Pin = MachinePin
for name in ('I2C', 'SoftI2C', 'SPI', 'UART', 'Timer'):
    setattr(machine, name, type(name, (), {}))
machine.disable_irq = lambda: 0
machine.enable_irq = lambda state: None
sys.modules['machine'] = machine
for name, module in [('ustruct', struct), ('utime', time), ('ubinascii', binascii), ('ucollections', collections)]:
    sys.modules[name] = module

def load(package, name):
    path = ROOT / package / 'code'
    sys.path.insert(0, str(path))
    try:
        return importlib.import_module(name)
    finally:
        sys.path.pop(0)

def load_source(package, name):
    path = ROOT / package / 'code' / (name + '.py')
    spec = importlib.util.spec_from_file_location('_baseline_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class Pin:
    def __init__(self):
        self.state = 1
        self.events = []
    def value(self, value=None):
        if value is not None:
            self.state = value
            self.events.append((value, time.monotonic()))
        return self.state

class UART:
    def __init__(self, data=b''):
        self.data, self.frames = data, []
    def any(self):
        return len(self.data)
    def read(self, n=None):
        n = len(self.data) if n is None else n
        result, self.data = self.data[:n], self.data[n:]
        return result
    def write(self, frame):
        self.frames.append(bytes(frame))
        return len(frame)

class Bus:
    def __init__(self, chip=0):
        self.chip, self.events = chip, []
    def scan(self):
        self.events.append(('scan',))
        return [0x18]
    def readfrom_mem(self, address, reg, count):
        self.events.append(('read', address, reg, count))
        return bytes([self.chip if reg == 0 else 0]) * count
    def readfrom_mem_into(self, address, reg, buffer):
        buffer[:] = self.readfrom_mem(address, reg, len(buffer))
    def writeto_mem(self, address, reg, data):
        self.events.append(('write', address, reg, bytes(data)))
    def writeto(self, address, data):
        self.events.append(('write', address, bytes(data)))
    def readfrom_into(self, address, buffer):
        buffer[:] = bytes(len(buffer))

async def heartbeat_during(operation):
    beats = []
    async def heartbeat():
        while True:
            beats.append(time.monotonic())
            await asyncio.sleep(.001)
    task = asyncio.create_task(heartbeat())
    try:
        result = await operation()
        return result, len(beats)
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

class AsyncRegressions(unittest.IsolatedAsyncioTestCase):
    async def test_pr118_updated_source_packages_keep_importable_async_entries(self):
        for package, module, classname in [
            ('hdc1080', 'hdc1080_async', 'HDC1080Async'),
            ('lm75a', 'lm75a_async', 'LM75AAsync'),
            ('sht45', 'sht45_async', 'SHT45Async'),
        ]:
            m = load('sensors/' + package + '_async_driver', module)
            self.assertTrue(callable(getattr(m, classname)))

    async def test_ads_gain_indices_and_register_words(self):
        m = load('signal_acquisition/ads1015_async_driver', 'ads1015_async')
        class Driver:
            gain = 0
            def __init__(self): self.words = []
            def _write_register(self, register, value): self.words.append(value)
            def _read_register(self, register): return 0x8000 if register == 1 else 123
        driver = Driver()
        obj = m.ADS1115Async.__new__(m.ADS1115Async)
        m._ADSBaseAsync.__init__(obj, driver)
        for gain in range(6):
            await obj.set_gain_async(gain)
            self.assertEqual(await obj.read_async(0), 123)
            self.assertEqual(driver.words[-1] & 0x0e00, gain << 9)
        for invalid in (-1, 6, 512, '1'):
            with self.assertRaises(ValueError): await obj.set_gain_async(invalid)

    async def test_e103_at_mode_preserves_uart(self):
        m = load('communication/e103w02_async_driver', 'e103w02_async')
        obj = m.E103W02Async.__new__(m.E103W02Async)
        obj._uart, obj._uart_lock = UART(b'AT-response\n'), asyncio.Lock()
        obj._timeout_ms, obj._command_mode = 10, True
        for method, args in [(obj.read_async, ()), (obj.readline_async, ()), (obj.write_async, (b'hello',))]:
            with self.assertRaises(RuntimeError): await method(*args)
            self.assertEqual(obj._uart.data, b'AT-response\n')
            self.assertEqual(obj._uart.frames, [])
        obj._command_mode = False
        self.assertEqual(await obj.read_async(), b'AT-response\n')

    async def test_dds_modes_and_transitions(self):
        for package, module in [('ad9833', 'ad9833_async'), ('mcp41010', 'dds_async')]:
            with self.subTest(package=package):
                m = load('signal_generation/' + package + '_async_driver', module)
                class SPI:
                    def __init__(self): self.frames = []
                    def init(self, **kwargs): pass
                    def write(self, frame): self.frames.append(bytes(frame))
                spi = SPI()
                obj = m.AD9833Async(spi, Pin(), Pin())
                for mode, expected in [('SQUARE', 0x2068), ('SQUARE/2', 0x2060), ('OFF', 0x21c0), ('SIN', 0x2000), ('TRIANGLE', 0x2002), ('RESET', 0x2100)]:
                    await obj.set_mode_async(mode)
                    self.assertEqual(int.from_bytes(spi.frames[-1], 'big'), expected)

    async def test_e103_transparent_read_boundaries_match_source(self):
        m = load('communication/e103w02_async_driver', 'e103w02_async')
        obj = m.E103W02Async.__new__(m.E103W02Async)
        obj._uart, obj._uart_lock = UART(b'abc\ntail'), asyncio.Lock()
        obj._timeout_ms, obj._command_mode = 10, False
        self.assertEqual(await obj.readline_async(), b'abc\n')
        self.assertEqual(obj._uart.data, b'tail')
        self.assertEqual(await obj.read_async(100, timeout_ms=100), b'tail')
        self.assertEqual(await obj.readline_async(), b'')
        for value in (bytearray(b'a'), memoryview(b'b'), 'c'):
            self.assertEqual(await obj.write_async(value), 1)
        self.assertEqual(obj._uart.frames, [b'a', b'b', b'c'])
        with self.assertRaises(ValueError): await obj.read_async(0)
        with self.assertRaises(ValueError): await obj.readline_async(max_bytes=0)

    async def test_servo_final_pulse_and_cache(self):
        m = load('motor_drivers/iic_bus_16_servo_async_driver', 'bus_servo_async')
        class Controller:
            SERVO_180 = '180'
            def __init__(self, start, reverse):
                self._cfg = {0: {'type': self.SERVO_180, 'angle': start, 'min': 500, 'max': 2500, 'rev': reverse}}
                self.pulses = []
            def _ensure_channel(self, channel): pass
            def _ensure_attached(self, channel): pass
            def _clip(self, value, low, high): return min(max(value, low), high)
            def _write_pulse(self, channel, pulse): self.pulses.append(pulse)
        for start, target, reverse in [(0, 10, False), (30, 10, False), (0, 10, True)]:
            c = Controller(start, reverse)
            obj = m.BusPWMServoControllerAsync(c)
            await obj.set_angle_async(0, target, speed_deg_per_s=1000)
            physical = 180 - target if reverse else target
            self.assertEqual(c.pulses[-1], round(500 + 2000 * physical / 180))
            self.assertEqual(c._cfg[0]['angle'], target)

    async def test_ch9328_cancel_and_close_release_keys(self):
        m = load('input/ch9328_async_driver', 'ch9328_async')
        for operation in ('tap', 'text'):
            uart = UART()
            obj = m.CH9328Async(uart)
            await obj.set_keyboard_mode_async(3)
            call = obj.tap_key_async(4, delay=100) if operation == 'tap' else obj.type_text_async('Ab', delay=100)
            task = asyncio.create_task(call)
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError): await task
            self.assertEqual(uart.frames[-1], bytes(8))
            await obj.aclose()
            self.assertEqual(uart.frames[-1], bytes(8))

    async def test_cancelled_reset_pulses_release_after_minimum(self):
        cases = [
            ('communication/pn532_async_driver', 'pn532_uart_async', 'PN532_UARTAsync', '_reset', 100),
            ('input/cst816_async_driver', 'cst816_async', 'CST816Async', '_reset_pin', 5),
            ('input/cst328_async_driver', 'cst328_async', 'CST328Async', '_rst_pin', 10),
            ('input/ft6336_async_driver', 'ft6336_async', 'FT6336Async', '_reset_pin', 200),
            ('communication/si4732_async_driver', 'si4732_async', 'SI4732Async', '_reset_pin', 10),
            ('sensors/qmi8658_async_driver', 'qmi8658_async', 'QMI8658Async', '_reset_pin', 10),
            ('sensors/vl53l5cx_async_driver', 'vl53l5cx_async', 'VL53L5CXMPAsync', '_lpn', 100),
        ]
        for package, name, classname, attr, delay in cases:
            with self.subTest(package=package):
                m = load(package, name)
                cls = getattr(m, classname)
                obj = cls.__new__(cls)
                pin = Pin()
                setattr(obj, attr, pin)
                obj._RESET_DELAY_MS = delay
                obj._log = lambda *args: None
                obj._uart = UART()
                obj._lock = asyncio.Lock()
                task = asyncio.create_task(obj.reset_async())
                while pin.value() != 0: await asyncio.sleep(.001)
                task.cancel()
                await asyncio.sleep(.001)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError): await task
                self.assertEqual(pin.value(), 1)
                low_index = next(i for i, (value, t) in enumerate(pin.events) if value == 0)
                low = pin.events[low_index][1]
                high = next(t for value, t in pin.events[low_index + 1:] if value == 1)
                self.assertGreaterEqual((high - low) * 1000, delay - 1)
                self.assertEqual(obj._uart.frames, [])

    async def test_as726x_busy_wait_yields_and_timeout_includes_setup(self):
        m = load('sensors/as7263_async_driver', 'as726x_async')
        class BusyBus(Bus):
            def readfrom_mem_into(self, address, reg, buffer): buffer[:] = b'\x02'
        obj = m.AS726XAsync(BusyBus())
        started = time.monotonic()
        async def measurement():
            with self.assertRaises(RuntimeError):
                await obj.take_one_shot_sync_measurement(timeout_ms=20)
        _, beats = await heartbeat_during(measurement)
        self.assertGreater(beats, 1)
        self.assertLess(time.monotonic() - started, .2)
        self.assertFalse(obj._async_lock.locked())

    async def test_as7341_led_matches_source_and_yields(self):
        m = load('sensors/as7341_async_driver', 'as7341_async')
        bus = Bus()
        obj = m.AS7341Async(bus)
        self.assertEqual(bus.events, [])
        _, beats = await heartbeat_during(lambda: obj.set_led_current_async(10))
        self.assertGreater(beats, 5)
        expected = list(bus.events)
        syncbus = Bus()
        original = load_source('sensors/as7341_driver', 'as7341')
        sync = original.AS7341.__new__(original.AS7341)
        sync._bus, sync._address = syncbus, 0x39
        sync._buffer1, sync._buffer2 = bytearray(1), bytearray(2)
        sync.set_led_current(10)
        self.assertEqual(expected, syncbus.events)
        self.assertEqual(await obj.get_spectral_data_async(), (0, 0, 0, 0, 0, 0))

    async def test_as7341_startup_and_cancelled_bank_transaction(self):
        m = load('sensors/as7341_async_driver', 'as7341_async')
        class SpectralBus(Bus):
            def readfrom_mem(self, address, reg, count):
                data = super().readfrom_mem(address, reg, count)
                if reg == m.AS7341.AS7341_ID:
                    return bytes([m.AS7341.AS7341_ID_VALUE]) * count
                return data
        bus, reference = SpectralBus(), SpectralBus()
        obj = m.AS7341Async(bus)
        self.assertTrue(await obj.initialize_async())
        original = load_source('sensors/as7341_driver', 'as7341')
        sync = original.AS7341(reference)
        self.assertEqual(bus.events, reference.events)
        self.assertTrue(sync.isconnected())
        task = asyncio.create_task(obj.set_led_current_async(10))
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        self.assertFalse(obj._async_lock.locked())
        self.assertFalse(await obj.isconnected_async())
        last = next(e for e in reversed(bus.events) if e[0] == 'write' and e[2] == obj.AS7341_CFG_0)
        self.assertEqual(last[3][0] & obj.AS7341_CFG_0_REG_BANK, 0)

    async def test_as726x_one_shot_register_order_matches_source(self):
        m = load('sensors/as7263_async_driver', 'as726x_async')
        class VirtualBus:
            def __init__(self):
                self.events, self.virtual = [], {4: 0}
                self.pending_read, self.pending_write = None, None
            def readfrom_mem_into(self, addr, reg, buffer):
                self.events.append(('read', reg))
                if reg == 0:
                    buffer[0] = int(self.pending_read is not None)
                else:
                    buffer[0] = self.virtual.get(self.pending_read, 0)
                    self.pending_read = None
            def writeto_mem(self, addr, reg, buffer):
                value = buffer[0]
                self.events.append(('write', reg, value))
                if self.pending_write is not None:
                    register, self.pending_write = self.pending_write, None
                    self.virtual[register] = value | (2 if register == 4 and value & 12 == 12 else 0)
                elif value & 128:
                    self.pending_write = value & 127
                else:
                    self.pending_read = value
        bus, reference = VirtualBus(), VirtualBus()
        obj = m.AS726XAsync(bus)
        await obj.take_one_shot_sync_measurement()
        original = load_source('sensors/as7263_driver', 'as726x')
        original.AS726X(reference).take_one_shot_sync_measurement()
        self.assertEqual(bus.events, reference.events)

    async def test_gp2y_averaging_parity_and_cancellation(self):
        m = load('sensors/gp2y0a21yk_async_driver', 'gp2y0a21yk_async')
        class ADC:
            def __init__(self): self.reads = 0
            def read_u16(self): self.reads += 1; return 32000
        adc = ADC()
        obj = m.GP2Y0A21YKAsync(adc)
        original = load_source('sensors/gp2y0a21yk_driver', 'gp2y0a21yk')
        reference = original.GP2Y0A21YK(ADC())
        for average in (1, 4, 20):
            obj.set_averaging(average)
            reference.set_averaging(average)
            expected = reference.get_distance_centimeter()
            before = adc.reads
            result, beats = await heartbeat_during(obj.get_distance_centimeter_async)
            self.assertEqual(result, expected)
            self.assertEqual(adc.reads - before, average)
            self.assertGreater(beats, 0)
        with self.assertRaises(TypeError): await obj.is_closer_async('bad')
        task = asyncio.create_task(obj.get_distance_volt_async())
        await asyncio.sleep(0)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError): await task
        before = adc.reads
        await asyncio.sleep(.01)
        self.assertEqual(adc.reads, before)

    async def test_bma423_startup_is_awaited_and_matches_source(self):
        m = load('sensors/bma423_async_driver', 'bma423_async')
        bus = Bus(chip=0x13)
        obj = m.BMA423Async(bus)
        self.assertEqual(bus.events, [])
        _, beats = await heartbeat_during(obj.initialize_async)
        self.assertGreater(beats, 10)
        reference = Bus(chip=0x13)
        original = load_source('sensors/bma423_driver', 'bma423')
        original.BMA423(reference)
        self.assertEqual(bus.events, reference.events)
        before = len(bus.events)
        await obj.initialize_async()
        self.assertEqual(len(bus.events), before)

    async def test_bh1750_startup_is_awaited_and_matches_source(self):
        m = load('sensors/BH1750_async_driver', 'bh_1750_async')
        bus = Bus()
        obj = m.BH1750Async(0x23, bus)
        self.assertEqual(bus.events, [])
        _, beats = await heartbeat_during(obj.initialize_async)
        self.assertGreater(beats, 10)
        reference = Bus()
        original = load_source('sensors/BH1750_driver', 'bh_1750')
        original.BH1750(0x23, reference)
        self.assertEqual(bus.events, reference.events)

    async def test_atecc_import_status_and_full_config_packets(self):
        m = load('misc/atecc608a_async_driver', 'atecc608a_async')
        self.assertEqual(m.ATCA.ATCA_BLOCK_SIZE, 32)
        obj = m.ATECC608AAsync(Bus())
        addresses = []
        async def execute(packet, timeout):
            addresses.append(packet.param2)
            self.assertEqual(packet.param1, 0x80)
            return packet
        obj._execute_async = execute
        packets = await obj.atcab_read_config_zone_async()
        self.assertEqual(addresses, [0, 8, 16, 24])
        self.assertEqual(len(packets), 4)
        status = load('misc/atecc608a_async_driver', self._local_module('misc/atecc608a_async_driver', 'status.py'))
        self.assertEqual(status.decode_error(0x03)[0], 0xd2)
        self.assertIsNotNone(status.decode_error(0x03)[1])

    @staticmethod
    def _local_module(package, original):
        # Manifest maps also support isolated dependency filenames.
        data = json.loads((ROOT / package / 'package.json').read_text('utf-8-sig'))
        for destination, source in data['urls']:
            if source == 'code/' + original or Path(source).name.endswith('_' + original):
                return Path(destination).stem
        return Path(original).stem

if __name__ == '__main__':
    unittest.main()
