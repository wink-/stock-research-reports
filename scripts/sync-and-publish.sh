#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${STOCK_RESEARCH_REPORT_REPO:-/home/ubuntu/projects/stock-research-reports}"
SOURCE_DIR="${STOCK_RESEARCH_REPORT_SOURCE:-/home/ubuntu/projects/stock-research/reports}"

python3 "$REPO_DIR/scripts/publish_reports.py" "$SOURCE_DIR" --destination "$REPO_DIR" >/dev/null

git -C "$REPO_DIR" add README.md reports
if git -C "$REPO_DIR" diff --cached --quiet; then
    exit 0
fi

git -C "$REPO_DIR" commit -m "reports: publish generated research"
git -C "$REPO_DIR" push origin main
printf 'Published updated stock research reports.\n'
