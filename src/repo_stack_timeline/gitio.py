"""Bounded plumbing against an isolated, read-only view of the object database.

No Git command runs in the source repository or reads its configuration/refs.
Only hexadecimal object identifiers are accepted, intentionally.
"""
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import subprocess
import tempfile
import time
from .errors import TimelineError


class Runner:
    def __init__(self, cwd, env, budget):
        self.cwd, self.env, self.budget = cwd, env, budget
        self.git = shutil.which("git")
        if not self.git:
            raise TimelineError("git_unavailable", "Git is required")

    def run(self, args, cap=None, allowed=(0,)):
        self.budget.check()
        cap = self.budget.limits.git_output_bytes if cap is None else cap
        proc = subprocess.Popen([self.git, *args], cwd=self.cwd, env=self.env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        chunks = {proc.stdout: bytearray(), proc.stderr: bytearray()}
        try:
            with selectors.DefaultSelector() as sel:
                for stream in chunks:
                    os.set_blocking(stream.fileno(), False)
                    sel.register(stream, selectors.EVENT_READ)
                while sel.get_map():
                    self.budget.check()
                    for key, _ in sel.select(min(.05, max(0, self.budget.deadline - time.monotonic()))):
                        data = os.read(key.fileobj.fileno(), 65536)
                        if not data:
                            sel.unregister(key.fileobj)
                            continue
                        limit = cap if key.fileobj is proc.stdout else 16384
                        if len(chunks[key.fileobj]) + len(data) > limit:
                            raise TimelineError("git_output_limit", "Git output exceeded its byte limit")
                        chunks[key.fileobj].extend(data)
                while proc.poll() is None:
                    self.budget.check()
                    time.sleep(.005)
            out = bytes(chunks[proc.stdout])
            if proc.returncode not in allowed:
                # Do not expose paths, config, credentials, or uncontrolled Git diagnostics.
                raise TimelineError("git_object_error", f"Git {args[0]} failed (exit {proc.returncode}); missing, ambiguous, corrupt, or wrong-type object")
            return proc.returncode, out
        finally:
            # Kill the entire group even if a parent exited while a descendant held a pipe.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            proc.stdout.close()
            proc.stderr.close()


class ObjectRepository:
    def __init__(self, source, budget, object_format="sha1"):
        if object_format not in ("sha1", "sha256"):
            raise TimelineError("invalid_format", "Object format must be sha1 or sha256")
        self.source = Path(source).resolve()
        self.budget = budget
        self.width = 40 if object_format == 'sha1' else 64
        gitdir = self.source / '.git' if (self.source / '.git').is_dir() else self.source
        if (self.source / '.git').is_file():
            raise TimelineError("unsupported_repository", "Gitfiles/linked worktrees are unsupported; use the owning repository or a bare clone")
        self.objects = gitdir / 'objects'
        if not self.objects.is_dir() or not (gitdir / 'HEAD').is_file():
            raise TimelineError("invalid_repository", "Expected a regular or bare Git repository")
        alternates = self.objects / 'info' / 'alternates'
        if alternates.exists() and alternates.stat().st_size:
            raise TimelineError("unsupported_repository", "Alternate object stores are unsupported")
        self.temp = tempfile.TemporaryDirectory(prefix='repo-stack-objects-')
        isolated = Path(self.temp.name)
        (isolated / 'refs').mkdir()
        (isolated / 'objects').mkdir()
        (isolated / 'HEAD').write_text('ref: refs/heads/unused\n')
        config = '[core]\n bare = true\n repositoryFormatVersion = ' + ('0' if object_format == 'sha1' else '1') + '\n'
        if object_format == 'sha256':
            config += '[extensions]\n objectFormat = sha256\n'
        (isolated / 'config').write_text(config)
        # Allowlist, not a denylist: excludes GIT_CONFIG*, replacements, tracing,
        # alternate objects, exec paths, pagers, and injected repository settings.
        env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT') if k in os.environ}
        env.update(HOME=str(isolated), XDG_CONFIG_HOME=str(isolated), LC_ALL='C',
                   GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
                   GIT_DIR=str(isolated), GIT_OBJECT_DIRECTORY=str(self.objects),
                   GIT_NO_REPLACE_OBJECTS='1', GIT_OPTIONAL_LOCKS='0',
                   GIT_TERMINAL_PROMPT='0', GIT_ALLOW_PROTOCOL='', GIT_NO_LAZY_FETCH='1')
        self.runner = Runner(isolated, env, budget)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.temp.cleanup()

    def resolve(self, token):
        if not isinstance(token, str) or not re.fullmatch(r'[0-9a-fA-F]{4,' + str(self.width) + r'}', token):
            raise TimelineError("invalid_revision", "Use explicit hexadecimal commit IDs (4 to object-ID width); refs, ranges and revision expressions are unsupported")
        _, out = self.runner.run(['rev-parse', '--verify', '--end-of-options', token.lower() + '^{commit}'], cap=256)
        oid = out.decode('ascii').strip()
        if not re.fullmatch('[0-9a-f]{' + str(self.width) + '}', oid):
            raise TimelineError('invalid_object', 'Git returned an invalid commit ID')
        return oid

    def read_object(self, oid, kind, maximum):
        _, size = self.runner.run(['cat-file', '-s', oid], cap=64)
        try:
            count = int(size)
        except ValueError:
            raise TimelineError('invalid_object', 'Invalid Git object size') from None
        if count < 0 or count > maximum:
            raise TimelineError('blob_bytes_limit' if kind == 'blob' else 'git_output_limit', f'{kind} object exceeds its byte limit ({maximum})')
        if kind == 'blob':
            self.budget.consume('total_bytes', count)
        _, raw = self.runner.run(['cat-file', kind, oid], cap=maximum)
        if len(raw) != count:
            raise TimelineError('invalid_object', 'Git object size mismatch')
        return raw

    def commit(self, oid):
        raw = self.read_object(oid, 'commit', min(self.budget.limits.git_output_bytes, 1_048_576))
        headers = raw.split(b'\n\n', 1)[0].splitlines()
        tree = None
        parents = []
        timestamp = None
        for line in headers:
            if line.startswith(b'tree '):
                tree = line[5:].decode('ascii')
            elif line.startswith(b'parent '):
                parents.append(line[7:].decode('ascii'))
            elif line.startswith(b'committer '):
                m = re.search(rb' (-?\d+) ([+-]\d{4})$', line)
                if m:
                    timestamp = {'unix': int(m[1]), 'offset': m[2].decode('ascii')}
        if tree is None or any(not re.fullmatch('[0-9a-f]{' + str(self.width) + '}', x) for x in [tree, *parents]):
            raise TimelineError('invalid_object', 'Invalid commit tree/parent headers')
        return dict(commit=oid, tree=tree, parents=parents, committer_time=timestamp)

    def manifests(self, tree, lockfiles=False):
        # Include directories in counts. Git never recurses into gitlinks.
        _, out = self.runner.run(['ls-tree', '-r', '-t', '-z', '--full-tree', tree])
        entries = out.split(b'\0')
        if entries[-1] != b'':
            raise TimelineError('invalid_object', 'Unterminated tree listing')
        found = []
        skipped = []
        names = (b'package.json', b'pyproject.toml') + ((b'package-lock.json', b'npm-shrinkwrap.json') if lockfiles else ())
        for entry in entries[:-1]:
            self.budget.consume('tree_entries')
            try:
                header, path = entry.split(b'\t', 1)
                mode, kind, oid = header.split(b' ')
            except ValueError:
                raise TimelineError('invalid_object', 'Invalid tree entry') from None
            if kind == b'commit':
                skipped.append({'code': 'submodule_skipped', 'path': path.decode('utf-8', 'surrogateescape')})
            if path.rsplit(b'/', 1)[-1] not in names:
                continue
            self.budget.consume('manifests')
            found.append((path.decode('utf-8', 'surrogateescape'), mode.decode(), kind.decode(), oid.decode()))
        return sorted(found), skipped

    def relation(self, before, after):
        if before == after:
            return 'same'
        # Read the bounded reachable graph in full. merge-base may short-circuit
        # using timestamps without encountering a missing parent object.
        maximum = self.budget.limits.ancestry_commits
        code, raw = self.runner.run(['rev-list', '--parents', f'--max-count={maximum+1}', before, after], allowed=(0,128))
        if code == 128:
            return 'unknown'
        lines = raw.decode('ascii').splitlines()
        if len(lines) > maximum:
            raise TimelineError('ancestry_commits_limit', 'Reachable ancestry exceeds its commit limit')
        graph = {}
        for line in lines:
            fields = line.split()
            graph[fields[0]] = fields[1:]
        for target, start, name in ((before, after, 'ancestor'), (after, before, 'descendant')):
            pending, seen = [start], set()
            while pending:
                self.budget.check()
                oid = pending.pop()
                if oid == target:
                    return name
                if oid not in graph:
                    return 'unknown'
                if oid not in seen:
                    seen.add(oid)
                    pending.extend(graph[oid])
        return 'diverged_or_unrelated'
