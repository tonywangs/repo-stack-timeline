#!/usr/bin/env python3
"""Offline project-specific wheel installer; pip is not required."""
import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import venv
import zipfile
from wheel_backend import build_wheel, DIST


def install(destination):
    destination=Path(destination).absolute()
    if destination.exists():raise ValueError('Installation destination must be fresh')
    if any(x.isspace() for x in str(destination)):
        raise ValueError('Installation path must not contain whitespace (console-script shebang)')
    venv.EnvBuilder(with_pip=False).create(destination)
    python=destination/'bin/python'
    purelib=Path(subprocess.check_output([str(python),'-I','-c','import sysconfig;print(sysconfig.get_path("purelib"))'],text=True).strip())
    with tempfile.TemporaryDirectory() as tmp:
        wheel=Path(tmp)/build_wheel(tmp)
        with zipfile.ZipFile(wheel) as archive:
            records=list(csv.reader(io.StringIO(archive.read(DIST+'/RECORD').decode())))
            for name,digest,size in records:
                raw=archive.read(name)
                if digest:
                    expected='sha256='+base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b'=').decode()
                    if digest!=expected or str(len(raw))!=size:raise ValueError('Wheel RECORD mismatch')
                path=purelib/name
                if '..' in Path(name).parts or Path(name).is_absolute():raise ValueError('Invalid wheel path')
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    script=destination/'bin/repo-stack-timeline'
    script.write_text(f'#!{python} -I\nfrom repo_stack_timeline.cli import main\nraise SystemExit(main())\n')
    script.chmod(0o755)
    return script


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--venv',required=True)
    print(install(p.parse_args().venv))
