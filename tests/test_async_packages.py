"""Check actual install payloads against the synchronous packages."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE_NAMES = {
    'piranha_led_async_driver': 'piranha_led_drive',
    'uv_matrix_async_driver': 'uv_matrix',
    'jedm_gas_meas_async_driver': 'jedm_gas_meas',
}

class WithoutDocstrings(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return None
        return self.generic_visit(node)

def program(path):
    return ast.dump(WithoutDocstrings().visit(ast.parse(path.read_bytes())), include_attributes=False)

class AsyncPackages(unittest.TestCase):
    def test_local_install_targets_exist(self):
        packages = list(ROOT.glob('*/*_async_driver/package.json'))
        self.assertEqual(len(packages), 224)
        for manifest in packages:
            data = json.loads(manifest.read_text('utf-8-sig'))
            destinations = []
            for destination, source in data['urls']:
                destinations.append(destination)
                if not source.startswith(('http:', 'https:', 'github:')):
                    self.assertTrue((manifest.parent / source).is_file(), (manifest, source))
            self.assertEqual(len(destinations), len(set(destinations)), manifest)

    def test_install_does_not_replace_sync_with_different_python(self):
        for manifest in ROOT.glob('*/*_async_driver/package.json'):
            package = manifest.parent
            source = package.with_name(SOURCE_NAMES.get(package.name, package.name.replace('_async_driver', '_driver')))
            original_manifest = source / 'package.json'
            self.assertTrue(original_manifest.is_file(), package)
            originals = {destination: source / path for destination, path in json.loads(original_manifest.read_text('utf-8-sig'))['urls']}
            for destination, path in json.loads(manifest.read_text('utf-8-sig'))['urls']:
                candidate = package / path
                baseline = originals.get(destination)
                if baseline is not None and baseline.suffix == '.py' and baseline.is_file() and candidate.is_file():
                    self.assertEqual(program(candidate), program(baseline), (package.name, destination))

if __name__ == '__main__':
    unittest.main()
