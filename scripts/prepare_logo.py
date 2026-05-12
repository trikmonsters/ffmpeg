#!/usr/bin/env python3
"""
prepare_logo.py
Resize logo image dan atur opacity sebelum di-overlay ke video.
Mendukung PNG (dengan transparansi) dan JPG (akan dikonversi ke PNG).
"""

import argparse
import sys
from PIL import Image


def prepare_logo(input_path: str, output_path: str, width: int, opacity: float):
    print(f"🖼️  Input  : {input_path}")
    print(f"📐 Width  : {width}px")
    print(f"🔆 Opacity: {opacity}")

    img = Image.open(input_path)

    # Konversi ke RGBA agar bisa handle transparansi & opacity
    img = img.convert("RGBA")

    # Resize proporsional berdasarkan lebar
    original_w, original_h = img.size
    ratio = width / original_w
    new_h = int(original_h * ratio)
    img = img.resize((width, new_h), Image.LANCZOS)

    print(f"📏 Resized: {original_w}x{original_h} → {width}x{new_h}")

    # Terapkan opacity ke channel alpha
    if opacity < 1.0:
        r, g, b, a = img.split()
        a = a.point(lambda px: int(px * opacity))
        img = Image.merge("RGBA", (r, g, b, a))
        print(f"✅ Opacity {opacity} applied")

    img.save(output_path, "PNG")
    print(f"💾 Saved  : {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Prepare logo untuk overlay video")
    parser.add_argument("--input",   required=True,          help="Path logo input")
    parser.add_argument("--output",  required=True,          help="Path logo output (PNG)")
    parser.add_argument("--width",   type=int, default=200,  help="Lebar logo dalam pixel")
    parser.add_argument("--opacity", type=float, default=0.9, help="Opacity 0.0-1.0")
    args = parser.parse_args()

    if not (0.0 <= args.opacity <= 1.0):
        print("❌ Opacity harus antara 0.0 dan 1.0")
        sys.exit(1)

    if args.width < 10 or args.width > 2000:
        print("❌ Width harus antara 10 dan 2000 pixel")
        sys.exit(1)

    prepare_logo(args.input, args.output, args.width, args.opacity)


if __name__ == "__main__":
    main()
