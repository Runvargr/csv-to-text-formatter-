"""
Unit tests for csv_formatter.formatter.CSVFormatter.
"""

import textwrap
from pathlib import Path

import pandas as pd
import pytest

from csv_formatter import CSVFormatter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_CSV = textwrap.dedent("""\
    name,age,department,salary
    Alice,30,Engineering,95000
    Bob,25,Marketing,62000
    Carol,35,Engineering,110000
    David,28,Sales,58000
""")


@pytest.fixture()
def formatter():
    return CSVFormatter()


# ---------------------------------------------------------------------------
# format_string – basic rendering
# ---------------------------------------------------------------------------

class TestFormatString:
    def test_default_template_contains_values(self, formatter):
        output = formatter.format_string(SIMPLE_CSV)
        assert "Alice" in output
        assert "Engineering" in output
        assert "95000" in output

    def test_default_template_all_rows(self, formatter):
        output = formatter.format_string(SIMPLE_CSV)
        for name in ("Alice", "Bob", "Carol", "David"):
            assert name in output

    def test_table_template_header(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, "table.txt.j2")
        assert "name" in output
        assert "age" in output
        assert "salary" in output

    def test_table_template_separator(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, "table.txt.j2")
        assert "+" in output and "-" in output

    def test_report_template_statistics_section(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, "report.txt.j2")
        assert "SUMMARY STATISTICS" in output

    def test_report_template_record_section(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, "report.txt.j2")
        assert "RECORDS" in output
        assert "Alice" in output


# ---------------------------------------------------------------------------
# format_file
# ---------------------------------------------------------------------------

class TestFormatFile:
    def test_format_file(self, tmp_path, formatter):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text(SIMPLE_CSV, encoding="utf-8")
        output = formatter.format_file(csv_file)
        assert "Alice" in output
        assert "Bob" in output

    def test_nonexistent_file_raises(self, formatter):
        with pytest.raises(FileNotFoundError):
            formatter.format_file("/nonexistent/path/data.csv")


# ---------------------------------------------------------------------------
# column selection
# ---------------------------------------------------------------------------

class TestColumnSelection:
    def test_select_columns(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, columns=["name", "department"])
        assert "name" in output
        assert "department" in output
        # 'age' and 'salary' should not appear as headers
        assert "age:" not in output
        assert "salary:" not in output

    def test_missing_column_raises(self, formatter):
        with pytest.raises(ValueError, match="not found"):
            formatter.format_string(SIMPLE_CSV, columns=["name", "nonexistent"])


# ---------------------------------------------------------------------------
# filtering
# ---------------------------------------------------------------------------

class TestFilters:
    def test_filter_keeps_matching_rows(self, formatter):
        output = formatter.format_string(
            SIMPLE_CSV, filters={"department": "Engineering"}
        )
        assert "Alice" in output
        assert "Carol" in output
        assert "Bob" not in output
        assert "David" not in output

    def test_filter_no_match_produces_empty_records(self, formatter):
        output = formatter.format_string(
            SIMPLE_CSV, filters={"department": "Finance"}
        )
        assert "Total records: 0" in output

    def test_filter_unknown_column_raises(self, formatter):
        with pytest.raises(ValueError, match="Filter column not found"):
            formatter.format_string(SIMPLE_CSV, filters={"nonexistent": "x"})


# ---------------------------------------------------------------------------
# sorting
# ---------------------------------------------------------------------------

class TestSorting:
    def test_sort_ascending(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, sort_by="salary", ascending=True)
        idx_david = output.index("David")
        idx_carol = output.index("Carol")
        assert idx_david < idx_carol  # David (58000) appears before Carol (110000)

    def test_sort_descending(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, sort_by="salary", ascending=False)
        idx_carol = output.index("Carol")
        idx_david = output.index("David")
        assert idx_carol < idx_david  # Carol (110000) appears before David (58000)


# ---------------------------------------------------------------------------
# limit
# ---------------------------------------------------------------------------

class TestLimit:
    def test_limit_row_count(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, limit=2)
        assert "Total records: 2" in output

    def test_limit_zero(self, formatter):
        output = formatter.format_string(SIMPLE_CSV, limit=0)
        assert "Total records: 0" in output


# ---------------------------------------------------------------------------
# render_template_string
# ---------------------------------------------------------------------------

class TestRenderTemplateString:
    def test_inline_template(self, formatter):
        tmpl = "Count: {{ row_count }}\n{% for row in rows %}{{ row.name }}\n{% endfor %}"
        output = formatter.render_template_string(tmpl, csv_string=SIMPLE_CSV)
        assert "Count: 4" in output
        assert "Alice" in output

    def test_requires_exactly_one_source(self, formatter):
        with pytest.raises(ValueError):
            formatter.render_template_string("{{ row_count }}")

    def test_both_sources_raises(self, tmp_path, formatter):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text(SIMPLE_CSV)
        with pytest.raises(ValueError):
            formatter.render_template_string(
                "{{ row_count }}", csv_path=csv_file, csv_string=SIMPLE_CSV
            )


# ---------------------------------------------------------------------------
# extra_context
# ---------------------------------------------------------------------------

class TestExtraContext:
    def test_extra_context_is_available_in_template(self, formatter):
        tmpl = "Title: {{ title }}"
        output = formatter.render_template_string(
            tmpl, csv_string=SIMPLE_CSV, extra_context={"title": "My Report"}
        )
        assert "Title: My Report" in output


# ---------------------------------------------------------------------------
# custom template directory
# ---------------------------------------------------------------------------

class TestCustomTemplateDir:
    def test_custom_template_dir(self, tmp_path, formatter):
        custom_tmpl = tmp_path / "custom.txt.j2"
        custom_tmpl.write_text("rows={{ row_count }}", encoding="utf-8")
        f = CSVFormatter(template_dirs=[tmp_path])
        output = f.format_string(SIMPLE_CSV, "custom.txt.j2")
        assert "rows=4" in output


# ---------------------------------------------------------------------------
# Jinja2 filters
# ---------------------------------------------------------------------------

class TestFilters_Jinja2:
    def test_currency_filter(self, formatter):
        tmpl = "{% for row in rows %}{{ row.salary | currency }}{% endfor %}"
        output = formatter.render_template_string(tmpl, csv_string=SIMPLE_CSV)
        assert "$95,000.00" in output

    def test_floatfmt_filter(self, formatter):
        tmpl = "{% for row in rows %}{{ row.salary | floatfmt(0) }}{% endfor %}"
        output = formatter.render_template_string(tmpl, csv_string=SIMPLE_CSV)
        assert "95000" in output

    def test_ljust_filter(self, formatter):
        tmpl = "{{ 'hi' | ljust(10) }}"
        output = formatter.render_template_string(tmpl, csv_string=SIMPLE_CSV)
        assert output.startswith("hi")
        assert len(output.rstrip("\n")) >= 10
