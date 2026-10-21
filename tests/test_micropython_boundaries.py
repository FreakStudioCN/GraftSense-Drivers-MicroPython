"""Installation-independent guards for MicroPython's private const boundary."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def top_statements(body):
    for node in body:
        yield node
        if isinstance(node, (ast.If, ast.Try)):
            for field in ('body', 'orelse', 'finalbody'):
                yield from top_statements(getattr(node, field, []))
            for handler in getattr(node, 'handlers', []):
                yield from top_statements(handler.body)


def constants(tree):
    result = {}
    for node in top_statements(tree.body):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'const':
            for target in node.targets:
                if isinstance(target, ast.Name): result[target.id] = node.value.args[0]
    return result


class MicroPythonBoundaries(unittest.TestCase):
    def test_runtime_does_not_rely_on_cpython_builtin_new(self):
        errors = []
        for package in ROOT.glob('*/*_async_driver'):
            for path in (package/'code').rglob('*.py'):
                for node in ast.walk(ast.parse(path.read_bytes())):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == '__new__':
                        errors.append((str(path.relative_to(ROOT)),node.lineno))
        self.assertEqual(errors, [], 'MicroPython built-in types do not expose object.__new__')

    def test_all_packages_respect_module_private_const_exports(self):
        errors = []
        for package in sorted(ROOT.glob('*/*_async_driver')):
            code = package/'code'
            modules = {}
            for path in code.rglob('*.py'):
                name = '.'.join(path.relative_to(code).with_suffix('').parts).removesuffix('.__init__')
                tree = ast.parse(path.read_bytes())
                modules[name] = (path,tree,{n for n in constants(tree) if n.startswith('_')})
            for name,(path,tree,_) in modules.items():
                aliases = {}
                parent = name if path.name == '__init__.py' else name.rpartition('.')[0]
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for item in node.names:
                            aliases[item.asname or item.name.split('.')[0]] = item.name if item.asname else item.name.split('.')[0]
                    elif isinstance(node, ast.ImportFrom):
                        prefix = parent.split('.')[:len(parent.split('.'))-node.level+1] if node.level else []
                        target = '.'.join(prefix+([node.module] if node.module else []))
                        for item in node.names:
                            if target+'.'+item.name in modules:
                                aliases[item.asname or item.name] = target+'.'+item.name
                            if target in modules and item.name in modules[target][2]:
                                errors.append((str(path.relative_to(ROOT)),node.lineno,item.name))
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Attribute): continue
                    parts = []; first = node
                    while isinstance(first, ast.Attribute):
                        parts.append(first.attr); first = first.value
                    if not isinstance(first, ast.Name) or first.id not in aliases: continue
                    parts.reverse()
                    target = '.'.join([aliases[first.id],*parts[:-1]])
                    if target in modules and parts[-1] in modules[target][2]:
                        errors.append((str(path.relative_to(ROOT)),node.lineno,parts[-1]))
        self.assertEqual(errors, [], 'Private consts disappear from module exports on MicroPython')

    def test_locally_mirrored_register_values_equal_source(self):
        groups = [
            ('input/ft5336_async_driver/code/ft5336_async.py', ['input/ft5336_driver/code/ft5336.py']),
            ('input/ft6x06_async_driver/code/ft6x06_async.py', ['input/ft6x06_driver/code/ft6x06.py']),
            ('motor_drivers/drv2605l_async_driver/code/drv2605l_async.py', ['motor_drivers/drv2605l_driver/code/drv2605l.py']),
            ('sensors/mpu9250_async_driver/code/ak8963_async.py', ['sensors/mpu9250_driver/code/ak8963.py','sensors/mpu9250_driver/code/mpu6500.py']),
        ]
        for adapter, providers in groups:
            source = {}
            for path in providers: source.update(constants(ast.parse((ROOT/path).read_bytes())))
            mirrored = constants(ast.parse((ROOT/adapter).read_bytes()))
            for name in mirrored.keys() & source.keys():
                with self.subTest(adapter=adapter, constant=name):
                    self.assertEqual(ast.dump(mirrored[name]), ast.dump(source[name]))


if __name__ == '__main__': unittest.main()
