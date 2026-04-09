"""
Example usage of the csv_formatter package.

Run from the project root:
    python examples/example_usage.py
"""

import sys
from pathlib import Path

# Allow running from the project root without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

from csv_formatter import CSVFormatter

CSV_FILE = Path(__file__).parent / "sample.csv"


def example_default():
    print("=" * 60)
    print("EXAMPLE 1 – Default (list) template")
    print("=" * 60)
    formatter = CSVFormatter()
    output = formatter.format_file(CSV_FILE, limit=3)
    print(output)


def example_table():
    print("=" * 60)
    print("EXAMPLE 2 – ASCII table template")
    print("=" * 60)
    formatter = CSVFormatter()
    output = formatter.format_file(CSV_FILE, "table.txt.j2", limit=5)
    print(output)


def example_report():
    print("=" * 60)
    print("EXAMPLE 3 – Structured report template")
    print("=" * 60)
    formatter = CSVFormatter()
    output = formatter.format_file(
        CSV_FILE,
        "report.txt.j2",
        filters={"department": "Engineering"},
        sort_by="salary",
        ascending=False,
        extra_context={"title": "Engineering Department Report"},
    )
    print(output)


def example_columns_and_sort():
    print("=" * 60)
    print("EXAMPLE 4 – Select columns, sort descending, limit rows")
    print("=" * 60)
    formatter = CSVFormatter()
    output = formatter.format_file(
        CSV_FILE,
        "table.txt.j2",
        columns=["name", "department", "salary"],
        sort_by="salary",
        ascending=False,
        limit=5,
    )
    print(output)


def example_inline_template():
    print("=" * 60)
    print("EXAMPLE 5 – Inline (string) template")
    print("=" * 60)
    formatter = CSVFormatter()
    template_src = (
        "Top {{ row_count }} employees by salary:\n"
        "{% for row in rows %}"
        "  {{ loop.index }}. {{ row.name }} — ${{ row.salary }}\n"
        "{% endfor %}"
    )
    output = formatter.render_template_string(
        template_src,
        csv_path=CSV_FILE,
        sort_by="salary",
        ascending=False,
        limit=3,
    )
    print(output)


if __name__ == "__main__":
    example_default()
    example_table()
    example_report()
    example_columns_and_sort()
    example_inline_template()
