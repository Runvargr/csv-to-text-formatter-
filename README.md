# csv-to-text-formatter

A Python library and CLI tool that converts CSV data into human-readable text using
[pandas](https://pandas.pydata.org/) for data processing and
[Jinja2](https://jinja.palletsprojects.com/) for flexible templating.

---

## Features

- **Three built-in templates** — list, ASCII table, and structured report
- **Custom templates** — supply your own Jinja2 `.j2` files
- **Filtering** — keep only rows where a column matches a value
- **Column selection** — include only the columns you care about
- **Sorting** — sort ascending or descending by any column
- **Row limit** — cap output at N rows
- **Summary statistics** — per-column min/max/mean/unique/missing counts
- **Custom Jinja2 filters** — `currency`, `floatfmt`, `ljust`, `rjust`, `center`
- **Python API and CLI** — use as a library or from the command line

---

## Installation

```bash
pip install -r requirements.txt
pip install -e .          # installs the csv-formatter CLI entry point
```

Requires Python ≥ 3.7.

---

## Quick Start

### CLI

```bash
# Default list format
csv-formatter data.csv

# ASCII table
csv-formatter data.csv --template table.txt.j2

# Structured report
csv-formatter data.csv --template report.txt.j2

# Filter, sort, limit
csv-formatter data.csv \
    --filter department=Engineering \
    --sort-by salary --desc \
    --limit 5

# Select specific columns and write to file
csv-formatter data.csv \
    --columns name,salary \
    --output report.txt

# Use a custom template from a local directory
csv-formatter data.csv \
    --template-dir ./my_templates \
    --template custom.txt.j2
```

Run `csv-formatter --help` for a full list of options.

### Python API

```python
from csv_formatter import CSVFormatter

formatter = CSVFormatter()

# From a file
output = formatter.format_file("data.csv", "table.txt.j2")
print(output)

# From a string
csv_text = "name,age\nAlice,30\nBob,25\n"
output = formatter.format_string(csv_text, "report.txt.j2")

# With filtering, sorting, and column selection
output = formatter.format_file(
    "data.csv",
    "table.txt.j2",
    columns=["name", "department", "salary"],
    filters={"department": "Engineering"},
    sort_by="salary",
    ascending=False,
    limit=10,
    extra_context={"title": "Engineering Team"},
)

# Inline template string
tmpl = "Top earners:\n{% for row in rows %}  {{ row.name }} — ${{ row.salary }}\n{% endfor %}"
output = formatter.render_template_string(tmpl, csv_path="data.csv",
                                          sort_by="salary", ascending=False, limit=3)
```

---

## Built-in Templates

| Template | Description |
|---|---|
| `default.txt.j2` | Simple key-value list, one record per block |
| `table.txt.j2` | Plain-text ASCII table with auto-sized columns |
| `report.txt.j2` | Structured report with records and summary statistics |

### Example output — `table.txt.j2`

```
+---------------+-----+-------------+--------+
|      name     | age |  department | salary |
+---------------+-----+-------------+--------+
| Carol White   | 35  | Engineering | 110000 |
| Eve Davis     | 32  | Engineering | 98000  |
| Alice Johnson | 30  | Engineering | 95000  |
+---------------+-----+-------------+--------+
Total rows: 3
```

### Example output — `report.txt.j2`

```
============================================================
               Engineering Department Report
============================================================

Total records: 3
Columns: name, age, department, salary, city

------------------------------------------------------------
RECORDS
------------------------------------------------------------
Record #1
  name:                Carol White
  age:                 35
  ...

============================================================
SUMMARY STATISTICS
============================================================
Column: salary
  Unique values : 3
  Missing values: 0
  Min           : 92000
  Max           : 110000
  Mean          : 98750.0
```

---

## Custom Templates

Place a Jinja2 template file (`.j2`) anywhere and pass its directory with
`--template-dir` (CLI) or the `template_dirs` constructor argument (API).

### Available template context variables

| Variable | Type | Description |
|---|---|---|
| `columns` | `list[str]` | Column names in display order |
| `rows` | `list[dict]` | One dict per row, keyed by column name |
| `row_count` | `int` | Number of rows after filtering/limiting |
| `col_widths` | `dict[str, int]` | Display width of each column |
| `summary` | `dict` | Per-column stats: `min`, `max`, `mean`, `unique`, `missing` |

Any key passed via `extra_context` (API) is also available in the template.

### Custom Jinja2 filters

| Filter | Signature | Example |
|---|---|---|
| `currency` | `value \| currency(symbol="$", decimals=2)` | `95000 \| currency` → `$95,000.00` |
| `floatfmt` | `value \| floatfmt(decimals=2)` | `3.14159 \| floatfmt(3)` → `3.142` |
| `ljust` | `value \| ljust(width)` | `"hi" \| ljust(10)` → `"hi        "` |
| `rjust` | `value \| rjust(width)` | `"hi" \| rjust(10)` → `"        hi"` |
| `center` | `value \| center(width)` | `"hi" \| center(10)` → `"    hi    "` |

---

## Project Layout

```
csv-to-text-formatter-/
├── csv_formatter/
│   ├── __init__.py        # Package exports
│   ├── formatter.py       # CSVFormatter class (pandas + Jinja2)
│   ├── cli.py             # Click-based CLI
│   └── templates/
│       ├── default.txt.j2
│       ├── table.txt.j2
│       └── report.txt.j2
├── examples/
│   ├── sample.csv         # Sample dataset
│   └── example_usage.py   # Runnable usage examples
├── tests/
│   ├── test_formatter.py  # Unit tests for CSVFormatter
│   └── test_cli.py        # Unit tests for the CLI
├── setup.py
├── requirements.txt
└── README.md
```

---

## Running the Examples

```bash
python examples/example_usage.py
```

---

## Running the Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## License

[MIT](LICENSE)
