#!/usr/bin/env python3
import pyarrow.orc as orc
import argparse
import os
import sys
import yaml
import pandas as pd

def safe_convert(value):
    """Convert complex types (like Timestamps, Decimals) into strings for YAML output."""
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    elif isinstance(value, (bytes, bytearray)):
        return value.decode(errors="replace")
    elif isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    else:
        return str(value)

def convert_orc_to_yaml(input_path, output_path=None):
    """Reads an ORC file and writes it as a YAML file."""
    if not os.path.exists(input_path):
        print(f"❌ Error: File not found: {input_path}")
        sys.exit(1)

    try:
        print(f"📥 Reading ORC file: {input_path}")
        table = orc.read_table(input_path)
        print(f"✅ Successfully read ORC file with {table.num_rows} rows and {table.num_columns} columns.")
    except Exception as e:
        print(f"❌ Failed to read ORC file: {e}")
        sys.exit(1)

    if not output_path:
        output_path = os.path.splitext(input_path)[0] + ".yaml"

    try:
        df = table.to_pandas()
        records = df.to_dict(orient="records")

        # Safely convert all values
        safe_records = [
            {k: safe_convert(v) for k, v in record.items()}
            for record in records
        ]

        print(f"💾 Writing to YAML: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                safe_records,
                f,
                sort_keys=True,
                allow_unicode=True,
                default_flow_style=False,
                width=120,
            )
        print(f"🎉 Conversion complete: {output_path}")
    except Exception as e:
        print(f"❌ Failed to write YAML: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Convert ORC file to readable YAML using PyArrow.")
    parser.add_argument("input", help="Path to the input ORC file.")
    parser.add_argument("-o", "--output", help="Optional path for the output YAML file.")
    args = parser.parse_args()

    convert_orc_to_yaml(args.input, args.output)

if __name__ == "__main__":
    main()
