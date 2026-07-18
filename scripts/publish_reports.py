#!/usr/bin/env python3
"""Copy generated stock-research artifacts into a browsable report repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

REPORT_RE = re.compile(r"^(?P<symbol>[A-Z0-9.-]+)_(?P<date>\d{8})\.(?P<ext>md|json)$")


@dataclass(frozen=True)
class PublishedReport:
    symbol: str
    date: str
    markdown: Path
    json_file: Path | None


def copy_reports(source: Path, destination: Path) -> list[PublishedReport]:
    grouped: dict[tuple[str, str], dict[str, Path]] = {}
    for artifact in sorted(source.iterdir() if source.exists() else []):
        match = REPORT_RE.fullmatch(artifact.name)
        if not match:
            continue
        key = (match["symbol"], match["date"])
        grouped.setdefault(key, {})[match["ext"]] = artifact

    published: list[PublishedReport] = []
    for (symbol, compact_date), artifacts in sorted(grouped.items()):
        markdown = artifacts.get("md")
        if markdown is None:
            continue

        report_date = f"{compact_date[:4]}-{compact_date[4:6]}-{compact_date[6:]}"
        symbol_dir = destination / "reports" / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)

        markdown_target = symbol_dir / f"{report_date}.md"
        shutil.copy2(markdown, markdown_target)
        shutil.copy2(markdown, symbol_dir / "latest.md")

        json_target = None
        if json_source := artifacts.get("json"):
            json.loads(json_source.read_text(encoding="utf-8"))
            json_target = symbol_dir / f"{report_date}.json"
            shutil.copy2(json_source, json_target)
            shutil.copy2(json_source, symbol_dir / "latest.json")

        published.append(
            PublishedReport(
                symbol=symbol,
                date=report_date,
                markdown=markdown_target,
                json_file=json_target,
            )
        )

    return published


def build_index(reports: list[PublishedReport]) -> str:
    latest: dict[str, PublishedReport] = {}
    for report in reports:
        if report.symbol not in latest or report.date > latest[report.symbol].date:
            latest[report.symbol] = report

    rows = []
    for symbol, report in sorted(latest.items()):
        base = f"reports/{symbol}"
        archive = sorted(
            (item for item in reports if item.symbol == symbol),
            key=lambda item: item.date,
            reverse=True,
        )
        archive_links = " · ".join(
            f"[{item.date}]({base}/{item.date}.md)" for item in archive
        )
        rows.append(
            f"| {symbol} | [{report.date}]({base}/latest.md) | "
            f"[JSON]({base}/latest.json) | {archive_links} |"
        )

    table = (
        "| Symbol | Latest report | Latest data | Archive |\n"
        "|---|---|---|---|\n"
        + "\n".join(rows)
        if rows
        else "_No reports published yet._"
    )

    return f"""# Stock Research Reports

Automatically published preliminary stock-research reports generated from programmatic market-data sources.

## Reports

{table}

## Important

These reports present preliminary market data and deterministic technical analysis. They are not investment advice and do not provide buy, sell, or hold recommendations.

Source code: [wink-/stock-research](https://github.com/wink-/stock-research)
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Directory containing generated reports")
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Report repository root",
    )
    args = parser.parse_args()

    reports = copy_reports(args.source.resolve(), args.destination.resolve())
    (args.destination / "README.md").write_text(build_index(reports), encoding="utf-8")
    print(f"Prepared {len(reports)} report(s).")


if __name__ == "__main__":
    main()
