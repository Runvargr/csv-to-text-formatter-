"""
Unit tests for csv_formatter.cli (Click CLI).
"""

import textwrap

import pytest
from click.testing import CliRunner

from csv_formatter.cli import main

SIMPLE_CSV = textwrap.dedent("""\
    name,age,department,salary
    Alice,30,Engineering,95000
    Bob,25,Marketing,62000
    Carol,35,Engineering,110000
    David,28,Sales,58000
""")


@pytest.fixture()
def csv_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text(SIMPLE_CSV, encoding="utf-8")
    return str(p)


@pytest.fixture()
def runner():
    return CliRunner()


class TestCLIBasic:
    def test_default_output(self, runner, csv_file):
        result = runner.invoke(main, [csv_file])
        assert result.exit_code == 0, result.output
        assert "Alice" in result.output

    def test_table_template(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--template", "table.txt.j2"])
        assert result.exit_code == 0, result.output
        assert "name" in result.output
        assert "+" in result.output

    def test_report_template(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--template", "report.txt.j2"])
        assert result.exit_code == 0, result.output
        assert "SUMMARY STATISTICS" in result.output

    def test_missing_file_returns_error(self, runner):
        result = runner.invoke(main, ["/nonexistent/file.csv"])
        assert result.exit_code != 0


class TestCLIOptions:
    def test_columns_option(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--columns", "name,department"])
        assert result.exit_code == 0, result.output
        assert "department:" in result.output
        assert "salary:" not in result.output

    def test_filter_option(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--filter", "department=Engineering"])
        assert result.exit_code == 0, result.output
        assert "Alice" in result.output
        assert "Bob" not in result.output

    def test_sort_by_option(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--sort-by", "salary"])
        assert result.exit_code == 0, result.output
        # David (58000) should appear before Carol (110000) in ascending order
        assert result.output.index("David") < result.output.index("Carol")

    def test_sort_desc_option(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--sort-by", "salary", "--desc"])
        assert result.exit_code == 0, result.output
        assert result.output.index("Carol") < result.output.index("David")

    def test_limit_option(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--limit", "2"])
        assert result.exit_code == 0, result.output
        assert "Total records: 2" in result.output

    def test_output_file(self, runner, csv_file, tmp_path):
        out_file = str(tmp_path / "out.txt")
        result = runner.invoke(main, [csv_file, "--output", out_file])
        assert result.exit_code == 0, result.output
        assert "Output written to" in result.output
        from pathlib import Path
        content = Path(out_file).read_text(encoding="utf-8")
        assert "Alice" in content

    def test_invalid_filter_format(self, runner, csv_file):
        result = runner.invoke(main, [csv_file, "--filter", "bad_filter_no_equals"])
        assert result.exit_code != 0

    def test_help_option(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.output

    def test_custom_template_dir(self, runner, csv_file, tmp_path):
        custom_tmpl = tmp_path / "mine.txt.j2"
        custom_tmpl.write_text("count={{ row_count }}", encoding="utf-8")
        result = runner.invoke(
            main,
            [
                csv_file,
                "--template-dir",
                str(tmp_path),
                "--template",
                "mine.txt.j2",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "count=4" in result.output
