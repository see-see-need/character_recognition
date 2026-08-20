from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

project_root = Path(SPECPATH)
datas = []
hiddenimports = []
binaries = []
for package in ("paddleocr", "paddlex", "paddle"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

# PaddleX validates these distributions through importlib.metadata before it
# creates an OCR predictor. PyInstaller can bundle their modules without the
# corresponding dist-info directories, which makes the packaged application
# report a misleading dependency error at runtime.
metadata_distributions = (
    "PyYAML",
    "aistudio-sdk",
    "chardet",
    "colorlog",
    "filelock",
    "huggingface-hub",
    "imagesize",
    "modelscope",
    "numpy",
    "opencv-contrib-python",
    "packaging",
    "pandas",
    "pillow",
    "prettytable",
    "py-cpuinfo",
    "pyclipper",
    "pydantic",
    "pypdfium2",
    "python-bidi",
    "requests",
    "ruamel.yaml",
    "shapely",
    "typing-extensions",
    "ujson",
)
for distribution in metadata_distributions:
    datas += copy_metadata(distribution)
models = project_root / "models"
if models.exists():
    datas.append((str(models), "models"))

a = Analysis(
    [str(project_root / "src" / "screen_ocr" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ScreenOCR",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="ScreenOCR",
)
