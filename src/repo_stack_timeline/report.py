import base64
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from .errors import TimelineError


def json_bytes(report, maximum, budget=None):
    output = bytearray()
    encoder = json.JSONEncoder(ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False)
    for chunk in encoder.iterencode(report):
        if budget:
            budget.check()
        data = chunk.encode('ascii')
        if len(output) + len(data) + 1 > maximum:
            raise TimelineError('report_bytes_limit', 'Serialized JSON exceeds report byte limit')
        output.extend(data)
    output.extend(b'\n')
    return bytes(output)


def html_bytes(data):
    root = Path(__file__).parent
    style = (root / 'viewer.css').read_text('utf-8')
    script = (root / 'viewer.js').read_text('utf-8')
    def digest(value):
        return base64.b64encode(hashlib.sha256(value.encode('utf-8')).digest()).decode('ascii')
    csp = f"default-src 'none'; script-src 'sha256-{digest(script)}'; style-src 'sha256-{digest(style)}'; connect-src 'none'; img-src 'none'; base-uri 'none'; form-action 'none'"
    # Data cannot close its inert script element; rendered strings use textContent.
    safe = data.decode('ascii').replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    template = (root / 'viewer.html').read_text('utf-8')
    # Replace data last, so hostile text resembling a template token stays literal.
    return template.replace('@@CSP@@', csp).replace('@@STYLE@@', style).replace('@@SCRIPT@@', script).replace('@@DATA@@', safe).encode('utf-8')


def rename_exclusive(source, destination):
    """Linux atomic no-replace directory publication. Never fall back to overwrite."""
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        rename = libc.renameat2
    except AttributeError:
        raise TimelineError('unsupported_platform', 'Atomic publication requires Linux renameat2') from None
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(source), -100, os.fsencode(destination), 1):
        code = ctypes.get_errno()
        if code in (errno.EEXIST, errno.ENOTEMPTY):
            raise TimelineError('output_exists', 'Output already exists; choose a fresh directory')
        raise OSError(code, os.strerror(code), str(destination))


def publish(report, output, budget):
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise TimelineError('output_exists', 'Output already exists; choose a fresh directory')
    if not output.parent.is_dir():
        raise TimelineError('output_parent_missing', 'Output parent directory must already exist')
    data = json_bytes(report, budget.limits.report_bytes, budget)
    html = html_bytes(data)
    checksum = ''.join(f'{hashlib.sha256(raw).hexdigest()}  {name}\n' for name, raw in [('report.json',data),('index.html',html)]).encode()
    if len(data) + len(html) + len(checksum) > budget.limits.report_bytes:
        raise TimelineError('report_bytes_limit', 'Complete bundle exceeds report byte limit')
    budget.check()
    temporary = Path(tempfile.mkdtemp(prefix='.repo-stack-tmp-', dir=output.parent))
    try:
        for name, raw in [('report.json',data),('index.html',html),('SHA256SUMS',checksum)]:
            budget.check()
            with (temporary / name).open('xb') as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
        descriptor = os.open(temporary, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        budget.check()
        rename_exclusive(temporary, output)
        descriptor = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {'files': ['report.json', 'index.html', 'SHA256SUMS'], 'bytes': len(data)+len(html)+len(checksum)}
