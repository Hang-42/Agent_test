import json
from pathlib import Path
import time
import urllib.request
OUT=Path('/out')
def log(text):
    with (OUT/'timeline.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'at':time.time(),'text':text},ensure_ascii=False)+'\n')
try:
    log('模拟小乐：这次想看植物。')
    text='模拟小乐刚刚说“这次想看植物”。请生成一句简短中文回应，尊重这次的新选择，不要发起移动或声称已到达植物，也不要使用 GitHub。写 /out/stage_final.json，包含 greeting。'
    req=urllib.request.Request('http://127.0.0.1:39182/event',data=json.dumps({'text':text},ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=10) as response:
        if json.load(response).get('result')!='stored': raise RuntimeError('event rejected')
    with (OUT/'requests.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'at':time.time(),'text':text},ensure_ascii=False)+'\n')
    log('任务：根据成员当前选择，生成回应。')
    until=time.monotonic()+120
    while time.monotonic()<until:
        try:
            data=json.loads((OUT/'stage_final.json').read_text(encoding='utf-8'))
            log('Agent：'+str(data['greeting'])); break
        except (FileNotFoundError,json.JSONDecodeError,KeyError): time.sleep(1)
    else: raise TimeoutError('missing final response')
    time.sleep(8)
finally:
    (OUT/'record.stop').touch()
