"""
Core formatter module.

Uses pandas to load and process CSV data, then renders it through Jinja2
templates to produce human-readable text output.
"""

from __future__ import annotations

import os
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import pandas as pd
from jinja2 import (
    Environment,
    FileSystemLoader,
    PackageLoader,
    Template,
    select_autoescape,
)


# Built-in template directory bundled with the package
_BUILTIN_TEMPLATES_DIR = Path(__file__).parent / "templates"


class CSVFormatter:
    """Format CSV data as human-readable text using Jinja2 templates.

    Parameters
    ----------
    template_dirs:
        Extra directories to search for templates, in addition to the
        built-in templates that ship with the package.
    """

    def __init__(self, template_dirs: Optional[Sequence[Union[str, Path]]] = None) -> None:
        dirs: List[str] = [str(_BUILTIN_TEMPLATES_DIR)]
        if template_dirs:
            dirs = [str(d) for d in template_dirs] + dirs

        self._env = Environment(
            loader=FileSystemLoader(dirs),
            autoescape=select_autoescape(disabled_extensions=("j2", "txt")),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register useful filters
        self._env.filters["currency"] = _filter_currency
        self._env.filters["floatfmt"] = _filter_floatfmt
        self._env.filters["ljust"] = _filter_ljust
        self._env.filters["rjust"] = _filter_rjust
        self._env.filters["center"] = _filter_center

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def format_file(
        self,
        csv_path: Union[str, Path],
        template_name: str = "default.txt.j2",
        *,
        columns: Optional[Sequence[str]] = None,
        filters: Optional[Dict[str, object]] = None,
        sort_by: Optional[Union[str, Sequence[str]]] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        extra_context: Optional[dict] = None,
        read_csv_kwargs: Optional[dict] = None,
    ) -> str:
        """Read *csv_path*, process the data, and render *template_name*.

        Parameters
        ----------
        csv_path:
            Path to the CSV file to read.
        template_name:
            Name of the Jinja2 template file (must be resolvable via the
            configured template dirs).
        columns:
            Subset of columns to include in the output. All columns are
            included when ``None``.
        filters:
            Mapping of ``column_name -> value`` used to keep only rows
            where the column equals the given value.
        sort_by:
            Column name (or list of column names) to sort by.
        ascending:
            Sort direction; ignored when *sort_by* is ``None``.
        limit:
            Maximum number of rows to include (applied after sorting).
        extra_context:
            Arbitrary extra variables made available inside the template.
        read_csv_kwargs:
            Extra keyword arguments forwarded to :func:`pandas.read_csv`.

        Returns
        -------
        str
            Rendered text output.
        """
        df = pd.read_csv(csv_path, **(read_csv_kwargs or {}))
        return self._render(
            df,
            template_name,
            columns=columns,
            filters=filters,
            sort_by=sort_by,
            ascending=ascending,
            limit=limit,
            extra_context=extra_context,
        )

    def format_string(
        self,
        csv_string: str,
        template_name: str = "default.txt.j2",
        *,
        columns: Optional[Sequence[str]] = None,
        filters: Optional[Dict[str, object]] = None,
        sort_by: Optional[Union[str, Sequence[str]]] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        extra_context: Optional[dict] = None,
        read_csv_kwargs: Optional[dict] = None,
    ) -> str:
        """Same as :meth:`format_file` but accepts raw CSV text instead of a path."""
        df = pd.read_csv(StringIO(csv_string), **(read_csv_kwargs or {}))
        return self._render(
            df,
            template_name,
            columns=columns,
            filters=filters,
            sort_by=sort_by,
            ascending=ascending,
            limit=limit,
            extra_context=extra_context,
        )

    def render_template_string(
        self,
        template_source: str,
        csv_path: Optional[Union[str, Path]] = None,
        csv_string: Optional[str] = None,
        *,
        columns: Optional[Sequence[str]] = None,
        filters: Optional[Dict[str, object]] = None,
        sort_by: Optional[Union[str, Sequence[str]]] = None,
        ascending: bool = True,
        limit: Optional[int] = None,
        extra_context: Optional[dict] = None,
        read_csv_kwargs: Optional[dict] = None,
    ) -> str:
        """Render an inline template string (not a file) against CSV data.

        Exactly one of *csv_path* or *csv_string* must be supplied.
        """
        if csv_path is None and csv_string is None:
            raise ValueError("Provide either csv_path or csv_string.")
        if csv_path is not None and csv_string is not None:
            raise ValueError("Provide only one of csv_path or csv_string, not both.")

        if csv_path is not None:
            df = pd.read_csv(csv_path, **(read_csv_kwargs or {}))
        else:
            df = pd.read_csv(StringIO(csv_string), **(read_csv_kwargs or {}))

        df = self._process_dataframe(
            df, columns=columns, filters=filters,
            sort_by=sort_by, ascending=ascending, limit=limit)

        template = self._env.from_string(template_source)
        context = self._build_context(df, extra_context)
        return template.render(**context)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _render(
        self,
        df: pd.DataFrame,
        template_name: str,
        *,
        columns: Optional[Sequence[str]],
        filters: Optional[Dict[str, object]],
        sort_by: Optional[Union[str, Sequence[str]]],
        ascending: bool,
        limit: Optional[int],
        extra_context: Optional[dict],
    ) -> str:
        df = self._process_dataframe(
            df, columns=columns, filters=filters,
            sort_by=sort_by, ascending=ascending, limit=limit)
        template = self._env.get_template(template_name)
        context = self._build_context(df, extra_context)
        return template.render(**context)

    @staticmethod
    def _process_dataframe(
        df: pd.DataFrame,
        *,
        columns: Optional[Sequence[str]],
        filters: Optional[Dict[str, object]],
        sort_by: Optional[Union[str, Sequence[str]]],
        ascending: bool,
        limit: Optional[int],
    ) -> pd.DataFrame:
        # Apply filters before column selection so filter columns don't need
        # to be in the output column list.
        if filters:
            for col, val in filters.items():
                if col not in df.columns:
                    raise ValueError(f"Filter column not found in CSV: {col!r}")
                df = df[df[col] == val]

        if columns:
            missing = [c for c in columns if c not in df.columns]
            if missing:
                raise ValueError(f"Columns not found in CSV: {missing}")
            df = df[list(columns)]

        if sort_by:
            sort_cols = [sort_by] if isinstance(sort_by, str) else list(sort_by)
            df = df.sort_values(by=sort_cols, ascending=ascending)

        if limit is not None:
            df = df.head(limit)

        return df.reset_index(drop=True)

    @staticmethod
    def _build_context(df: pd.DataFrame, extra_context: Optional[dict]) -> dict:
        rows = df.to_dict(orient="records")

        # Compute column widths (max of header length and longest cell value)
        col_widths: Dict[str, int] = {}
        for col in df.columns:
            width = len(str(col))
            for row in rows:
                cell_len = len(str(row[col]) if row[col] is not None else "")
                if cell_len > width:
                    width = cell_len
            col_widths[col] = width

        context: dict = {
            "columns": list(df.columns),
            "rows": rows,
            "row_count": len(rows),
            "col_widths": col_widths,
            "summary": {
                col: {
                    "min": df[col].min() if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "max": df[col].max() if pd.api.types.is_numeric_dtype(df[col]) else None,
                    "mean": round(float(df[col].mean()), 4)
                    if pd.api.types.is_numeric_dtype(df[col])
                    else None,
                    "unique": int(df[col].nunique()),
                    "missing": int(df[col].isna().sum()),
                }
                for col in df.columns
            },
        }
        if extra_context:
            context.update(extra_context)
        return context


# ------------------------------------------------------------------
# Jinja2 custom filters
# ------------------------------------------------------------------

def _filter_currency(value, symbol: str = "$", decimals: int = 2) -> str:
    """Format a number as a currency string, e.g. ``1234.5`` → ``$1,234.50``."""
    try:
        return f"{symbol}{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _filter_floatfmt(value, decimals: int = 2) -> str:
    """Format a float to a fixed number of decimal places."""
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _filter_ljust(value, width: int, fillchar: str = " ") -> str:
    return str(value).ljust(width, fillchar)


def _filter_rjust(value, width: int, fillchar: str = " ") -> str:
    return str(value).rjust(width, fillchar)


def _filter_center(value, width: int, fillchar: str = " ") -> str:
    return str(value).center(width, fillchar)
