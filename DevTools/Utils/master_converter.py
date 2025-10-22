#!/usr/bin/env python3
"""
Utils/master_converter.py

Master Converter
- Core: JSON, YAML, CSV, XML
- Optional: TOML (if tomli/tomli_w available)
"""

from __future__ import annotations
import os, sys, csv, json, io
import xml.etree.ElementTree as ET
from typing import Any, List, Dict, Optional
from datetime import datetime

# Optional YAML
try:
    import yaml
    HAVE_YAML = True
except Exception:
    yaml = None
    HAVE_YAML = False

# Optional TOML
try:
    import tomllib
    HAVE_TOMLLIB = True
except Exception:
    tomllib = None
    HAVE_TOMLLIB = False

if not HAVE_TOMLLIB:
    try:
        import tomli as tomllib
        HAVE_TOMLLIB = True
    except Exception:
        pass

try:
    import tomli_w
    HAVE_TOMLI_W = True
except Exception:
    tomli_w = None
    HAVE_TOMLI_W = False


# UI imports
try:
    from Utils.UIUtils import UiUtils, ColorUi
    from Utils.path_selector import select_path
except Exception:
    class ColorUi:
        @staticmethod
        def colorize(text, color="White", bold=False, italic=False, underline=False):
            return text
        @staticmethod
        def print_multi(*segments, end="\n"):
            parts = [seg[0] for seg in segments if seg]
            print("".join(parts), end=end)
    class UiUtils:
        @staticmethod
        def clear_screen():
            os.system("cls" if os.name == "nt" else "clear")
    def select_path(verbose=False): return input("Path: ").strip()


# ----------------------------
# Supported formats
# ----------------------------
CORE_FORMATS = ("json", "yaml", "yml", "csv", "xml")
OPTIONAL_WRITE_FORMATS = ("toml",)
OPTIONAL_READ_FORMATS = ("toml",)

def _norm_ext(path: str) -> str:
    return os.path.splitext(path)[1].lower().lstrip(".")


def detect_format(path: str, peek_bytes: int = 2048) -> str:
    ext = _norm_ext(path)
    if ext in CORE_FORMATS or ext in OPTIONAL_READ_FORMATS:
        return "yaml" if ext == "yml" else ext
    try:
        with open(path, "rb") as fh:
            head = fh.read(peek_bytes).strip()
            if head.startswith(b"{") or head.startswith(b"["):
                return "json"
            if b"<?xml" in head or b"<" in head:
                return "xml"
            if b"---" in head or b": " in head:
                return "yaml"
    except Exception:
        pass
    raise ValueError(f"Could not detect format for '{path}'.")


# ----------------------------
# Loaders
# ----------------------------
def load_json(path: str): 
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_yaml(path: str):
    if not HAVE_YAML:
        raise RuntimeError("PyYAML is not installed. Run `pip install pyyaml`.")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_csv(path: str):
    with open(path, "r", encoding="utf-8", newline="") as f:
        sample = f.read(2048)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            dialect = csv.excel
        has_header = csv.Sniffer().has_header(sample)
        reader = csv.reader(f, dialect)
        rows = list(reader)
    if not rows:
        return []
    if has_header:
        header, data_rows = rows[0], rows[1:]
        return [{header[i]: r[i] if i < len(r) else None for i in range(len(header))} for r in data_rows]
    return rows

def load_toml(path: str):
    if not HAVE_TOMLLIB:
        raise RuntimeError("TOML reader unavailable. Install `tomli` or use Python 3.11+.")
    with open(path, "rb") as f:
        return tomllib.load(f)

def _xml_to_dict(elem: ET.Element) -> Any:
    """Convert XML ElementTree to dict."""
    d = {}
    if elem.attrib:
        d["@attributes"] = elem.attrib
    children = list(elem)
    if children:
        child_dict = {}
        for child in children:
            cd = _xml_to_dict(child)
            if child.tag in child_dict:
                if not isinstance(child_dict[child.tag], list):
                    child_dict[child.tag] = [child_dict[child.tag]]
                child_dict[child.tag].append(cd[child.tag])
            else:
                child_dict.update(cd)
        d[elem.tag] = child_dict
    else:
        d[elem.tag] = elem.text.strip() if elem.text else ""
    return d

def load_xml(path: str):
    tree = ET.parse(path)
    root = tree.getroot()
    return _xml_to_dict(root)


def load_data(path: str, fmt: Optional[str] = None):
    fmt = fmt or detect_format(path)
    if fmt == "json": return load_json(path)
    if fmt in ("yaml", "yml"): return load_yaml(path)
    if fmt == "csv": return load_csv(path)
    if fmt == "xml": return load_xml(path)
    if fmt == "toml": return load_toml(path)
    raise ValueError(f"Unsupported format: {fmt}")


# ----------------------------
# Dumpers
# ----------------------------
def dump_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path

def dump_yaml(data, path):
    if not HAVE_YAML:
        raise RuntimeError("PyYAML not installed.")
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    return path

def dump_toml(data, path):
    if not HAVE_TOMLI_W:
        raise RuntimeError("tomli_w not installed.")
    with open(path, "wb") as f:
        f.write(tomli_w.dumps(data).encode("utf-8"))
    return path

def dump_csv(data, path):
    from io import StringIO
    headers = []
    if isinstance(data, list) and all(isinstance(d, dict) for d in data):
        headers = sorted({k for row in data for k in row.keys()})
    elif isinstance(data, dict):
        data = [data]
        headers = sorted(data[0].keys())
    else:
        raise ValueError("CSV export supports list[dict] or dict.")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    return path


def _dict_to_xml(data: Any, root_name="root") -> ET.Element:
    """Convert dict/list into XML ElementTree."""
    def build_elem(parent, val):
        if isinstance(val, dict):
            for k, v in val.items():
                if k == "@attributes":
                    for a, av in v.items():
                        parent.set(a, str(av))
                else:
                    child = ET.SubElement(parent, k)
                    build_elem(child, v)
        elif isinstance(val, list):
            for item in val:
                child = ET.SubElement(parent, "item")
                build_elem(child, item)
        else:
            parent.text = str(val)

    root = ET.Element(root_name)
    build_elem(root, data)
    return root

def dump_xml(data: Any, path: str):
    root_name = "root"
    if isinstance(data, dict) and len(data) == 1:
        root_name = next(iter(data.keys()))
        data = data[root_name]
    root = _dict_to_xml(data, root_name)
    ET.indent(root, space="  ", level=0)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


def dump_data(data, path, fmt):
    fmt = "yaml" if fmt == "yml" else fmt
    if fmt == "json": return dump_json(data, path)
    if fmt == "yaml": return dump_yaml(data, path)
    if fmt == "csv": return dump_csv(data, path)
    if fmt == "xml": return dump_xml(data, path)
    if fmt == "toml": return dump_toml(data, path)
    raise ValueError(f"Unsupported format: {fmt}")


# ----------------------------
# Conversion API
# ----------------------------
def _default_output_path(input_path, to_fmt, base_dir=None):
    stem = os.path.splitext(os.path.basename(input_path))[0]
    outname = f"{stem}.{to_fmt}"
    if base_dir:
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, outname)
    return os.path.join(os.path.dirname(input_path), outname)

def convert_file(input_path, to_fmt, output_path=None, base_dir=None):
    to_fmt = to_fmt.lower()
    from_fmt = detect_format(input_path)
    data = load_data(input_path, from_fmt)
    out_path = output_path or _default_output_path(input_path, to_fmt, base_dir)
    return dump_data(data, out_path, to_fmt)


# ----------------------------
# Interactive Runner
# ----------------------------
def run_master_converter_interactive(default_outdir=None):
    UiUtils.clear_screen()
    ColorUi.print_multi(("Master Converter", getattr(ColorUi, "NeonPurple", None), True))
    ColorUi.print_multi(("Supported: JSON, YAML, CSV, XML", getattr(ColorUi, "Grey", None)))
    if HAVE_TOMLLIB: ColorUi.print_multi(("TOML (read)", getattr(ColorUi, "Grey", None)))
    if HAVE_TOMLI_W: ColorUi.print_multi(("TOML (write)", getattr(ColorUi, "Grey", None)))
    print()

    ColorUi.print_multi(("Select input file:", getattr(ColorUi, "BrightYellow", None), True))
    input_path = select_path(verbose=True)
    if not os.path.exists(input_path):
        ColorUi.print_multi((f"❌ Path not found: {input_path}", getattr(ColorUi, "BrightRed", None), True))
        input(ColorUi.colorize("\nPress Enter to return...", getattr(ColorUi, "BrightBlack", None)))
        return

    targets = ["json", "yaml", "csv", "xml"]
    if HAVE_TOMLI_W: targets.append("toml")

    ColorUi.print_multi(("Select target format:", getattr(ColorUi, "BrightYellow", None), True))
    for i, f in enumerate(targets, 1):
        ColorUi.print_multi((f"{i}. {f.upper()}", getattr(ColorUi, "Violet", None)))
    try:
        sel = int(input(ColorUi.colorize("Choice: ", getattr(ColorUi, "BrightWhite", None), bold=True)).strip())
        to_fmt = targets[sel - 1]
    except Exception:
        ColorUi.print_multi(("❌ Invalid choice", getattr(ColorUi, "BrightRed", None), True))
        input(ColorUi.colorize("\nPress Enter...", getattr(ColorUi, "BrightBlack", None)))
        return

    try:
        spinner = UiUtils.spinner("Converting", color="BrightGreen", interval=0.1)
        out_path = convert_file(input_path, to_fmt, base_dir=default_outdir)
        spinner()
        ColorUi.print_multi((f"\n✅ Converted → {out_path}", getattr(ColorUi, "BrightGreen", None), True))
    except Exception as e:
        if spinner: spinner()
        ColorUi.print_multi((f"\n❌ Conversion failed: {e}", getattr(ColorUi, "BrightRed", None), True))
    input(ColorUi.colorize("\nPress Enter to return...", getattr(ColorUi, "BrightBlack", None)))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Master Converter (JSON/YAML/CSV/XML/TOML)")
    p.add_argument("input", nargs="?", help="Input file path.")
    p.add_argument("-t", "--to", dest="to_fmt", help="Target format.")
    p.add_argument("--outdir", dest="outdir", help="Output directory.")
    p.add_argument("-i", "--interactive", action="store_true")
    args = p.parse_args()

    if args.interactive or not args.input:
        run_master_converter_interactive(default_outdir=args.outdir)
        sys.exit(0)

    out = convert_file(args.input, args.to_fmt, base_dir=args.outdir)
    print(f"✅ Converted → {out}")
