import sys
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import date, timedelta
from pathlib import Path
from calendar import monthrange

# Ensure tools/ is on the path regardless of where the script is invoked from
sys.path.insert(0, str(Path(__file__).parent))

from connectors import ALL_CONNECTORS
from connectors.config import load_config, ConfigError

DEFAULT_CONFIG_PATH = Path.home() / ".invoicepilot" / "config.yml"
LOCK_FILE = Path.home() / ".invoicepilot" / ".lock"
API_TIMEOUT = 60
PLAYWRIGHT_TIMEOUT = 120


def months_between(start: date, end: date) -> list[date]:
    months = []
    current = start.replace(day=1)
    while current <= end:
        months.append(current)
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return months


def parse_date_range(query: str) -> tuple[date, date]:
    today = date.today()
    query = query.lower().strip()

    if "last month" in query:
        first_of_this = today.replace(day=1)
        end_of_last = first_of_this - timedelta(days=1)
        start = end_of_last.replace(day=1)
        return start, end_of_last

    if query.startswith("since "):
        # "since April 2024"
        from dateutil.parser import parse as dateparse
        start = dateparse(query.replace("since ", "")).date().replace(day=1)
        return start, today

    # Try "March 2025" or "Q1 2025"
    try:
        from dateutil.parser import parse as dateparse
        parsed = dateparse(query).date().replace(day=1)
        last_day = monthrange(parsed.year, parsed.month)[1]
        return parsed, parsed.replace(day=last_day)
    except Exception:
        raise ValueError(f"Could not parse date range: '{query}'. Try 'last month', 'March 2025', or 'since April 2024'.")


def run_download(query: str, overwrite: bool = False, connectors_filter: list[str] | None = None):
    # Lock file
    if LOCK_FILE.exists():
        print("InvoicePilot is already running. If this is wrong, delete ~/.invoicepilot/.lock")
        sys.exit(1)

    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOCK_FILE.touch()

        try:
            config = load_config(DEFAULT_CONFIG_PATH)
        except ConfigError as e:
            print(f"Config error: {e}")
            sys.exit(1)

        try:
            start, end = parse_date_range(query)
        except ValueError as e:
            print(str(e))
            sys.exit(1)

        out_base: Path = config["output_dir_expanded"]
        months = months_between(start, end)
        multi = len(months) > 1

        connector_configs = config.get("connectors") or {}
        unconfigured = config.get("_unconfigured", [])

        # Build connector instances
        active = []
        for cls in ALL_CONNECTORS:
            # Instantiate first so we can read instance.name safely (works for both real and mocked connectors)
            instance = cls(config={})
            inst_name = instance.name
            if connectors_filter and inst_name.lower() not in [f.lower() for f in connectors_filter]:
                continue
            svc_key = inst_name.lower().replace(" ", "")
            cfg = connector_configs.get(svc_key) or connector_configs.get(inst_name.lower()) or {}
            # Re-instantiate with the actual config
            instance = cls(config=cfg)
            if not instance.is_configured():
                continue
            active.append(instance)

        api_connectors = [c for c in active if c.stable]
        playwright_connectors = [c for c in active if not c.stable]

        if multi:
            print(f"InvoicePilot — Downloading {start.strftime('%B %Y')} → {end.strftime('%B %Y')} ({len(months)} months)\n")
        else:
            print(f"InvoicePilot — Downloading {start.strftime('%B %Y')}\n")

        all_results = {}  # connector_name -> ConnectorResult (aggregated)

        for i, month_start in enumerate(months):
            if multi:
                print(f"  Downloading month {i+1}/{len(months)}: {month_start.strftime('%B %Y')}...")

            if month_start.month == 12:
                month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)

            month_dir = out_base / month_start.strftime("%Y-%m")

            # Run API connectors in parallel
            def run_one(connector):
                svc_dir = month_dir / connector.name.replace(" ", "")
                return connector.download(month_start, month_end, svc_dir)

            with ThreadPoolExecutor(max_workers=len(api_connectors) or 1) as pool:
                futures = {pool.submit(run_one, c): c for c in api_connectors}
                for future, connector in futures.items():
                    try:
                        result = future.result(timeout=API_TIMEOUT)
                    except FuturesTimeout:
                        from connectors.base import ConnectorResult
                        result = ConnectorResult(
                            connector=connector.name, files=[], count=0, skipped=0,
                            error=f"Timed out after {API_TIMEOUT}s",
                            hint="Try again later",
                            timed_out=True,
                        )
                    _merge_result(all_results, result)

            # Run Playwright connectors serially
            for connector in playwright_connectors:
                svc_dir = month_dir / connector.name.replace(" ", "")
                result = connector.download(month_start, month_end, svc_dir)
                _merge_result(all_results, result)

        # Print summary
        print()
        total_count = 0
        total_skipped = 0
        issues = []

        for name, result in all_results.items():
            name_str = str(name)
            badge = " ⚠" if not _get_connector_stable(active, name) else ""
            if result.error:
                hint_str = f" → {result.hint}" if result.hint else ""
                print(f"  ✗ {name_str:<18}{result.error}{hint_str}")
                issues.append(name)
            else:
                count_str = f"{result.count} invoice{'s' if result.count != 1 else ''}"
                name_badge = name_str + badge
                if multi:
                    print(f"  ✓ {name_badge:<18}{count_str} across {len(months)} months")
                else:
                    print(f"  ✓ {name_badge:<18}{count_str}")
                total_count += result.count
                total_skipped += result.skipped

        print()
        skip_str = f" {total_skipped} skipped (already exist)." if total_skipped else ""
        issue_str = f" {len(issues)} service{'s' if len(issues) != 1 else ''} need{'s' if len(issues) == 1 else ''} attention." if issues else ""
        print(f"  {total_count} invoice{'s' if total_count != 1 else ''} downloaded.{skip_str}{issue_str}")
        print(f"  Folder: {out_base}/")

    finally:
        LOCK_FILE.unlink(missing_ok=True)


def _merge_result(results: dict, result):
    name = result.connector
    if name not in results:
        results[name] = result
    else:
        existing = results[name]
        from connectors.base import ConnectorResult
        results[name] = ConnectorResult(
            connector=name,
            files=existing.files + result.files,
            count=existing.count + result.count,
            skipped=existing.skipped + result.skipped,
            error=result.error or existing.error,
            hint=result.hint or existing.hint,
            timed_out=result.timed_out or existing.timed_out,
        )


def _get_connector_stable(active, name):
    for c in active:
        if c.name == name:
            return c.stable
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="+", help='Date range, e.g. "last month" or "March 2025"')
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--only", nargs="+", help="Only run specific connectors")
    args = parser.parse_args()
    run_download(" ".join(args.query), overwrite=args.overwrite, connectors_filter=args.only)
