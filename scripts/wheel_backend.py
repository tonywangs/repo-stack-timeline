"""Small, dependency-free PEP 517 backend for this pure-Python project only."""
import base64
import csv
import hashlib
import io
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIST = 'repo_stack_timeline-1.0.0.dist-info'
METADATA = '''Metadata-Version: 2.1
Name: repo-stack-timeline
Version: 1.0.0
Summary: Offline declared dependency history for explicit Git snapshots
Requires-Python: >=3.11
License: MIT
Classifier: Operating System :: POSIX :: Linux

Vendored packaging 24.0 retains its Apache-2.0/BSD-2-Clause licenses.
'''
WHEEL = 'Wheel-Version: 1.0\nGenerator: repo-stack-stdlib\nRoot-Is-Purelib: true\nTag: py3-none-any\n'
ENTRY_POINTS = '[console_scripts]\nrepo-stack-timeline = repo_stack_timeline.cli:main\n'


def get_requires_for_build_wheel(config_settings=None):
    return []


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    files = {}
    for path in sorted((ROOT/'src/repo_stack_timeline').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            files[path.relative_to(ROOT/'src').as_posix()] = path.read_bytes()
    files[DIST+'/METADATA'] = METADATA.encode()
    files[DIST+'/WHEEL'] = WHEEL.encode()
    files[DIST+'/entry_points.txt'] = ENTRY_POINTS.encode()
    files[DIST+'/LICENSE'] = (ROOT/'LICENSE').read_bytes()
    record = io.StringIO(newline='')
    writer = csv.writer(record,lineterminator='\n')
    for name,raw in sorted(files.items()):
        digest=base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b'=').decode()
        writer.writerow([name,'sha256='+digest,len(raw)])
    writer.writerow([DIST+'/RECORD','',''])
    files[DIST+'/RECORD']=record.getvalue().encode()
    destination=Path(wheel_directory)/'repo_stack_timeline-1.0.0-py3-none-any.whl'
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,raw in sorted(files.items()):
            item=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o644<<16
            archive.writestr(item,raw)
    return destination.name


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',default='dist')
    print(build_wheel(p.parse_args().output))
