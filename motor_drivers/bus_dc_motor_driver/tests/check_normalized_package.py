"""Static package checks for device code/examples; PC test fixtures are excluded."""

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = ("导入相关模块", "全局变量", "功能函数", "自定义类", "初始化配置", "主程序")
files = sorted((ROOT / "code").glob("*.py")) + sorted((ROOT / "examples").glob("*.py"))
methods = 0
for file in files:
    source = file.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    titles = re.findall(r"^# =+\s*(导入相关模块|全局变量|功能函数|自定义类|初始化配置|主程序)\s*=+\s*$", source, re.M)
    assert tuple(titles) == SECTIONS, (file.name, titles)
    assert source.splitlines()[6] == "# @License : MIT", file.name
    if file.parent.name == "code" and file.name != "main.py":
        metadata = {
            n.targets[0].id: ast.literal_eval(n.value)
            for n in tree.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id.startswith("__")
        }
        assert metadata["__version__"] == "1.1.0", file.name
        assert metadata["__author__"] in ("李清水", "赵岩松"), file.name
        assert metadata["__license__"] == "MIT", file.name
        assert "MicroPython" in metadata["__platform__"], file.name
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        assert node.returns is not None, (file.name, node.name, "return annotation")
        for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs:
            if arg.arg != "self":
                assert arg.annotation is not None, (file.name, node.name, arg.arg)
        if file.parent.name == "code" and file.name != "main.py" and (not node.name.startswith("_") or node.name == "__init__"):
            doc = ast.get_docstring(node) or ""
            assert all(section in doc for section in ("==================", "Args:", "Returns:", "Raises:", "Notes:")), (file.name, node.name)
            assert "ISR-safe" in doc, (file.name, node.name)
        methods += 1

manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
assert manifest["name"] == ROOT.name
sources = set()
for target, source in manifest["urls"]:
    for path in (target, source):
        assert not Path(path).is_absolute() and not path.startswith(("/", "\\")) and ".." not in Path(path).parts
    directory = ROOT
    for part in Path(source).parts:
        assert part in {entry.name for entry in directory.iterdir()}, source
        directory /= part
    sources.add(source)
assert sources == {"code/" + file.name for file in (ROOT / "code").glob("*.py") if file.name != "main.py"}
assert "MIT" in (ROOT / "LICENSE").read_text(encoding="utf-8")
print(f"PASS: {len(files)} device source/example files, six sections, {methods} annotated functions, API doc sections and exact-case manifest")
