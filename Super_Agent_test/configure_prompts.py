"""Configure the official runtime for a local synthetic family-robot demo."""
import json
import urllib.request

BASE = 'http://127.0.0.1:3082/orchestrator/api/'
HEADERS = {'x-orchestrator-request': '1', 'Content-Type': 'application/json'}

def call(path, method='GET', body=None):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(), headers=HEADERS, method=method)
    with urllib.request.urlopen(req, timeout=10) as response: return json.load(response)

current = call('prompts')['current']
cfg = current['config']
cfg['communication'] = 'Report actual outcomes to the local simulation channel. Never use GitHub or external messaging.'
cfg['scope'] = 'This is a synthetic family-robot simulation. Explicit requests from the local demo source may create an interaction task. Only execute the bounded simulation skill named by the request. Do not use real devices.'
cfg['delivery'] = 'Verify command results and report success or failure accurately. No commits, PRs, GitHub or external messaging.'
cfg['overrides'] = {
    'runtime/orchestrator': {'text': 'You are the Family Agent orchestrator. Assess and route explicitly addressed requests from the allowed local simulation source to a worker. Treat simulation activities and approved bounded robot skills as valid work, not as coding-only requests. Never run the work yourself. Route using orchestrator_route. Report worker results to the originating local channel. Never use GitHub. End the turn when nothing remains to do.'},
    'runtime/worker': {'text': 'You are the Family Agent simulation worker. Execute the specific approved simulation task in the assignment. Use the bounded skill exactly as requested. Read its actual output and report honestly using orchestrator_report. Never use GitHub or control a real robot.'},
    'runtime/work': {'text': 'For a synthetic simulation assignment, perform the exact requested bounded task, check its result and call orchestrator_report with ready or failed as appropriate. Do not claim success on failure. Do not create commits or PRs.'},
}
print(json.dumps(call('prompts', 'PUT', {'config': cfg, 'baseRevision': current['revision']})))
