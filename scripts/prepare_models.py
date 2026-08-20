from __future__ import annotations

import os
import shutil
from pathlib import Path


MODELS = (
    ("detection", "PP-OCRv5_mobile_det"),
    ("recognition", "PP-OCRv5_mobile_rec"),
    ("recognition", "korean_PP-OCRv5_mobile_rec"),
)
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "models"


def find_cached_model(name: str) -> Path:
    search_roots = [
        Path.home() / ".paddlex",
        Path.home() / ".cache" / "paddlex",
        Path.home() / ".cache" / "paddle",
    ]
    matches: list[Path] = []
    for root in search_roots:
        if root.exists():
            matches.extend(path for path in root.rglob(name) if path.is_dir())
    usable = [path for path in matches if any(path.rglob("*.json"))]
    if not usable:
        raise FileNotFoundError(f"找不到已下载模型：{name}")
    return max(usable, key=lambda path: sum(item.stat().st_size for item in path.rglob("*") if item.is_file()))


def main() -> int:
    os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "BOS")
    from paddleocr import TextDetection, TextRecognition

    OUTPUT.mkdir(exist_ok=True)
    for kind, name in MODELS:
        print(f"Preparing {name}...")
        constructor = TextDetection if kind == "detection" else TextRecognition
        constructor(model_name=name, device="cpu", engine="paddle_static")
        source = find_cached_model(name)
        target = OUTPUT / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
        print(f"  {source} -> {target}")
    print("Offline models are ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

