"""Synthetic human events -> real Super-agent Worker -> simulation skills."""
import json
from pathlib import Path
import time
import urllib.request

OUT=Path('/out'); offset=0
def log(text):
    with (OUT/'timeline.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'at':time.time(),'text':text},ensure_ascii=False)+'\n')
def pump():
    global offset
    path=OUT/'replies.jsonl'
    if not path.exists(): return
    with path.open(encoding='utf-8') as f:
        f.seek(offset)
        while line:=f.readline():
            try:
                item=json.loads(line)
                if item.get('kind')=='acknowledgement': log('Agent：已接收任务。')
            except ValueError: pass
        offset=f.tell()
def event(text,summary):
    payload=json.dumps({'text':text},ensure_ascii=False).encode()
    req=urllib.request.Request('http://127.0.0.1:39182/event',data=payload,headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=10) as response:
        if json.load(response).get('result')!='stored': raise RuntimeError('event rejected')
    with (OUT/'requests.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'at':time.time(),'text':text},ensure_ascii=False)+'\n')
    log('任务：'+summary)
def wait(names,timeout=360):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        pump()
        try:
            result=[json.loads((OUT/name).read_text(encoding='utf-8')) for name in names]
            for name,obj in zip(names,result):
                if name.startswith('skill_') and not obj.get('success'): raise RuntimeError(name+' failed: '+str(obj))
            # Give the Worker time to publish its own result before a follow-up.
            t=time.monotonic()+7
            while time.monotonic()<t: pump(); time.sleep(.4)
            return result
        except (FileNotFoundError,json.JSONDecodeError): time.sleep(1)
    raise TimeoutError('missing '+', '.join(names))

def main():
 try:
    log('模拟状态：暂未回应；可能低落（低置信度）')
    event('合成家庭仿真：照护者允许短时陪伴。模拟状态为暂未回应、可能低落且置信度低，不做诊断。先读取 /out/memory.json 与 /out/semantic_map.json，根据植物旧记忆和地图写一个简短中文邀请，允许拒绝。将 greeting 和 map_object 写到 /out/invite.json，只能引用真实地图类别，不要运行运动，不使用 GitHub。','状态触发；读取旧记忆与语义地图。')
    invite,=wait(['invite.json']); assert invite.get('map_object')=='potted_plant'
    log('Agent：'+invite['greeting']); log('模拟小乐：好呀。')
    event('模拟小乐明确同意。请按顺序使用 bash /scripts/run_skill.sh activity，然后 bash /scripts/run_skill.sh plant，最后 bash /scripts/run_skill.sh point-plant。每项等待结束并验证对应 /out/skill_*.json 的 success；不要将预设路线描述成地图自主导航。完成后写 /out/stage_plant.json，包含 success 和简短中文提示。只操作仿真。','前往活动点和植物观察点，云台虚拟提示。')
    a,b,c,stage=wait(['skill_activity.json','skill_plant.json','skill_point-plant.json','stage_plant.json'])
    assert stage.get('success') is True
    log('Agent：'+str(stage.get('message','请看植物附近。')))
    log('模拟小乐：找到了！叶子是绿色的。')
    log('预设提示：能再找一找叶子吗？')
    log('模拟小乐：（暂未回应）')
    event('模拟互动：小乐暂未回应，不判断情绪。请运行 bash /scripts/run_skill.sh point-leaf 并验证 /out/skill_point-leaf.json；写 /out/stage_leaf.json，含 success 与一句耐心的中文提示，不要操作 GitHub。','等待后调整云台，给出第二次虚拟提示。')
    _,leaf=wait(['skill_point-leaf.json','stage_leaf.json']); assert leaf.get('success') is True
    log('Agent：'+str(leaf.get('message','没关系，我们慢慢找。')))
    log('模拟小乐：这里是叶子。')
    log('预设反馈：对，你找到了！')
    log('模拟小乐：想看电视图片，说话轻一点。')
    event('模拟小乐明确请求改看电视图片，声音轻一点。请读取 /out/semantic_map.json 确认 tv 存在，读取并更新 /out/memory.json：current_preference=tv、visual=true、quiet=true，保留已有历史及 source=synthetic。依次运行 bash /scripts/run_skill.sh tv 和 bash /scripts/run_skill.sh point-tv 并验证结果，写 /out/stage_tv.json 含 success、message。不要声称电视已被打开；只在仿真执行。','更新偏好，前往电视观察点并虚拟提示。')
    _,_,tv=wait(['skill_tv.json','skill_point-tv.json','stage_tv.json']); assert tv.get('success') is True
    memory=json.loads((OUT/'memory.json').read_text()); assert memory.get('current_preference')=='tv' and memory.get('quiet') is True and memory.get('visual') is True
    log('记忆更新：电视图片、轻声。'); log('Agent：'+str(tv.get('message','我们来看看电视。')))
    log('模拟小乐：这里是电视屏幕。'); log('预设反馈：对，这是电视屏幕。')
    log('模拟小乐：我想休息。')
    event('模拟小乐提出休息。请运行 bash /scripts/run_skill.sh home 并验证 /out/skill_home.json，写 /out/stage_home.json 含 success 和一句中文回应；先关闭虚拟提示，不能再追问。只在仿真。','关闭虚拟提示，返回等待点。')
    _,home=wait(['skill_home.json','stage_home.json']); assert home.get('success') is True
    log('Agent：'+str(home.get('message','好，我们先休息。')))
    log('模拟小乐（稍后）：我们再玩一次吧。')
    event('新一轮模拟互动，小乐只说：我们再玩一次吧。请重新读取 /out/memory.json 与 /out/semantic_map.json，用最新记忆生成一句中文活动建议，提供更换选项，不要声称实际打开电视。写 /out/stage_recall.json，含 greeting、map_object 和 memory_evidence。只在仿真。','读取更新记忆，生成下一轮建议。')
    recall,=wait(['stage_recall.json']); assert recall.get('map_object')=='tv' and recall.get('memory_evidence')
    log('Agent：'+str(recall['greeting']))
    log('模拟小乐：这次想看植物。')
    log('模拟脚本：本轮在成员选择植物后结束。')
    (OUT/'story_result.json').write_text(json.dumps({'success':True,'invite':invite,'plant':stage,'leaf':leaf,'tv':tv,'home':home,'recall':recall},ensure_ascii=False,indent=2),encoding='utf-8')
 except Exception as e:
    log('演示停止：'+str(e)); (OUT/'story_result.json').write_text(json.dumps({'success':False,'error':str(e)},ensure_ascii=False,indent=2),encoding='utf-8'); raise
 finally:
    pump(); (OUT/'record.stop').touch()

if __name__=='__main__': main()
