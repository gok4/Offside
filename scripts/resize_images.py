#!/usr/bin/env python3
"""
resize_images.py

Batch-resizes images to a target width (preserving aspect ratio) and
converts them to WebP with transparency preserved, at much smaller
file sizes than the original PNGs.

Usage:
    python3 resize_images.py <input_dir> <output_dir> [--width 600] [--quality 80]

Walks the input directory recursively, mirrors the folder structure in
the output directory, and converts every .png/.jpg/.jpeg it finds to
.webp.
"""

import sys
import argparse
from pathlib import Path
from PIL import Image


def resize_and_convert(src_path: Path, dst_path: Path, target_width: int, quality: int):
    with Image.open(src_path) as im:
        # Preserve transparency: convert to RGBA if it has an alpha channel
        # or is in a mode that supports one; otherwise keep as RGB.
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
        else:
            im = im.convert("RGB")

        w, h = im.size
        if w > target_width:
            new_h = round(h * (target_width / w))
            im = im.resize((target_width, new_h), Image.LANCZOS)

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst_path, "WEBP", quality=quality, method=6)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument("--width", type=int, default=600)
    parser.add_argument("--quality", type=int, default=80)
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)

    if not in_dir.is_dir():
        print(f"Input directory not found: {in_dir}")
        sys.exit(1)

    exts = {".png", ".jpg", ".jpeg"}
    files = [p for p in in_dir.rglob("*") if p.suffix.lower() in exts]

    if not files:
        print(f"No images found under {in_dir}")
        sys.exit(1)

    total_before = 0
    total_after = 0

    for src in files:
        rel = src.relative_to(in_dir)
        dst = out_dir / rel.with_suffix(".webp")
        before = src.stat().st_size
        resize_and_convert(src, dst, args.width, args.quality)
        after = dst.stat().st_size
        total_before += before
        total_after += after
        print(f"{rel} : {before/1024:.0f}KB -> {after/1024:.0f}KB")

    print(f"\n{len(files)} images processed")
    print(f"Total: {total_before/1024/1024:.1f}MB -> {total_after/1024/1024:.1f}MB "
          f"({100 * total_after / total_before:.1f}% of original)")


if __name__ == "__main__":
    main()
