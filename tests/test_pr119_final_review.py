"""Whole-installation and source-parity regressions from the final PR119 review."""
import ast
import asyncio
import collections
import importlib
import json
import types
from pathlib import Path
import unittest
from unittest.mock import patch

import test_async_regressions as env
from test_async_packages import installed_source
from test_pr119_review_fixes import Registers, cancel_after, annotation_ignoring_code

ROOT=env.ROOT

def program(path):
    tree=ast.parse(path.read_bytes())
    for node in ast.walk(tree):
        if hasattr(node,'body') and isinstance(node.body,list):
            node.body=[s for s in node.body if not isinstance(s,ast.Expr) or not isinstance(s.value,ast.Constant) or not isinstance(s.value.value,str)]
    return ast.dump(tree,include_attributes=False)

class GlobalInstallation(unittest.TestCase):
    def test_every_async_target_is_compatible_with_all_installed_packages(self):
        owners=collections.defaultdict(list)
        for manifest in ROOT.glob('*/*/package.json'):
            data=json.loads(manifest.read_text('utf-8-sig'))
            for target,source in data.get('urls',[]):
                path=installed_source(manifest,source)
                if target.endswith('.py') and path.is_file():
                    owners[target.casefold()].append((manifest.parent.name,program(path)))
        errors=[]
        for target,group in owners.items():
            if any(name.endswith('_async_driver') for name,_ in group) and len({p for _,p in group})>1:
                errors.append((target,[name for name,_ in group]))
        self.assertEqual(errors,[])

    def test_runtime_manifests_do_not_install_application_entry_points(self):
        for manifest in ROOT.glob('*/*_async_driver/package.json'):
            for target,_ in json.loads(manifest.read_text('utf-8-sig'))['urls']:
                self.assertNotIn(target,('main.py','boot.py','__init__.py'),manifest)
        ad=json.loads((ROOT/'sensors/ad8232_async_driver/package.json').read_text('utf-8'))
        self.assertEqual(ad['fw'],'ulab')

    def test_no_runtime_assumes_cpython_property_internals(self):
        errors=[]
        for package in ROOT.glob('*/*_async_driver'):
            for path in (package/'code').rglob('*.py'):
                for node in ast.walk(ast.parse(path.read_bytes())):
                    if isinstance(node,ast.Attribute) and node.attr in ('fget','fset','fdel','bit_length','bit_count'):
                        errors.append((str(path.relative_to(ROOT)),node.lineno))
        self.assertEqual(errors,[])

    def test_private_class_constants_used_as_attributes_are_retained(self):
        errors=[]
        for package in ROOT.glob('*/*_async_driver'):
            for path in (package/'code').rglob('*.py'):
                tree=ast.parse(path.read_bytes())
                exports={}
                for node in tree.body:
                    if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Attribute):
                        exports[ast.unparse(node.targets[0])]=node.value
                for cls in ast.walk(tree):
                    if not isinstance(cls,ast.ClassDef):continue
                    used={n.attr for n in ast.walk(cls) if isinstance(n,ast.Attribute)}
                    for node in cls.body:
                        if not isinstance(node,ast.Assign) or not isinstance(node.value,ast.Call):continue
                        if not isinstance(node.value.func,ast.Name) or node.value.func.id!='const':continue
                        for name in node.targets:
                            if not isinstance(name,ast.Name) or not name.id.startswith('_') or name.id not in used:continue
                            export=exports.get(cls.name+'.'+name.id)
                            if export is None or ast.dump(export)!=ast.dump(node.value.args[0]):
                                errors.append((str(path.relative_to(ROOT)),cls.name,name.id))
        self.assertEqual(errors,[])

    def test_timeout_and_io_exception_names_have_micropython_fallbacks(self):
        errors=[]
        for package in ROOT.glob('*/*_async_driver'):
            for path in (package/'code').rglob('*.py'):
                tree=ast.parse(path.read_bytes());bound=set()
                for node in ast.walk(tree):
                    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):bound.add(node.name)
                    if isinstance(node,ast.ImportFrom):bound.update(a.asname or a.name for a in node.names)
                    if isinstance(node,(ast.Assign,ast.AnnAssign)):
                        for target in node.targets if isinstance(node,ast.Assign) else [node.target]:
                            if isinstance(target,ast.Name):bound.add(target.id)
                loaded={n.id for n in ast.walk(tree) if isinstance(n,ast.Name) and isinstance(n.ctx,ast.Load)}
                missing=({'TimeoutError','IOError'}&loaded)-bound
                if missing:errors.append((str(path.relative_to(ROOT)),sorted(missing)))
        self.assertEqual(errors,[])

class ReadyBus(Registers):
    def __init__(self,ready=True):
        super().__init__()
        self.ready=ready
        self.registers.update({0x0d:0x10,0:0x48,0x75:0x71})
    def readfrom_mem(self,address,reg,count):
        if reg==8:
            self.events.append(('read',address,reg,count))
            return bytes([(self.registers.get(reg,0)&15)|(0xb0 if self.ready else 0)])
        return super().readfrom_mem(address,reg,count)

class FinalAsyncFixes(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        original=importlib.machinery.SourceFileLoader.get_code
        def get_code(loader,name):
            if Path(loader.path).is_relative_to(ROOT):return annotation_ignoring_code(loader,name)
            return original(loader,name)
        loader_patch=patch.object(importlib.machinery.SourceFileLoader,'get_code',get_code)
        loader_patch.start();self.addCleanup(loader_patch.stop)

    async def test_dps310_normal_startup_matches_source_and_timeout_is_bounded(self):
        module=env.load('sensors/dps310_async_driver','dps310_async')
        bus=ReadyBus();sensor=module.DPS310Async(bus)
        self.assertEqual(bus.events,[])
        await sensor.initialize_async()
        source=env.load_source('sensors/dps310_driver','micropython_dps310/dps310')
        reference=ReadyBus();baseline=source.DPS310(reference)
        self.assertEqual([e for e in bus.events if e[0]=='write'],[e for e in reference.events if e[0]=='write'])
        self.assertEqual(await sensor.get_pressure_async(),baseline.pressure)
        self.assertEqual(await sensor.get_temperature_async(),baseline.temperature)
        bad=module.DPS310Async(ReadyBus(False))
        async def timeout():
            with self.assertRaises(TimeoutError):await bad.initialize_async(10)
        _,beats=await env.heartbeat_during(timeout)
        self.assertGreater(beats,1)
        self.assertFalse(bad._initialized)
        await cancel_after(bad.initialize_async(),.002)
        self.assertFalse(bad._async_lock.locked())
        bad._i2c.ready=True
        await bad.initialize_async()
        await bad.aclose();await bad.aclose()

    async def test_standalone_mpu_and_magnetometer_preserve_source_startup(self):
        module=env.load('sensors/mpu9250_async_driver','ak8963_async')
        for name in ('MPU6500','AK8963'):
            cls=getattr(module,name+'Async')
            bus=ReadyBus();sensor=cls(bus)
            self.assertEqual(bus.events,[])
            _,beats=await env.heartbeat_during(sensor.initialize_async)
            self.assertGreater(beats,1)
            source=env.load_source('sensors/mpu9250_driver',name.lower())
            reference=ReadyBus();getattr(source,name)(reference)
            self.assertEqual(bus.events,reference.events)
            await sensor.aclose();await sensor.aclose()
            bad=cls(ReadyBus())
            await cancel_after(bad.initialize_async(),.002)
            self.assertFalse(bad._initialized)
            self.assertFalse(bad._async_lock.locked())

    async def test_composite_start_accepts_previous_children_without_async_state(self):
        module=env.load('sensors/mpu9250_async_driver','ak8963_async')
        class PreviousMPU(module.MPU6500):
            def __init__(self):pass
        class PreviousMAG(module.AK8963):
            def __init__(self):pass
        old_mpu,old_mag=PreviousMPU(),PreviousMAG()
        sensor=module.MPU9250Async(ReadyBus(),old_mpu,old_mag)
        await sensor.start_async()
        self.assertIsNot(sensor.mpu6500,old_mpu)
        self.assertIsNot(sensor.ak8963,old_mag)
        self.assertTrue(sensor.mpu6500._initialized and sensor.ak8963._initialized)
        children=(sensor.mpu6500,sensor.ak8963)
        await sensor.start_async()
        self.assertEqual((sensor.mpu6500,sensor.ak8963),children)
        await sensor.aclose()

    async def test_si1145_startup_write_order_matches_sync_source(self):
        module=env.load('sensors/si1145_async_driver','si1145_async')
        bus=ReadyBus();sensor=module.SI1145Async(bus)
        self.assertEqual(bus.events,[])
        _,beats=await env.heartbeat_during(sensor.initialize_async)
        self.assertGreater(beats,1)
        source=env.load_source('sensors/si1145_driver','si1145')
        reference=ReadyBus();source.SI1145(reference)
        self.assertEqual(bus.events,reference.events)
        before=len(bus.events);await sensor.initialize_async()
        self.assertEqual(len(bus.events),before)

    async def test_magnetometer_reset_writes_integer_bit_and_yields(self):
        for name in ('lis2mdl','lis3mdl'):
            module=env.load('sensors/'+name+'_async_driver','_gs_'+name+'_micropython_'+name+'.'+name+'_async')
            cls=getattr(module,name.upper()+'Async')
            sensor=cls.__new__(cls);sensor._i2c=ReadyBus();sensor._address=0x1e
            _,beats=await env.heartbeat_during(sensor.reset_async)
            self.assertGreater(beats,1)
            self.assertTrue(any(e[0]=='write' for e in sensor._i2c.events))

    async def test_ltr390_reset_preserves_retries_and_allows_cancellation(self):
        module=env.load('sensors/ltr390uv_async_driver','ltr390uv_async')
        class Register(dict):
            def __init__(self,steps):
                super().__init__();self.steps=iter(steps);self.events=[]
            def write(self):self.events.append(('write',self['soft_reset']))
            def read(self):
                step=next(self.steps);self.events.append(('read',step))
                if step=='timeout':raise OSError(110,'not ready')
                self['soft_reset']=step
        for steps in ([1,'timeout',0],[1,1,1]):
            obj=module.LTR390UVAsync.__new__(module.LTR390UVAsync)
            obj.ctrl_reg=Register(steps)
            reference=module.LTR390UV.__new__(module.LTR390UV)
            reference.ctrl_reg=Register(steps)
            async def operation():
                if steps[-1]:
                    with self.assertRaises(RuntimeError):await obj.soft_reset_async()
                else:await obj.soft_reset_async()
            _,beats=await env.heartbeat_during(operation)
            if steps[-1]:
                with self.assertRaises(RuntimeError):reference.soft_reset()
            else:reference.soft_reset()
            self.assertEqual(obj.ctrl_reg.events,reference.ctrl_reg.events)
            self.assertGreater(beats,1)
        obj.ctrl_reg=Register([1,1,1])
        await cancel_after(obj.soft_reset_async(),.002)
        self.assertEqual(obj.ctrl_reg.events,[('write',1)])

    async def test_portable_bit_ranges_and_constant_write_chunks_match_source(self):
        for package,name in [('adt7410','_gs_adt7410_i2c_helpers'),
                             ('mmc5603','_gs_mmc5603_micropython_mmc5603.i2c_helpers')]:
            adapter=env.load('sensors/'+package+'_async_driver',name)
            source_name='i2c_helpers' if package=='adt7410' else 'micropython_mmc5603/i2c_helpers'
            source=env.load_source('sensors/'+package+'_driver',source_name)
            for value in (-1,0,3,4):
                events=[]
                for provider in (adapter,source):
                    obj=types.SimpleNamespace(_i2c=ReadyBus(),_address=0x30)
                    field=provider.CBits(2,0x20,3)
                    if value in (-1,4):
                        with self.assertRaises(ValueError):field.__set__(obj,value)
                    else:field.__set__(obj,value)
                    events.append(obj._i2c.events)
                self.assertEqual(*events)
        for package in ('hscdtd008a','rm3100'):
            adapter=env.load('sensors/'+package+'_async_driver','_gs_'+package+'_sensor_pack.bus_service')
            source=env.load_source('sensors/'+package+'_driver','sensor_pack/bus_service')
            for value,count in ((0,0),(0,1),(255,16),(255,17),(127,33),(256,1)):
                streams=[]
                for provider in (adapter,source):
                    class Capture(provider.BusAdapter):
                        def write(self,address,data):self.events.append((address,bytes(data)))
                    obj=Capture(None);obj.events=[]
                    if value==256:
                        with self.assertRaises(ValueError):obj.write_const(0x30,value,count)
                    else:obj.write_const(0x30,value,count)
                    streams.append(obj.events)
                self.assertEqual(*streams)
