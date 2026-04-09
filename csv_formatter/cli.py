"""
CLI interface for csv-formatter.

Usage examples
--------------
  csv-formatter data.csv
  csv-formatter data.csv --template table.txt.j2
  csv-formatter data.csv --template report.txt.j2 --sort-by salary --desc
  csv-formatter data.csv --columns name,age --limit 10
  csv-formatter data.csv --filter department=Engineering
  csv-formatter data.csv --output report.txt
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional

import click

from .formatter import CSVFormatter


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("csv_file", type=click.Path(exists=True, readable=True, dir_okay=False))
@click.option(
    "-t",
    "--template",
    default="default.txt.j2",
    show_default=True,
    help="Jinja2 template name or path to render the data with.",
)
@click.option(
    "--template-dir",
    "template_dirs",
    multiple=True,
    type=click.Path(exists=True, file_okay=False),
    help="Extra directory to search for templates (repeatable).",
)
@click.option(
    "-c",
    "--columns",
    default=None,
    help="Comma-separated list of column names to include.",
)
@click.option(
    "-f",
    "--filter",
    "filters",
    multiple=True,
    metavar="COL=VALUE",
    help="Filter rows by column value, e.g. --filter department=Engineering (repeatable).",
)
@click.option(
    "--sort-by",
    default=None,
    help="Column name to sort by.",
)
@click.option(
    "--desc",
    is_flag=True,
    default=False,
    help="Sort in descending order (requires --sort-by).",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    help="Maximum number of rows to output.",
)
@click.option(
    "-o",
    "--output",
    default=None,
    type=click.Path(writable=True, dir_okay=False),
    help="Write output to this file instead of stdout.",
)
def main(
    csv_file: str,
    template: str,
    template_dirs: tuple,
    columns: Optional[str],
    filters: tuple,
    sort_by: Optional[str],
    desc: bool,
    limit: Optional[int],
    output: Optional[str],
) -> None:
    """Format CSV_FILE as human-readable text using a Jinja2 template."""

    # Parse columns
    parsed_columns = [c.strip() for c in columns.split(",")] if columns else None

    # Parse filters (COL=VALUE pairs)
    parsed_filters: Dict[str, str] = {}
    for f in filters:
        if "=" not in f:
            raise click.BadParameter(
                f"Filters must be in COL=VALUE format, got: {f!r}",
                param_hint="--filter",
            )
        col, _, val = f.partition("=")
        parsed_filters[col.strip()] = val.strip()

    # Resolve template: if the user passed an absolute or relative path to a
    # .j2 file, add its parent directory so Jinja2 can find it by basename.
    template_path = Path(template)
    extra_dirs = list(template_dirs)
    if template_path.suffix and template_path.exists():
        extra_dirs.append(str(template_path.parent))
        template = template_path.name

    formatter = CSVFormatter(template_dirs=extra_dirs if extra_dirs else None)

    result = formatter.format_file(
        csv_file,
        template_name=template,
        columns=parsed_columns,
        filters=parsed_filters if parsed_filters else None,
        sort_by=sort_by,
        ascending=not desc,
        limit=limit,
    )

    if output:
        Path(output).write_text(result, encoding="utf-8")
        click.echo(f"Output written to {output}")
    else:
        click.echo(result)
