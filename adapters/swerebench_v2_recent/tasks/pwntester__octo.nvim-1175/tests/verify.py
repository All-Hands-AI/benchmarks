#!/opt/openhands-sdk-venv/bin/python
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path
import log_parsers
TIMING = (
    re.compile(r"\s*\[\s*\d+(?:\.\d+)?\s*(?:ms|s)\s*\]\s*$", re.I),
    re.compile(r"\s+in\s+\d+(?:\.\d+)?\s+(?:msec|sec)\b", re.I),
    re.compile(r"\s*\(\s*\d+(?:\.\d+)?\s*(?:ms|s)\s*\)\s*$", re.I),
)
FORBIDDEN = (
    re.compile(r"\b(?:curl|wget|gh)\b", re.I),
    re.compile(r"\bgit\s+(?:clone|fetch|pull|ls-remote)\b", re.I),
    re.compile(r"(?:github\.com|raw\.githubusercontent\.com|api\.github\.com|gitlab\.com|bitbucket\.org)", re.I),
)
def normalize(name):
    for pattern in TIMING:
        name = pattern.sub("", name)
    return name.strip()
def command_violations(trajectory, repository, instance_id):
    if not trajectory.exists():
        return ["agent trajectory missing"]
    data = json.loads(trajectory.read_text())
    violations = []
    identifiers = (repository.lower(), instance_id.lower())
    for step in data.get("steps", []):
        for call in step.get("tool_calls", []):
            args = call.get("arguments", {})
            command = args.get("command") if isinstance(args, dict) else None
            if not isinstance(command, str):
                continue
            if any(pattern.search(command) for pattern in FORBIDDEN):
                violations.append(command[:500])
            lowered = command.lower()
            if any(identifier in lowered for identifier in identifiers) and re.search(r"\b(?:curl|wget|gh|git)\b", lowered):
                violations.append(command[:500])
    return list(dict.fromkeys(violations))
spec = json.loads(Path('/tests/spec.json').read_text())
violations = command_violations(Path('/logs/agent/trajectory.json'), spec['repo'], spec['instance_id'])
search_audit = Path('/logs/agent/pplx_search_audit.json')
if search_audit.exists():
    violations.extend(json.loads(search_audit.read_text()).get('violations', []))
patch_path = Path('/tmp/swerebench_test.patch')
patch_path.write_text(spec['test_patch'])
apply_result = subprocess.run(
    ['git', '-C', spec['repo_dir'], 'apply', str(patch_path)],
    capture_output=True, text=True,
)
if apply_result.returncode != 0:
    violations.append('hidden test patch failed to apply')
    output = apply_result.stdout + apply_result.stderr
else:
    result = subprocess.run(['bash', '-lc', spec['test_cmd']], cwd=spec['repo_dir'], capture_output=True, text=True, timeout=7000)
    output = (result.stdout or '') + (result.stderr or '')
Path('/logs/verifier/test-output.txt').write_text(output)
parser = getattr(log_parsers, spec['log_parser'])
parsed = {normalize(name): status for name, status in parser(output).items()}
passed = {name for name, status in parsed.items() if status == 'PASSED'}
expected = {normalize(name) for name in spec['PASS_TO_PASS'] + spec['FAIL_TO_PASS']}
reward = 1.0 if passed == expected and not violations else 0.0
report = {
    'reward': reward,
    'lookup_violations': violations,
    'passed_match': passed == expected,
    'missing_expected': sorted(expected - passed),
    'unexpected_passed': sorted(passed - expected),
}
Path('/logs/verifier/report.json').write_text(json.dumps(report, indent=2))
Path('/logs/verifier/reward.txt').write_text(f'{reward}\n')
