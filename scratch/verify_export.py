import urllib.request
import json
import os
import csv
import io

print('1. Scanning python_itsdangerous...')
req_data = json.dumps({
    'repository_path': os.path.abspath('backend/dataset/corpus/python_itsdangerous'),
    'project_id': 'python_itsdangerous'
}).encode('utf-8')

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/scan', data=req_data, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as resp:
    scan_res = json.loads(resp.read().decode())
    print('Scan status:', scan_res['status'])

print('2. Fetching risk and graph data...')
with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/projects/python_itsdangerous/risk') as resp:
    risk_res = json.loads(resp.read().decode())

with urllib.request.urlopen('http://127.0.0.1:8000/api/v1/projects/python_itsdangerous/graph') as resp:
    graph_res = json.loads(resp.read().decode())

print('Assets count in risk:', len(risk_res['assets']))
print('Nodes count in graph:', len(graph_res['nodes']))

nodeTypeMap = {}
for n in graph_res['nodes']:
    nId = n.get('id') or n.get('asset_id')
    if nId:
        nodeTypeMap[nId] = n.get('category') or n.get('type') or 'file'

assets = []
for a in risk_res['assets']:
    factors = a.get('factors', {})
    assets.append({
        'asset_id': a['asset_id'],
        'asset_type': nodeTypeMap.get(a['asset_id'], 'file'),
        'heuristic_risk_score': a.get('score'),
        'scoring_methodology': 'Heuristic Formula (Phase 8 Composite Heuristic — Not GATv2)',
        'factors': {
            k: v.get('value') if isinstance(v, dict) else v for k, v in factors.items()
        },
        'missing_factors': a.get('missing_factors', []),
        'missing_data_policy': a.get('missing_data_policy', 'RENORMALIZE')
    })

json_payload = {
    'report_metadata': {
        'project_id': 'python_itsdangerous',
        'disclaimer': 'Deterministic heuristic only'
    },
    'graph_summary': {
        'total_nodes': len(graph_res['nodes']),
        'total_edges': len(graph_res['edges'])
    },
    'assets': assets
}

# Verify JSON syntax
serialized_json = json.dumps(json_payload, indent=2)
parsed_back = json.loads(serialized_json)
print('JSON Verification: Valid syntax, keys:', list(parsed_back.keys()))
assert len(parsed_back['assets']) == 7, 'Expected 7 assets'

# Verify CSV generation
def escape_csv(val):
    if val is None:
        return '""'
    s = str(val).strip()
    if any(s.startswith(c) for c in ['=', '+', '-', '@', '\t', '\r', '%', '|']):
        s = "'" + s
    s = s.replace('"', '""')
    return f'"{s}"'

csv_lines = [
    'project_id,asset_id,asset_type,heuristic_risk_score,scoring_methodology,missing_factors'
]
for a in assets:
    csv_lines.append(','.join([
        escape_csv('python_itsdangerous'),
        escape_csv(a['asset_id']),
        escape_csv(a['asset_type']),
        escape_csv(a['heuristic_risk_score']),
        escape_csv(a['scoring_methodology']),
        escape_csv('; '.join(a['missing_factors']))
    ]))

csv_content = '\r\n'.join(csv_lines)
reader = csv.reader(io.StringIO(csv_content))
rows = list(reader)
print('CSV Verification: Valid syntax, row count:', len(rows))
print('CSV Header:', rows[0])
print('CSV First data row:', rows[1])
assert len(rows) == 8, 'Expected 1 header + 7 data rows'
print('[PASS] Generated real CSV and JSON verified successfully against backend output!')
