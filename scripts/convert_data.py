import os
import json
import re
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional


def parse_sql_file(file_path: str, tables: List[str]) -> List[Dict[str, Any]]:
    """Parse SQL dump file and extract specific tables."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    results = []
    current_table = None
    current_data = []
    in_insert = False

    lines = content.split("\n")

    for line in lines:
        line = line.strip()

        if line.upper().startswith("CREATE TABLE"):
            match = re.search(r"`?(\w+)`?", line)
            if match:
                current_table = match.group(1)
                current_data = []
                in_insert = False

        elif line.upper().startswith("INSERT INTO"):
            match = re.search(r"`?(\w+)`?", line)
            if match:
                current_table = match.group(1)
                in_insert = True
                if current_table in tables:
                    values_match = re.search(r"VALUES\s*(.*)", line, re.DOTALL)
                    if values_match:
                        current_data.append(values_match.group(1))

        elif in_insert and current_table in tables:
            if line.startswith("(") and line.endswith(")"):
                current_data.append(line)
            elif line.endswith(";"):
                in_insert = False
            elif line:
                current_data.append(line)

    for table in tables:
        if table in results:
            continue
        results.append({"table": table, "status": "extracted"})

    return results


def parse_sql_simple(file_path: str, tables: List[str]) -> List[Dict[str, Any]]:
    """Simple SQL parser - extracts table data from INSERT statements."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    results = []
    table_data = {table: [] for table in tables}

    insert_pattern = r"INSERT INTO\s+`?(\w+)`?\s*\(.*?\)\s*VALUES\s*(.*?);"
    matches = re.findall(insert_pattern, content, re.DOTALL | re.IGNORECASE)

    for table_name, values in matches:
        if table_name in tables:
            value_pattern = r"\((.*?)\)"
            value_matches = re.findall(value_pattern, values)
            for i, vm in enumerate(value_matches):
                table_data[table_name].append(
                    {"text": vm, "metadata": {"table": table_name, "row": i}}
                )

    for table in tables:
        for item in table_data[table]:
            results.append(item)

    return results


def load_json_file(
    file_path: str, text_field: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load JSON file and convert to RAG format."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    if isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                if text_field and text_field in item:
                    text = item[text_field]
                elif "text" in item:
                    text = item["text"]
                elif "content" in item:
                    text = item["content"]
                else:
                    text = json.dumps(item)

                metadata = {
                    k: v for k, v in item.items() if k not in ["text", "content"]
                }
                metadata["row"] = i

                results.append({"text": text, "metadata": metadata})
    elif isinstance(data, dict):
        for key, value in data.items():
            results.append(
                {
                    "text": f"{key}: {value}"
                    if not isinstance(value, dict)
                    else json.dumps(value),
                    "metadata": {"key": key, "type": type(value).__name__},
                }
            )

    return results


def load_excel_file(
    file_path: str, sheet_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load Excel file and convert to RAG format."""
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    results = []

    for i, row in df.iterrows():
        text_parts = []
        metadata = {"row": i}

        for col, val in row.items():
            if pd.notna(val):
                text_parts.append(f"{col}: {val}")
                if col != "text" and col != "content":
                    metadata[col] = val

        results.append({"text": ". ".join(text_parts), "metadata": metadata})

    return results


def convert_data(
    input_path: str,
    output_path: str,
    input_format: str,
    tables: Optional[List[str]] = None,
    text_field: Optional[str] = None,
):
    """Main conversion function."""
    print(f"Converting {input_path}...")

    if input_format == "sql":
        if not tables:
            print("Warning: No tables specified for SQL file")
            return []
        results = parse_sql_simple(input_path, tables)
    elif input_format == "json":
        results = load_json_file(input_path, text_field)
    elif input_format in ["xlsx", "xls"]:
        results = load_excel_file(input_path)
    else:
        raise ValueError(f"Unsupported format: {input_format}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Converted {len(results)} records to {output_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Convert data to RAG format")
    parser.add_argument("input", help="Input file path")
    parser.add_argument(
        "-o", "--output", default="./data/extracted_data.json", help="Output file"
    )
    parser.add_argument(
        "-f", "--format", choices=["sql", "json", "xlsx", "xls"], required=True
    )
    parser.add_argument("-t", "--tables", nargs="+", help="Tables to extract from SQL")
    parser.add_argument("--text-field", help="JSON field to use as text")

    args = parser.parse_args()

    convert_data(args.input, args.output, args.format, args.tables, args.text_field)


if __name__ == "__main__":
    main()
