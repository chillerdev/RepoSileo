#!/usr/bin/env python3
"""Build a static APT/Sileo repository using only Python's standard library.

Optional: install `zstandard` when a package uses control.tar.zst.
"""

from __future__ import annotations

import argparse
import bz2
import gzip
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import sys
import tarfile
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent
DEBS = ROOT / "debs"
CONFIG = ROOT / "repo.config.json"

# PowerShell 5 may expose a legacy console encoding; force deterministic UTF-8 logs.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def ar_members(path: Path) -> Iterator[tuple[str, bytes]]:
    with path.open("rb") as stream:
        if stream.read(8) != b"!<arch>\n":
            raise ValueError("không phải định dạng Debian/ar")
        while header := stream.read(60):
            if len(header) != 60 or header[58:60] != b"`\n":
                raise ValueError("ar header không hợp lệ")
            name = header[:16].decode("utf-8", "replace").strip().rstrip("/")
            size = int(header[48:58].decode("ascii").strip())
            data = stream.read(size)
            if size % 2:
                stream.read(1)
            yield name, data


def decompress_control(name: str, payload: bytes) -> bytes:
    if name.endswith(".gz"):
        return gzip.decompress(payload)
    if name.endswith(".xz"):
        return lzma.decompress(payload)
    if name.endswith(".bz2"):
        return bz2.decompress(payload)
    if name.endswith(".zst"):
        try:
            import zstandard  # type: ignore
        except ImportError as exc:
            raise RuntimeError("cần cài `pip install zstandard` để đọc control.tar.zst") from exc
        return zstandard.ZstdDecompressor().decompress(payload)
    return payload


def control_text(path: Path) -> str:
    for name, payload in ar_members(path):
        if name.startswith("control.tar"):
            raw = decompress_control(name, payload)
            with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as archive:
                for member in archive.getmembers():
                    if member.isfile() and Path(member.name).name == "control":
                        extracted = archive.extractfile(member)
                        if extracted:
                            return extracted.read().decode("utf-8", "replace").strip()
    raise ValueError("không tìm thấy control trong file deb")


def parse_control(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    key = ""
    for line in text.splitlines():
        if line[:1].isspace() and key:
            result[key] += "\n" + line
        elif ":" in line:
            key, value = line.split(":", 1)
            result[key] = value.strip()
    return result


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_release(config: dict, files: list[Path]) -> None:
    header = [
        f"Origin: {config['origin']}", f"Label: {config['label']}",
        f"Suite: {config['suite']}", f"Version: {config['version']}",
        f"Codename: {config['codename']}",
        "Architectures: " + " ".join(config["architectures"]),
        "Components: " + " ".join(config["components"]),
        f"Description: {config['description']}",
    ]
    for title, algorithm in (("MD5Sum", "md5"), ("SHA256", "sha256")):
        header.append(f"{title}:")
        for path in files:
            header.append(f" {digest(path, algorithm)} {path.stat().st_size} {path.name}")
    (ROOT / "Release").write_text("\n".join(header) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cập nhật metadata cho Sileo repo")
    parser.add_argument("--check", action="store_true", help="thoát lỗi nếu có deb không đọc được")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    DEBS.mkdir(exist_ok=True)
    stanzas: list[str] = []
    website: list[dict[str, str]] = []
    errors = 0

    for deb in sorted(DEBS.glob("*.deb"), key=lambda p: p.name.lower()):
        try:
            text = control_text(deb)
            fields = parse_control(text)
            if not all(fields.get(key) for key in ("Package", "Version", "Architecture")):
                raise ValueError("control thiếu Package, Version hoặc Architecture")
            extra = [
                f"Filename: ./debs/{deb.name}", f"Size: {deb.stat().st_size}",
                f"MD5sum: {digest(deb, 'md5')}", f"SHA256: {digest(deb, 'sha256')}",
            ]
            stanzas.append(text.rstrip() + "\n" + "\n".join(extra))
            website.append({key: fields.get(key, "") for key in (
                "Package", "Name", "Version", "Architecture", "Description",
                "Section", "Author", "Maintainer", "Icon", "Depiction", "Homepage")})
            print(f"OK   {deb.name} ({fields['Package']} {fields['Version']})")
        except Exception as exc:
            errors += 1
            print(f"LOI  {deb.name}: {exc}")

    packages = ("\n\n".join(stanzas) + ("\n\n" if stanzas else "")).encode("utf-8")
    (ROOT / "Packages").write_bytes(packages)
    (ROOT / "Packages.gz").write_bytes(gzip.compress(packages, compresslevel=9, mtime=0))
    (ROOT / "Packages.bz2").write_bytes(bz2.compress(packages, compresslevel=9))
    payload = {"repo": config, "packages": website}
    (ROOT / "packages.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_release(config, [ROOT / "Packages", ROOT / "Packages.bz2", ROOT / "Packages.gz"])
    print(f"\nĐã tạo repo với {len(website)} gói; {errors} lỗi.")
    return 1 if args.check and errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
