"""Copy the monorepo RAG index into backend/data so the Vercel function can read it."""

from __future__ import annotations

import shutil
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
SRC = REPO / "data"
DST = BACKEND / "data"


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"copied {src.relative_to(REPO)} -> {dst.relative_to(BACKEND)}")


def main() -> None:
    index = SRC / "index"
    if not (index / "chunks.jsonl").exists():
        raise SystemExit(f"missing index at {index}")
    if DST.exists() and DST.resolve() != SRC.resolve():
        shutil.rmtree(DST)
    shutil.copytree(index, DST / "index")
    print(f"copied index -> {DST / 'index'}")
    seed = SRC / "contradictions.seed.json"
    if seed.exists():
        _copy_file(seed, DST / "contradictions.seed.json")
    manifest = SRC / "corpus" / "manifest.yaml"
    if manifest.exists():
        _copy_file(manifest, DST / "corpus" / "manifest.yaml")


if __name__ == "__main__":
    main()
