import pyarrow.orc as orc
import os
import yaml
import pandas as pd


def safe_convert(value):
    """Convert complex types (like Timestamps, Decimals) into strings for YAML output."""
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    elif isinstance(value, (bytes, bytearray)):
        return value.decode(errors="replace")
    elif isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    else:
        return str(value)


def convert_orc_to_yaml(input_path: str, output_path: str | None = None) -> str:
    """
    Convert an ORC file to a YAML file.

    Args:
        input_path (str): Path to the input ORC file.
        output_path (str, optional): Path to the output YAML file. Defaults to same name as input with `.yaml`.

    Returns:
        str: Path to the generated YAML file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        RuntimeError: If reading or writing fails.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        table = orc.read_table(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read ORC file: {e}")

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

        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                safe_records,
                f,
                sort_keys=True,
                allow_unicode=True,
                default_flow_style=False,
                width=120,
            )

    except Exception as e:
        raise RuntimeError(f"Failed to write YAML: {e}")

    return output_path
