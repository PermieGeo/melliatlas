"""Read-only checks for repository documentation and SDD traceability."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
GUIDANCE_DIRECTORIES = (Path('.'), Path('backend'), Path('web'), Path('docs/specs'))
REQUIRED_DOCUMENTS = (
    Path('README.md'),
    Path('docs/specs/README.md'),
    Path('docs/specs/umbrella_spec_melliatlas.md'),
)
MARKDOWN_LINK = re.compile(r'\[[^\]]+\]\(([^)]+)\)')
MERMAID_BLOCK = re.compile(r'^```mermaid\s*\n(.*?)^```\s*$', re.MULTILINE | re.DOTALL)
STAGE_HEADING = re.compile(r'^### (MVP-\d{2})\s+[—-]', re.MULTILINE)
ROADMAP_ENTRY = re.compile(r'^\|\s*`(MVP-\d{2})`\s*\|', re.MULTILINE)
REQUIREMENT = re.compile(r'^-\s+`(MVP-\d{2}\.R\d{2})`', re.MULTILINE)
ACCEPTANCE = re.compile(r'^-\s+`(MVP-\d{2}\.A\d{2})`', re.MULTILINE)


def without_fenced_code(markdown: str) -> str:
    """Remove fenced code before inspecting prose links."""
    return re.sub(r'^```[^\n]*\n.*?^```\s*$', '', markdown, flags=re.MULTILINE | re.DOTALL)


def missing_relative_links(markdown: str, document: Path, root: Path) -> list[str]:
    """Report missing local Markdown link targets without following external URLs."""
    errors: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(without_fenced_code(markdown)):
        target = raw_target.strip().split(' "', maxsplit=1)[0].strip('<>')
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or target.startswith(('#', '/')):
            continue
        relative = unquote(parsed.path)
        if not relative:
            continue
        resolved = (document.parent / relative).resolve()
        if not resolved.is_relative_to(root.resolve()):
            errors.append(f'{document}: link escapes repository: {target}')
        elif not resolved.exists():
            errors.append(f'{document}: missing link target: {target}')
    return errors


def stage_structure_errors(umbrella: str) -> list[str]:
    """Check that every roadmap stage has independently testable requirements."""
    errors: list[str] = []
    headings = list(STAGE_HEADING.finditer(umbrella))
    stages = [match.group(1) for match in headings]
    roadmap = ROADMAP_ENTRY.findall(umbrella)
    if not stages or stages[0] != 'MVP-01':
        errors.append('Stage descriptions must begin with MVP-01')
    if len(stages) != len(set(stages)):
        errors.append('Duplicate stage description ID')
    if roadmap != stages:
        errors.append('Roadmap IDs must match stage descriptions in order')
    if stages != [f'MVP-{index:02d}' for index in range(1, len(stages) + 1)]:
        errors.append('Stage IDs must form an ordered contiguous sequence')

    seen_requirements: set[str] = set()
    seen_acceptance: set[str] = set()
    for index, heading in enumerate(headings):
        stage = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(umbrella)
        body = umbrella[heading.end():end]
        if '**Objective.**' not in body:
            errors.append(f'{stage}: missing objective')
        if '**Required behavior**' not in body:
            errors.append(f'{stage}: missing required behavior section')
        if '**Acceptance evidence**' not in body:
            errors.append(f'{stage}: missing acceptance evidence section')
        requirements = REQUIREMENT.findall(body)
        acceptances = ACCEPTANCE.findall(body)
        if not requirements:
            errors.append(f'{stage}: missing identified requirements')
        if not acceptances:
            errors.append(f'{stage}: missing identified acceptance checks')
        for requirement in requirements:
            if not requirement.startswith(f'{stage}.'):
                errors.append(f'{stage}: foreign requirement {requirement}')
            if requirement in seen_requirements:
                errors.append(f'Duplicate requirement: {requirement}')
            seen_requirements.add(requirement)
        for acceptance in acceptances:
            if not acceptance.startswith(f'{stage}.'):
                errors.append(f'{stage}: foreign acceptance check {acceptance}')
            if acceptance in seen_acceptance:
                errors.append(f'Duplicate acceptance check: {acceptance}')
            seen_acceptance.add(acceptance)
    return errors


class DocumentationTests(unittest.TestCase):
    def test_required_documents_exist_and_are_meaningful(self) -> None:
        for relative in REQUIRED_DOCUMENTS:
            with self.subTest(document=str(relative)):
                document = ROOT / relative
                self.assertTrue(document.is_file(), f'Missing document: {relative}')
                content = document.read_text(encoding='utf-8')
                self.assertTrue(content.startswith('# '), f'Missing title: {relative}')

    def test_each_agent_guidance_file_has_a_companion_readme(self) -> None:
        for directory in GUIDANCE_DIRECTORIES:
            with self.subTest(directory=str(directory)):
                agents = ROOT / directory / 'AGENTS.md'
                readme = ROOT / directory / 'README.md'
                self.assertTrue(agents.is_file(), f'Missing guidance: {agents}')
                self.assertTrue(readme.is_file(), f'Missing companion README: {readme}')

    def test_local_markdown_links_resolve(self) -> None:
        documents = {ROOT / path for path in REQUIRED_DOCUMENTS}
        documents.update(ROOT / directory / 'README.md' for directory in GUIDANCE_DIRECTORIES)
        errors: list[str] = []
        for path in sorted(documents):
            errors.extend(missing_relative_links(path.read_text(encoding='utf-8'), path, ROOT))
        self.assertEqual([], errors, '\n'.join(errors))

    def test_root_readme_distinguishes_product_scope_and_implemented_state(self) -> None:
        readme = (ROOT / 'README.md').read_text(encoding='utf-8').casefold()
        for requirement in ('beekeeper', 'pollinator', 'conservation',
                            'synthetic', 'current status', 'mvp-01'):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, readme)
        self.assertIn('not yet implemented', readme)
        self.assertIn('not evidence that the area is safe', readme)
        self.assertNotIn('beegeotrace', readme)

    def test_readme_diagrams_are_fenced_and_request_flow_is_explained(self) -> None:
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        diagrams = MERMAID_BLOCK.findall(readme)
        self.assertGreaterEqual(len(diagrams), 2, 'Expected overview and interaction diagrams')
        self.assertEqual(readme.count('```mermaid'), len(diagrams))

        overview = next((item for item in diagrams if 'flowchart LR' in item), None)
        self.assertIsNotNone(overview)
        self.assertIn('Beekeeper', overview)
        self.assertIn('Wild pollinators', overview)

        interaction = next((item for item in diagrams if 'sequenceDiagram' in item), None)
        self.assertIsNotNone(interaction)
        for expected in (
            'actor Beekeeper',
            'participant Server',
            'participant Cache',
            'participant Results',
            'loop Beekeeper checks the investigation status',
            'alt Result not ready yet',
            'else Result available',
            'Request investigation for point X',
            'Point availability and recommended nearby points',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, interaction)

        lowered = readme.casefold()
        self.assertIn('conceptual interaction diagram', lowered)
        self.assertIn('request-and-result interaction flow', lowered)
        self.assertIn('synthetic or fixture-based', lowered)
        self.assertIn('cache or source-oriented store', lowered)

    def test_umbrella_roadmap_and_requirements_are_complete(self) -> None:
        umbrella = (ROOT / 'docs/specs/umbrella_spec_melliatlas.md').read_text(encoding='utf-8')
        self.assertEqual([], stage_structure_errors(umbrella))
        self.assertIn('**Status:**', umbrella)
        self.assertIn('MVP-01', umbrella)
        self.assertIn('wild pollinators', umbrella.lower())

    def test_specification_index_links_to_umbrella(self) -> None:
        index = (ROOT / 'docs/specs/README.md').read_text(encoding='utf-8')
        self.assertRegex(index, r'\[[^\]]+\]\(umbrella_spec_melliatlas\.md\)')
        self.assertIn('active/', index)
        self.assertIn('archive/', index)
        self.assertIn('STATE.json', index)

    def test_documentation_schemas_are_parseable(self) -> None:
        self.assertTrue((ROOT / 'docs/specs/feature-cross-ref.yaml').is_file())
        for name in ('state.schema.json', 'feature-cross-ref.schema.json'):
            with self.subTest(schema=name):
                schema = json.loads((ROOT / 'docs/specs' / name).read_text(encoding='utf-8'))
                self.assertEqual('object', schema['type'])
                self.assertIn('$schema', schema)

    def test_initial_territory_and_source_scope_is_explicit(self) -> None:
        umbrella = (ROOT / 'docs/specs/umbrella_spec_melliatlas.md').read_text(encoding='utf-8')
        stage1 = umbrella.split('### MVP-01 —', maxsplit=1)[1].split('### MVP-02 —', maxsplit=1)[0]
        stage2 = umbrella.split('### MVP-02 —', maxsplit=1)[1].split('### MVP-03 —', maxsplit=1)[0]
        for value in ('Smolensk Oblast', 'Vitebsk Oblast', 'Russia (RU)', 'Belarus (BY)',
                      'Saturn (RU only)', 'public websites/news', 'MVP-01.A06', 'MVP-01.A08'):
            with self.subTest(value=value):
                self.assertIn(value.casefold(), stage1.casefold())
        for value in ('FGIS Saturn', 'Russia', 'Belarus', 'MVP-02.A02',
                      'MVP-02.R03', 'live smoke', 'source-access review'):
            with self.subTest(value=value):
                self.assertIn(value.casefold(), stage2.casefold())
        self.assertIn('MVP-01', umbrella)
        self.assertIn('MVP-02', umbrella)

    def test_feature_catalog_has_unique_stable_ids(self) -> None:
        features = (ROOT / 'docs/FEATURES.md').read_text(encoding='utf-8')
        ids = re.findall(r'^\|\s*`([A-Z][A-Z0-9]*(?:\.[A-Z][A-Z0-9_]*)+)`\s*\|\s*([^|]+)\|$',
                         features, re.MULTILINE)
        feature_ids = [feature_id for feature_id, description in ids]
        self.assertTrue(all(description.strip() for _, description in ids))
        self.assertTrue(feature_ids)
        self.assertEqual(len(feature_ids), len(set(feature_ids)))
        for feature_id in ('GEOGRAPHY.RU_REGIONS', 'GEOGRAPHY.BY_REGIONS',
                           'GEOGRAPHY.PILOT_DISTRICTS', 'SOURCES.PUBLIC_WEB_RU',
                           'SOURCES.PUBLIC_WEB_BY', 'SOURCES.SATURN_RU'):
            with self.subTest(feature_id=feature_id):
                self.assertIn(feature_id, feature_ids)
        registry = (ROOT / 'docs/specs/feature-cross-ref.yaml').read_text(encoding='utf-8')
        self.assertIn('schema_version: 2\nfeatures:', registry)
        referenced_ids = re.findall(r'^  - feature_id: ([A-Z][A-Z0-9_.]+)$',
                                    registry, re.MULTILINE)
        self.assertTrue(referenced_ids)
        self.assertEqual(len(referenced_ids), len(set(referenced_ids)))
        self.assertTrue(set(referenced_ids).issubset(set(feature_ids)))
        referenced_paths = re.findall(r'^    spec_paths: \[([^\]]+)\]$',
                                      registry, re.MULTILINE)
        self.assertTrue(referenced_paths)
        for item in referenced_paths:
            for path in item.split(', '):
                self.assertTrue((ROOT / path).is_file(), f'Missing linked spec: {path}')

    def test_active_checkpoint_and_linked_plan_are_consistent(self) -> None:
        state = json.loads((ROOT / 'docs/specs/STATE.json').read_text(encoding='utf-8'))
        schema = json.loads((ROOT / 'docs/specs/state.schema.json').read_text(encoding='utf-8'))
        self.assertEqual(schema['properties']['schemaVersion']['const'], state['schemaVersion'])
        self.assertEqual(schema['properties']['mode']['const'], state['mode'])
        selected = [item for item in state['workstreams']
                    if item['id'] == state['selectedWorkstreamId']]
        self.assertEqual(1, len(selected))
        for workstream in state['workstreams']:
            with self.subTest(workstream=workstream['id']):
                spec_path = Path(workstream['specPath'])
                self.assertTrue(spec_path.is_relative_to(Path('docs/specs/active/subspecs')))
                self.assertTrue((ROOT / spec_path).is_file())
                self.assertIn(workstream['phase'], schema['properties']['workstreams']
                              ['items']['properties']['phase']['enum'])
                plan_path = spec_path.with_name(spec_path.stem + '_implementation_plan.md')
                self.assertTrue((ROOT / plan_path).is_file())
                spec = (ROOT / spec_path).read_text(encoding='utf-8')
                plan = (ROOT / plan_path).read_text(encoding='utf-8')
                self.assertIn(plan_path.name, spec)
                self.assertIn(spec_path.name, plan)
                self.assertIn('## ', spec)
                self.assertIn('## ', plan)
                self.assertIn('contract.md', plan)
                self.assertIn('TDD', plan)
                errors = missing_relative_links(spec, ROOT / spec_path, ROOT)
                errors.extend(missing_relative_links(plan, ROOT / plan_path, ROOT))
                self.assertEqual([], errors)

    def test_active_plan_preserves_test_inventory_and_separates_current_task(self) -> None:
        relative = Path('docs/specs/active/subspecs/subspec-01-backend-planning.md')
        if not (ROOT / relative).exists():
            return
        spec = (ROOT / relative).read_text(encoding='utf-8')
        plan = (ROOT / relative.with_name(relative.stem + '_implementation_plan.md')).read_text(encoding='utf-8')
        self.assertTrue(re.search(r'MVP01-BE-R\d{2}', spec))
        self.assertTrue(re.search(r'MVP01-BE-A\d{2}', spec))
        self.assertIn('Next bounded delivery task', plan)
        self.assertIn('Acceptance test inventory', plan)
        self.assertIn('Convergence review after each task', plan)
        self.assertIn('MVP01-BE-V01', plan)
        self.assertIn('BE-T001', plan)
        self.assertIn('BE-T060', plan)
        self.assertIn('Pending', plan)

    def test_link_validator_detects_broken_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / 'README.md'
            document.write_text('[missing](absent.md)', encoding='utf-8')
            self.assertEqual(1, len(missing_relative_links(document.read_text(), document, root)))

    def test_roadmap_validator_detects_missing_acceptance_evidence(self) -> None:
        umbrella = (ROOT / 'docs/specs/umbrella_spec_melliatlas.md').read_text(encoding='utf-8')
        damaged = umbrella.replace('**Acceptance evidence**', '**Unspecified checks**', 1)
        self.assertTrue(any('missing acceptance evidence' in issue for issue in stage_structure_errors(damaged)))


if __name__ == '__main__':
    unittest.main()
