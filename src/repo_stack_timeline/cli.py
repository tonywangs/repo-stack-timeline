import argparse
from dataclasses import fields
import json
import signal
from pathlib import Path
import sys
from .errors import TimelineError
from .limits import Limits, Budget
from .scan import scan
from .report import publish


def parser():
    p = argparse.ArgumentParser(description='Compare declared Python/npm dependencies in explicitly ordered Git commits, offline.')
    p.add_argument('repository', type=Path)
    p.add_argument('commits', nargs='+', help='1–32 hexadecimal commit IDs; order is significant; repeats allowed')
    p.add_argument('--output', required=True, type=Path, help='Fresh output directory outside the source repository; parent must exist')
    p.add_argument('--lockfiles', action='store_true', help='Include recorded npm lockfile v2/v3 state (schema version 2)')
    p.add_argument('--object-format', choices=['sha1', 'sha256'], default='sha1')
    for field in fields(Limits):
        p.add_argument('--max-' + field.name.replace('_','-'), type=float if field.name == 'seconds' else int, default=field.default)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    old_handlers = {}
    try:
        limits = Limits(**{field.name: getattr(args,'max_'+field.name) for field in fields(Limits)})
        source = args.repository.resolve()
        destination = args.output.resolve()
        if destination == source or source in destination.parents:
            raise TimelineError('output_inside_repository', 'Write reports outside the scanned repository to preserve its state')
        budget = Budget(limits)
        def cancel(signum, _frame):
            raise TimelineError('runtime_limit' if signum == signal.SIGALRM else 'cancelled', 'Runtime limit reached' if signum == signal.SIGALRM else 'Scan cancelled')
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGALRM):
            old_handlers[sig] = signal.signal(sig, cancel)
        signal.setitimer(signal.ITIMER_REAL, limits.seconds)
        report = scan(source, args.commits, limits, args.object_format, budget, lockfiles=args.lockfiles)
        result = publish(report, args.output, budget)
        if args.lockfiles:
            result['lockfile_status'] = report['lockfile_status']
        print(json.dumps(dict(status='ok', snapshots=len(report['snapshots']), **result), sort_keys=True))
        return 0
    except TimelineError as error:
        print(json.dumps(dict(status='error', code=error.code, message=str(error)), ensure_ascii=True, sort_keys=True), file=sys.stderr)
        return 130 if error.code == 'cancelled' else 2
    except (OSError, ValueError, UnicodeError, RecursionError) as error:
        print(json.dumps(dict(status='error', code='io_or_serialization_error', message=type(error).__name__), sort_keys=True), file=sys.stderr)
        return 2
    finally:
        if old_handlers:
            signal.setitimer(signal.ITIMER_REAL, 0)
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
