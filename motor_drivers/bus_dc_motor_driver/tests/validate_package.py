"""安装清单、依赖闭包和默认不运动检查；不访问真实设备。"""
import ast
import json
import runpy
import struct
import sys
import types
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'package.json').read_text(encoding='utf-8'))
assert manifest['name']=='bus_dc_motor_driver'
assert manifest['version']=='1.1.0'
assert (ROOT/'LICENSE').is_file() and manifest['license']=='MIT'
entries=manifest['urls']
names=[Path(target).stem for target,_ in entries]
assert len(names)==7 and len(set(names))==len(names)
allowed={'time','math','machine','ustruct','micropython'}|set(names)
for target,source in entries:
    assert target==Path(target).name and target.endswith('.py')
    file=ROOT/source
    assert file.is_file(),source
    tree=ast.parse(file.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        imports=([a.name.split('.')[0] for a in node.names] if isinstance(node,ast.Import)
                 else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else [])
        assert all(name in allowed for name in imports),(source,imports)

def blocked(*args,**kwargs):
    raise AssertionError('Default entry accessed hardware')

sys.path[:0]=[str(ROOT/'code'),str(ROOT/'examples')]
machine=types.ModuleType('machine')
for name in ('Pin','I2C','ADC','disable_irq','enable_irq'):setattr(machine,name,blocked)
micropython=types.ModuleType('micropython')
micropython.alloc_emergency_exception_buf=lambda size: None
with patch.dict(sys.modules,{'machine':machine,'ustruct':struct,'micropython':micropython}):
    for file in (ROOT/'code/main.py',ROOT/'examples/single_motor_pid_demo.py',
                 ROOT/'examples/four_motor_pid_demo.py',ROOT/'examples/bus_dc_motor_demo.py'):
        runpy.run_path(str(file),run_name='__main__')
print('PASS: seven installable modules, local dependency closure, MIT notice and four default-off entries')
