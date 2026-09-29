import json
import unittest
from repo_stack_timeline.extract import extract
from repo_stack_timeline.compare import compare


def manifest(text, python=False):
    return extract('pyproject.toml' if python else 'package.json', 'a'*40, text.encode())


class ExtractionTests(unittest.TestCase):
    def test_npm_all_categories_opaque_constraints(self):
        data = {c:{'@scope/a':'npm:elsewhere@^1','local':'file:../local'} for c in ('dependencies','devDependencies','optionalDependencies','peerDependencies')}
        result = manifest(json.dumps(data))
        self.assertEqual(len(result['declarations']),8)
        self.assertEqual(result['status'],'ok')
        self.assertEqual({d['values'][0]['raw'] for d in result['declarations']},{'npm:elsewhere@^1','file:../local'})

    def test_python_details_and_duplicate_marker_requirements(self):
        result = manifest('''[project]
name="fixture"
dependencies=['My_Pkg[SSL,fast] >= 1, < 3; python_version < "3.12"', 'My.Pkg==4; python_version >= "3.12"', 'URL-package @ https://example.invalid/pkg.whl']
[project.optional-dependencies]
CLI=['rich>=1']
[build-system]
requires=['setuptools>=68']
''',True)
        deps = {d['name']:d for d in result['declarations']}
        self.assertEqual(len(deps['my-pkg']['values']),2)
        v = next(x for x in deps['my-pkg']['values'] if x['name_as_declared']=='My_Pkg')
        self.assertEqual(v['extras'],['SSL','fast'])
        self.assertEqual(v['marker'],'python_version < "3.12"')
        self.assertEqual(v['specifier'],'<3,>=1')
        self.assertEqual(deps['url-package']['values'][0]['url'],'https://example.invalid/pkg.whl')
        self.assertEqual(deps['rich']['category'],'project.optional-dependencies.CLI')

    def test_malformed_and_unsupported(self):
        for value in ('{bad','[]','{"dependencies":{},"dependencies":{}}','{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(value=value):
                self.assertEqual(manifest(value)['status'],'invalid')
        for raw in (b'\xff',b'\xef\xbb\xbf{}'):
            self.assertEqual(extract('package.json','x',raw)['status'],'invalid')
        result = manifest('{"dependencies":{"valid":"*","bad":12},"overrides":{"x":"2"}}')
        self.assertEqual(result['status'],'partial')
        self.assertEqual(result['uncertain_categories'],['dependencies'])
        self.assertEqual(len(result['declarations']),1)
        self.assertIn('unsupported_metadata',[d['code'] for d in result['diagnostics']])

    def test_dynamic_does_not_claim_absence(self):
        good = manifest('[project]\ndependencies=["A>=1"]',True)
        bad = manifest('[project]\ndynamic=["dependencies"]',True)
        def snap(m):return dict(commit='a'*40,manifests=[m])
        events = compare(snap(good),snap(bad))
        self.assertEqual(events[0]['kind'],'unknown')
        bad = manifest('[project]\ndynamic=["dependencies"]\ndependencies=["B"]',True)
        self.assertEqual(bad['declarations'],[])
        self.assertIn('static_dynamic_conflict',[d['code'] for d in bad['diagnostics']])

    def test_empty_missing_and_invalid_sections(self):
        for text in ('[project]\ndependencies=2','[project]\ndependencies=["a",2,"???"]','[project]\noptional-dependencies=2','[build-system]\nbuild-backend="x"'):
            self.assertEqual(manifest(text,True)['status'],'partial')
        result = manifest('[tool.poetry.dependencies]\npython=">=3"',True)
        self.assertEqual(result['status'],'partial')
        self.assertEqual(result['declarations'],[])
        self.assertTrue(manifest('[project]\ndependencies=[]',True)['status']=='ok')

    def test_symlink_and_hostile_text(self):
        self.assertEqual(extract('package.json','x',b'../evil','120000')['status'],'unsupported')
        value = '</script><script>globalThis.PWNED=1</script>'
        result = manifest(json.dumps({'dependencies':{value:'<&"'}}))
        self.assertEqual(result['declarations'][0]['name'],value)
        self.assertEqual(result['declarations'][0]['values'][0]['raw'],'<&"')

    def test_duplicate_requirements_and_extra_collisions(self):
        result = manifest('[project]\ndependencies=["a", "a"]\n[project.optional-dependencies]\na_b=["b"]\na-b=["c"]',True)
        d = next(x for x in result['declarations'] if x['name']=='a')
        self.assertEqual(len(d['values']),2)
        self.assertIn('project.optional-dependencies.*',result['uncertain_categories'])

    def test_incomplete_category_cannot_claim_a_known_change(self):
        good=manifest('[project]\ndependencies=["a>=1"]',True)
        partial=manifest('[project]\ndependencies=["a>=2", "not a requirement !"]',True)
        events=compare(dict(commit='a',manifests=[good]),dict(commit='b',manifests=[partial]))
        self.assertEqual(events[0]['kind'],'unknown')
        self.assertIsNotNone(events[0]['before'])
        self.assertIsNotNone(events[0]['after'])

    def test_formatting_and_array_order_do_not_change_declarations(self):
        a=manifest('[project]\ndependencies=["a>=1", "b", "a<4"]',True)
        b=manifest('[project]\ndependencies = [\n "a<4",\n "a>=1", "b"\n]',True)
        self.assertEqual(compare(dict(commit='a',manifests=[a]),dict(commit='b',manifests=[b])),[])
        b=manifest('[project]\ndependencies=["a >=1", "b", "a<4"]',True)
        self.assertEqual(compare(dict(commit='a',manifests=[a]),dict(commit='b',manifests=[b]))[0]['kind'],'changed')
