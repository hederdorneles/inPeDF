"""Headless batch export with a bounded queue of independent PDF processes.

Copyright (C) 2026 Heder Dorneles Soares
License: GPL-2.0-only
"""

import argparse
from collections import Counter
import hashlib
import json
import multiprocessing
from pathlib import Path
import signal
import sys
import tempfile
import time

from .export import FORMATS, convert_file, publish_outputs


def convert_worker(connection, source, formats, staging, pages, password):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        result = {"status": "ok", **convert_file(source, formats, staging, pages, password)}
    except Exception as error:
        result = {"status": "error", "error": str(error)}
    try:
        connection.send(result)
    finally:
        connection.close()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="inpedf export",
        description=(
            "Convert PDFs to Markdown, TXT and JSON without a graphical session. "
            "Text is extracted page by page with source-page references. "
            "Batches use a configurable number of independent processes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  inpedf export document.pdf --format md,json --output-dir converted\n"
            "  inpedf export documents/*.pdf --jobs 4 --report report.json\n"
            "  inpedf export manual.pdf --pages 1,3-5 --format txt\n"
            "  inpedf export protected.pdf --password-file password.txt\n"
            "  inpedf export document.pdf --quiet\n"
            "  inpedf export document.pdf --verbose\n\n"
            "Existing outputs are preserved unless --overwrite is supplied.\n"
            "A failed PDF does not stop the remaining files. Ctrl+C cancels active\n"
            "tasks and removes incomplete outputs; completed files are kept.\n"
            "OCR and reconstruction of headings, tables and formulas are future work.\n\n"
            "Exit codes: 0 success; 1 conversion/write failure; 2 invalid options;\n"
            "            130 cancelled."
        ),
    )
    parser.add_argument("--usage", action="help", help="Show this help message and exit.")
    parser.add_argument("files", nargs="+", help="PDF file paths (shell wildcards are supported).")
    parser.add_argument("--format", default="md", help="Comma-separated formats: md,txt,json (default: md).")
    parser.add_argument("--output-dir", type=Path, default=Path("converted"))
    parser.add_argument("--pages", default="all", help="1-based pages, e.g. 1,3-5 (default: all).")
    parser.add_argument("--jobs", type=int, default=2, help="Parallel PDF processes (default: 2).")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing output files.")
    parser.add_argument("--password-file", type=Path, help="UTF-8 file containing a common PDF password.")
    parser.add_argument("--report", type=Path, help="Write a JSON result report for retrying failed files.")
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("--quiet", action="store_true", help="Show errors only.")
    verbosity.add_argument("--verbose", action="store_true", help="Show conversion settings, worker IDs and output paths.")
    return parser


def plan_outputs(sources, formats, output_dir):
    counts = Counter(source.stem.casefold() for source in sources)
    planned = []
    used = set()
    for source in sources:
        stem = source.stem
        if counts[stem.casefold()] > 1:
            suffix = hashlib.sha256(str(source).encode()).hexdigest()[:12]
            stem += "-" + suffix
        destinations = {fmt: output_dir / (stem + "." + fmt) for fmt in formats}
        names = {str(path).casefold() for path in destinations.values()}
        if used & names:
            raise ValueError(f"Conflicting output names for {source}")
        used.update(names)
        planned.append((source, destinations))
    return planned


def run_batch(planned, formats, args, password):
    results = []
    pending = []
    tasks = iter(planned)
    exhausted = False
    interrupted = False
    context = multiprocessing.get_context("spawn")
    try:
        while pending or not exhausted:
            while not exhausted and len(pending) < args.jobs:
                item = next(tasks, None)
                if item is None:
                    exhausted = True
                    break
                source, destinations = item
                if not args.overwrite and any(path.exists() for path in destinations.values()):
                    result = {"source": str(source), "status": "error", "error": "Output already exists. Use --overwrite."}
                    results.append(result)
                    print(f"ERROR {source}: {result['error']}", file=sys.stderr)
                    continue
                stage = tempfile.TemporaryDirectory(prefix=".inpedf-", dir=args.output_dir)
                receive, send = context.Pipe(duplex=False)
                process = context.Process(target=convert_worker, args=(
                    send, str(source), formats, stage.name, args.pages, password,
                ))
                try:
                    process.start()
                except BaseException:
                    if process.pid is not None:
                        if process.is_alive():
                            process.terminate()
                        process.join()
                    receive.close()
                    send.close()
                    stage.cleanup()
                    raise
                send.close()
                pending.append((process, receive, source, destinations, stage))
                if not args.quiet:
                    print(f"START {source}", file=sys.stderr, flush=True)
                if args.verbose:
                    print(f"DETAIL worker PID {process.pid}: {source}", file=sys.stderr)
            ready = [
                item for item in pending
                if item[1].poll() or item[0].exitcode is not None
            ]
            for item in ready:
                process, connection, source, destinations, stage = item
                try:
                    try:
                        result = connection.recv()
                    except EOFError:
                        raise RuntimeError("Conversion process exited without a result.")
                    if result["status"] == "ok":
                        publish_outputs(stage.name, destinations, args.overwrite)
                        result["outputs"] = [str(path) for path in destinations.values()]
                        if not args.quiet:
                            print(
                                f"OK [{len(results) + 1}/{len(planned)}] {source} ({result['pages']} pages)",
                                flush=True,
                            )
                        if args.verbose:
                            for destination in destinations.values():
                                print(f"DETAIL output: {destination}", file=sys.stderr)
                            print(f"DETAIL pages without text: {result['pages_without_text']}", file=sys.stderr)
                        if result["pages_without_text"] and not args.quiet:
                            print(f"WARNING {source}: {len(result['pages_without_text'])} pages without extractable text; OCR may be required.", file=sys.stderr)
                    else:
                        print(f"ERROR {source}: {result['error']}", file=sys.stderr)
                except Exception as error:
                    result = {"status": "error", "error": str(error)}
                    print(f"ERROR {source}: {error}", file=sys.stderr)
                finally:
                    process.join()
                    connection.close()
                    stage.cleanup()
                results.append({"source": str(source), **result})
                pending.remove(item)
            if pending and not ready:
                time.sleep(0.05)
    except KeyboardInterrupt:
        interrupted = True
        if not args.quiet:
            print("Cancelled. Completed files have been kept.", file=sys.stderr)
    finally:
        for process, connection, source, destinations, stage in pending:
            if process.is_alive():
                process.terminate()
        for process, connection, source, destinations, stage in pending:
            process.join()
            connection.close()
            stage.cleanup()
    if interrupted:
        completed = {result["source"] for result in results}
        results.extend({"source": str(source), "status": "cancelled"}
                       for source, _ in planned if str(source) not in completed)
    return results, interrupted


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    formats = list(dict.fromkeys(args.format.split(",")))
    if not formats or any(fmt not in FORMATS for fmt in formats):
        parser.error("--format must contain md, txt or json, separated by commas.")
    if args.jobs < 1:
        parser.error("--jobs must be positive.")
    try:
        sources = list(dict.fromkeys(Path(name).expanduser().resolve() for name in args.files))
        args.output_dir = args.output_dir.expanduser().resolve()
        args.output_dir.mkdir(parents=True, exist_ok=True)
        planned = plan_outputs(sources, formats, args.output_dir)
        password = args.password_file.read_text(encoding="utf-8").rstrip("\r\n") if args.password_file else None
        if args.report:
            args.report = args.report.expanduser().resolve()
            reserved = set(sources) | {path for _, destinations in planned for path in destinations.values()}
            if args.report in reserved:
                raise ValueError("The report must have a separate path from input and output files.")
            if args.report.exists() and not args.overwrite:
                raise FileExistsError("Report already exists. Use --overwrite.")
        if args.verbose:
            print(
                f"DETAIL files={len(sources)} jobs={args.jobs} formats={','.join(formats)} "
                f"pages={args.pages} overwrite={args.overwrite}",
                file=sys.stderr,
            )
            print(f"DETAIL output directory: {args.output_dir}", file=sys.stderr)
        results, interrupted = run_batch(planned, formats, args, password)
        successes = sum(result["status"] == "ok" for result in results)
        failures = sum(result["status"] == "error" for result in results)
        summary = {"succeeded": successes, "failed": failures, "cancelled": interrupted, "files": results}
        if not args.quiet:
            print(f"Completed: {successes}; failed: {failures}; cancelled: {interrupted}", file=sys.stderr)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".inpedf-report-", dir=args.report.parent) as stage:
                (Path(stage) / "document.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                publish_outputs(stage, {"json": args.report}, args.overwrite)
        return 130 if interrupted else int(failures > 0)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
