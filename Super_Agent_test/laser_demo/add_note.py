import json
import time
with open('/out/timeline.jsonl','a',encoding='utf-8') as f:
    f.write(json.dumps({'at':time.time(),'text':'校验提示：机器人仅到预设观察点；未验证到植物旁。'},ensure_ascii=False)+'\n')
