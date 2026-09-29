"""Fixture writer: uses Git plumbing, never production extraction/comparison."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


class Repository:
    def __init__(self, root, object_format='sha1'):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.env = {'PATH': os.environ['PATH'], 'HOME': str(self.root), 'LC_ALL': 'C',
                    'GIT_CONFIG_NOSYSTEM':'1', 'GIT_CONFIG_GLOBAL':os.devnull,
                    'GIT_AUTHOR_NAME':'Synthetic author', 'GIT_AUTHOR_EMAIL':'fixture@example.invalid',
                    'GIT_COMMITTER_NAME':'Synthetic author', 'GIT_COMMITTER_EMAIL':'fixture@example.invalid'}
        self.git('init', '--quiet', '--object-format='+object_format)

    def git(self, *args, data=None, timestamp=1_700_000_000):
        env = dict(self.env, GIT_AUTHOR_DATE=f'{timestamp} +0000', GIT_COMMITTER_DATE=f'{timestamp} +0000')
        return subprocess.run(['git', *args], cwd=self.root, env=env, input=data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout

    def commit(self, files, parents=(), timestamp=1_700_000_000, message='synthetic fixture'):
        tree = {}
        for path, content in files.items():
            parts = path.split('/')
            cursor = tree
            for part in parts[:-1]:
                cursor = cursor.setdefault(part, {})
            if isinstance(content, tuple):
                cursor[parts[-1]] = content
            else:
                if isinstance(content, str):
                    content = content.encode()
                cursor[parts[-1]] = ('100644', 'blob', self.git('hash-object','-w','--stdin',data=content).decode().strip())
        def write_tree(entries):
            raw = b''
            for name, value in sorted(entries.items()):
                if isinstance(value,dict):
                    value = ('040000','tree',write_tree(value))
                mode, kind, oid = value
                raw += f'{mode} {kind} {oid}\t'.encode() + name.encode('utf-8','surrogateescape') + b'\0'
            return self.git('mktree','-z',data=raw).decode().strip()
        oid = write_tree(tree)
        args = ['commit-tree',oid]
        for parent in parents:
            args.extend(['-p',parent])
        return self.git(*args,data=(message+'\n').encode(),timestamp=timestamp).decode().strip()


def file_state(root):
    result = {}
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink():
            result[str(p.relative_to(root))] = ('symlink',os.readlink(p))
        elif p.is_file():
            result[str(p.relative_to(root))] = (p.stat().st_mode,hashlib.sha256(p.read_bytes()).hexdigest())
    return result


def seed_history(repo, seed):
    """Independent oracle: expected identities/strings known BEFORE serialization.

    No production parser, canonicalizer, or comparator is called here.
    The model describes supported declarations and uncertainty separately.
    """
    import random
    rng = random.Random(seed)
    name = f'lib-{rng.randrange(1000)}'
    pyname = f'Lib_{rng.randrange(1000)}'
    canonical = pyname.lower().replace('_','-')
    constraint = f'>={rng.randrange(1,9)}.0'
    extra = rng.choice(['cli', 'test', 'web'])
    path = rng.choice(['packages/雪/package.json', 'apps/café/package.json', 'nested/space name/package.json'])
    group = 'project.optional-dependencies.'+extra
    requirement = f'{pyname}[TLS]{constraint}; python_version < "3.13"'
    root_files = {'package.json':json.dumps({'dependencies':{name:'^1.0.0'},'devDependencies':{'tool':'~2'}}),
                  'pyproject.toml':'[project]\nname="fixture"\ndependencies=['+json.dumps(requirement)+']\n[project.optional-dependencies]\n'+extra+'=["test-kit==1"]\n[build-system]\nrequires=["build-tool>=1"]\n',
                  path:json.dumps({'peerDependencies':{'@scope/widget':'workspace:*'}})}
    def key(p,e,c,n): return (p,e,c,n)
    root = {key('package.json','npm','dependencies',name):['^1.0.0'],key('package.json','npm','devDependencies','tool'):['~2'],
            key('pyproject.toml','python','project.dependencies',canonical):[requirement],
            key('pyproject.toml','python',group,'test-kit'):['test-kit==1'],
            key('pyproject.toml','python','build-system.requires','build-tool'):['build-tool>=1'],
            key(path,'npm','peerDependencies','@scope/widget'):['workspace:*']}
    main_files = dict(root_files, **{'package.json':json.dumps({'dependencies':{name:'^2.0.0'},'optionalDependencies':{'tool':'~2'}})})
    main = dict(root); del main[key('package.json','npm','devDependencies','tool')]
    main[key('package.json','npm','dependencies',name)] = ['^2.0.0']
    main[key('package.json','npm','optionalDependencies','tool')] = ['~2']
    branch_files = dict(root_files); branch_files.pop(path)
    moved = 'moved/'+path
    branch_files[moved] = root_files[path]
    branch = dict(root); branch[key(moved,'npm','peerDependencies','@scope/widget')] = branch.pop(key(path,'npm','peerDependencies','@scope/widget'))
    merge_files = dict(branch_files); merge_files['package.json'] = main_files['package.json']
    merge = dict(main); merge[key(moved,'npm','peerDependencies','@scope/widget')] = merge.pop(key(path,'npm','peerDependencies','@scope/widget'))
    damaged_files = dict(merge_files); damaged_files['package.json'] = '{bad json'
    damaged_files['pyproject.toml'] = '[project]\nname="fixture"\ndynamic=["dependencies", "optional-dependencies"]\n[build-system]\nrequires=["build-tool>=2"]\n'
    damaged = {k:v for k,v in merge.items() if k[0] not in ('package.json','pyproject.toml')}
    damaged[key('pyproject.toml','python','build-system.requires','build-tool')] = ['build-tool>=2']
    uncertainty = [('package.json','*'),('pyproject.toml','project.dependencies'),('pyproject.toml','project.optional-dependencies.*')]
    root_id = repo.commit(root_files,timestamp=1_700_000_000+seed,message=f'seed {seed} root')
    main_id = repo.commit(main_files,[root_id],timestamp=1_600_000_000+seed,message='older timestamp, newer commit')
    branch_id = repo.commit(branch_files,[root_id],timestamp=1_800_000_000+seed,message='branch')
    merge_id = repo.commit(merge_files,[main_id,branch_id],timestamp=1_500_000_000+seed,message='merge')
    damaged_id = repo.commit(damaged_files,[merge_id],timestamp=1_400_000_000+seed,message='incomplete metadata')
    ids = [root_id,main_id,branch_id,merge_id,damaged_id,merge_id,merge_id]
    models = [(root,[]),(main,[]),(branch,[]),(merge,[]),(damaged,uncertainty),(merge,[]),(merge,[])]
    return ids, models


def oracle_events(before, after):
    left, left_unknown = before; right, right_unknown = after
    events = {}
    for identity in set(left) | set(right):
        a,b = left.get(identity),right.get(identity)
        if a == b:
            continue
        kind = 'changed'
        if a is None: kind = 'added'
        if b is None: kind = 'absent'
        for values, unknown in ((a,left_unknown),(b,right_unknown)):
            if values is None:
                p,_,category,_ = identity
                if any(p == path and (c == '*' or c == category or c.endswith('.*') and category.startswith(c[:-1])) for path,c in unknown):
                    kind = 'unknown'
        events[identity] = (kind,a,b)
    return events
