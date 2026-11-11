"""Drive three synthetic turns through the real Super-agent event source."""
import json
from pathlib import Path
import time
import urllib.request

OUT=Path('/out')
REPLIES=OUT/'replies.jsonl'
offset=0

def log(text):
    with (OUT/'timeline.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'at':time.time(),'text':text},ensure_ascii=False)+'\n')

def pump():
    global offset
    if not REPLIES.exists(): return
    with REPLIES.open(encoding='utf-8') as f:
        f.seek(offset)
        while line := f.readline():
            try:
                e=json.loads(line)
                if e.get('kind') == 'acknowledgement': log('Agent：已接收任务，正在处理。')
            except ValueError: pass
        offset=f.tell()

def event(text, summary):
    request=urllib.request.Request('http://127.0.0.1:39182/event',data=json.dumps({'text':text}).encode(),
        headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=10) as response:
        answer=json.load(response)
    if answer.get('result')!='stored': raise RuntimeError(str(answer))
    with (OUT/'requests.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'at':time.time(),'text':text},ensure_ascii=False)+'\n')
    log('Router 输入: '+summary)

def await_files(names, timeout=180):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        pump()
        try:
            values=[json.loads((OUT/name).read_text(encoding='utf-8')) for name in names]
            # Let the Worker finish reporting before a new turn is delivered.
            settle=time.monotonic()+12
            while time.monotonic()<settle: pump(); time.sleep(.5)
            return values
        except (FileNotFoundError,ValueError): time.sleep(1)
    raise TimeoutError('missing files: '+', '.join(names))

def main():
    try:
        log('模拟状态：可能低落（低置信度）')
        event('这是合成的家庭仿真事件：照护者已允许发起陪伴。模拟感知观察到孩子少回应，情绪“可能低落”、置信度低，不作诊断。请读取 /out/semantic_map.json 和 /out/memory.json，根据已有记忆与真实地图对象挑一个温和的互动主题，生成一句中文提议。不要编造地图对象，不要声称去往或到达地图物体，移动技能只到固定活动点。接着运行唯一批准的移动技能 bash /scripts/run_motion.sh，检查 /out/motion_result.json；把 map_object（地图中的英文类别）、greeting、memory_evidence、motion_success 四个字段写入 /out/round1.json，并据实报告。只在仿真中运行，禁止 GitHub。','情绪信号触发；读取语义地图和已有记忆，选择陪伴主题。')
        motion,first=await_files(['motion_result.json','round1.json'])
        obj=first.get('map_object',''); labels={x['label'] for x in json.loads((OUT/'semantic_map.json').read_text())['objects']}
        if not motion.get('success') or first.get('motion_success') is not True or obj not in labels: raise RuntimeError('round1 map or motion validation failed')
        log('地图与旧记忆：植物；机器人到达活动点。')
        log('Agent：'+str(first.get('greeting','')))
        log('模拟成员: 我现在想看电视；请用图片提示，声音轻一点。')
        event('模拟成员明确回应：我现在想看电视，请用图片提示，声音轻一点。请读取 /out/memory.json，以当前明确偏好更新同一个文件：字段 current_preference 为 tv、visual 为 true、quiet 为 true，保留旧记录和 source=synthetic。再写 /out/round2.json，包含 reply、remembered 三个偏好的信息。先读取文件再更新，读取更新结果核验；只操作仿真，不用 GitHub。','成员修改偏好；读取并更新本地记忆。')
        memory,second=await_files(['memory.json','round2.json'])
        if memory.get('current_preference')!='tv' or memory.get('visual') is not True or memory.get('quiet') is not True: raise RuntimeError('updated memory validation failed')
        log('Agent：'+str(second.get('reply','')))
        log('记忆已更新：电视、图片提示、轻声。')
        log('模拟成员 [下一轮]: 我们开始吧。')
        event('新一轮模拟互动：孩子说“我们开始吧”。请重新读取 /out/memory.json 和 /out/semantic_map.json，根据最新记忆生成一句合适的中文回应与简短活动建议；将 greeting、map_object（英文类别）、memory_evidence 写入 /out/round3.json。memory_evidence 说明哪些已保存偏好影响回应。核验该地图对象存在，只在仿真中运行，并据实报告。','新一轮开始；重新读取记忆与地图，选择互动内容。')
        third,=await_files(['round3.json'])
        if third.get('map_object')!='tv' or not third.get('memory_evidence'): raise RuntimeError('round3 did not use the updated tv memory')
        log('Agent：'+str(third.get('greeting','')))
        log('验证：新一轮使用了电视和交互偏好。')
        (OUT/'scenario_result.json').write_text(json.dumps({'success':True,'round1':first,'round2':second,'round3':third},ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception as exc:
        log('演示失败: '+str(exc))
        (OUT/'scenario_result.json').write_text(json.dumps({'success':False,'error':str(exc)},ensure_ascii=False,indent=2),encoding='utf-8')
        raise
    finally:
        pump(); (OUT/'record.stop').touch()

if __name__=='__main__': main()
