"""Frozen declaration semantics, version declarations/1 (see docs/semantics.md)."""
import json
import re
import tomllib
from collections import defaultdict
from ._vendor.packaging.requirements import Requirement, InvalidRequirement
from ._vendor.packaging.utils import canonicalize_name

NPM_CATEGORIES = ('dependencies', 'devDependencies', 'optionalDependencies', 'peerDependencies')


def issue(code, category=None, **extra):
    return dict(code=code, **({'category': category} if category is not None else {}), **extra)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _invalid_constant(_):
    raise ValueError('nonfinite JSON value')


def extract(path, blob, raw, mode='100644'):
    ecosystem = 'npm' if path.rsplit('/', 1)[-1] == 'package.json' else 'python'
    result = dict(path=path, blob=blob, mode=mode, ecosystem=ecosystem,
                  status='ok', uncertain_all=False, uncertain_categories=[],
                  declarations=[], diagnostics=[])
    if mode not in ('100644', '100755'):
        result.update(status='unsupported', uncertain_all=True)
        result['diagnostics'].append(issue('manifest_not_regular_file'))
        return result
    try:
        text = raw.decode('utf-8')
        data = (json.loads(text, object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
                if ecosystem == 'npm' else tomllib.loads(text))
        if not isinstance(data, dict):
            raise ValueError('manifest root must be an object')
    except (UnicodeError, ValueError, RecursionError):
        result.update(status='invalid', uncertain_all=True)
        result['diagnostics'].append(issue('malformed_manifest'))
        return result
    grouped = defaultdict(list)

    def warn(code, category=None, uncertain=False, **extra):
        result['diagnostics'].append(issue(code, category, **extra))
        if uncertain:
            result['uncertain_categories'].append(category)

    def requirements(values, category):
        if not isinstance(values, list):
            warn('invalid_dependency_section', category, uncertain=True)
            return
        for value in values:
            if not isinstance(value, str):
                warn('invalid_requirement', category, uncertain=True)
                continue
            try:
                req = Requirement(value)
            except (InvalidRequirement, RecursionError):
                warn('invalid_requirement', category, uncertain=True, declaration=value)
                continue
            name = canonicalize_name(req.name)
            grouped[(category, name)].append(dict(raw=value, name_as_declared=req.name,
                extras=sorted(req.extras), specifier=str(req.specifier),
                marker=str(req.marker) if req.marker else None, url=req.url))

    if ecosystem == 'npm':
        for category in NPM_CATEGORIES:
            if category not in data:
                continue
            values = data[category]
            if not isinstance(values, dict):
                warn('invalid_dependency_section', category, uncertain=True)
                continue
            for name, value in sorted(values.items()):
                if not name or not isinstance(value, str):
                    warn('unsupported_declaration', category, uncertain=True, name=name)
                else:
                    grouped[(category, name)].append(dict(raw=value, name_as_declared=name))
        for key in ('bundledDependencies', 'bundleDependencies', 'overrides', 'resolutions', 'peerDependenciesMeta', 'packageExtensions'):
            if key in data:
                warn('unsupported_metadata', key)
    else:
        project = data.get('project')
        if project is None:
            warn('project_metadata_unavailable', 'project.dependencies', uncertain=True)
            warn('project_metadata_unavailable', 'project.optional-dependencies.*', uncertain=True)
        elif not isinstance(project, dict):
            warn('invalid_project_table')
            result['uncertain_all'] = True
        else:
            dynamic = project.get('dynamic', [])
            if not isinstance(dynamic, list) or any(not isinstance(x, str) for x in dynamic):
                warn('invalid_dynamic_metadata')
                result['uncertain_all'] = True
                dynamic = []
            for key in ('dependencies', 'optional-dependencies'):
                if key in dynamic:
                    category = 'project.' + key + ('.*' if key == 'optional-dependencies' else '')
                    warn('dynamic_metadata', category, uncertain=True)
                    if key in project:
                        warn('static_dynamic_conflict', category)
            if 'dependencies' in project and 'dependencies' not in dynamic:
                requirements(project['dependencies'], 'project.dependencies')
            if 'optional-dependencies' in project and 'optional-dependencies' not in dynamic:
                values = project['optional-dependencies']
                if not isinstance(values, dict):
                    warn('invalid_dependency_section', 'project.optional-dependencies.*', uncertain=True)
                else:
                    seen = set()
                    for group, reqs in sorted(values.items()):
                        category = 'project.optional-dependencies.' + group
                        normalized = canonicalize_name(group)
                        if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?', group) or normalized in seen:
                            warn('invalid_or_colliding_extra', 'project.optional-dependencies.*', uncertain=True, group=group)
                        seen.add(normalized)
                        requirements(reqs, category)
        build = data.get('build-system')
        if build is not None:
            if not isinstance(build, dict) or 'requires' not in build:
                warn('invalid_build_system', 'build-system.requires', uncertain=True)
            else:
                requirements(build['requires'], 'build-system.requires')
        if 'dependency-groups' in data:
            warn('unsupported_metadata', 'dependency-groups')
        tool = data.get('tool', {})
        if isinstance(tool, dict):
            for name in ('poetry', 'pdm', 'uv', 'hatch', 'flit', 'setuptools'):
                if name in tool:
                    warn('tool_metadata_not_evaluated', 'tool.' + name)
    for (category, name), values in sorted(grouped.items()):
        values.sort(key=lambda x: x['raw'])
        result['declarations'].append(dict(category=category, name=name, values=values))
    result['uncertain_categories'] = sorted(set(result['uncertain_categories']))
    if result['uncertain_all'] or result['uncertain_categories']:
        result['status'] = 'partial'
    return result
