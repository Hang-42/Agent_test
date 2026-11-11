# DeepSeek Super-agent 家庭仿真试验

## 结果和边界

使用 DeepSeek 官方 `dsh-superagent-prototype`（提交 `8c32a9dc5d72c033816c6a8110b37f40cf94fba4`）及 DeepSeek Harness `0.2.1-rc.3`。`upstream/` 是官方原始源码；`runtime/` 是保留核心编排器、为家庭仿真做小范围修改的源码副本。官方 Router 和 Worker 都通过 DeepSeek API 真正调用模型。2026-11-09 测试模型为 API 提供的默认 `deepseek-flash`；未证明这就是论文实验所用的具体模型。

本轮演示：合成照护者请求 → 官方 Router 接收并分配工单 → 官方 Worker 执行有界 ROS 技能 → MuJoCo 模拟机器人到达目标 → Worker 核验结果 → Worker 使用模型生成中文互动语句并将模拟选择写入 JSON。`output/decisions.json` 包含最初被官方默认编码场景提示词拒绝的事件和修改提示词后的接单记录；`output/replies.jsonl` 是原框架通过本地 Channel 输出的结果。`output/interaction_memory.json` 是一次演示记录，不是完整的记忆管理系统。

视频 `output/demo.mp4` 是 `/vision/color/image_raw` 的实际仿真相机视角，基于墙钟时间补帧，剪除了前面的等待；片尾的 POST-RUN SUMMARY 是事后添加的结果说明，互动内容不是现场屏幕或音频录制。开始及选择输入是合成的；尚未接入真实成员情绪感知、语音或语义地图，不适用于真实儿童或机器人。

## 结构与修改

- `runtime/src/app/setup.ts`：仅当 `FAMILY_AGENT_LOCAL_DEMO=1` 时启用仿真本地模式，不执行官方 GitHub 账户检查；原代码以工程任务为目标，默认需要 GitHub。
- `runtime/src/sources/family.ts`：注册官方 SourceKind，并在容器本地 `127.0.0.1:39182/event` 接收模拟事件、以本地文件作为输出 Channel。仅用于受控测试，没有实现生产认证或现实用户授权。
- `runtime/src/index.ts`：启动本地事件源；`runtime/src/policy.ts`：仅为本地仿真配置 `demo` 事件来源。
- `configure_prompts.py`：通过官方管理 API 调整 Router 和 Worker 的任务提示词。
- `robot_motion.py` / `run_motion.sh`：固定目标的仿真闭环控制技能，具有限速、超时及退出时发送停止；没有避障或物理急停。
- `record.py`：录制实际 RGB 话题。`start_superagent.sh`：初始化独立 profile、加载官方 bundle，并启动服务。

官方 Worker 具有 shell 能力。当前容器为联调原型，使用 host 网络和 IPC 以连接 ROS；不应连接实机、真实家庭数据或不可信事件。容器内模型服务可以读取挂载的 API 凭据；正式环境必须进一步隔离凭据、限制工具及网络、设计可信授权和独立运动安全机制。

## 本轮部署位置与复现要点

远程临时目录：`/tmp/family_agent_live2`；镜像：`family-agent-superagent:prototype`（官方源码构建）、`family-agent-superagent:simulation`（仿真适配）。`Dockerfile` 和 `Dockerfile.simulation` 分别对应这两个镜像。远程仿真使用 `/tmp/family_agent_super_demo/robot` 这个旧项目副本；仿真生成器会改写生成 XML，因此不要把原仓库直接作为可写挂载。

运行两个容器时使用同一个隔离 ROS domain（本轮为 83），同时配置 host 网络与共享 IPC，否则 ROS 可能发现话题但收不到数据。挂载 `/out` 共享结果、`/scripts` 只读；启动 Super-agent 后运行 `configure_prompts.py`，再向本机 `39182/event` 提交合成事件。启动 `record.py` 后再发送请求。`run_motion.sh` 将 ROS domain 设为 83；修改 domain 时必须同时修改所有进程。

API 密钥存于服务器 `~/.config/family-agent/deepseek_api_key`，不在本项目中。请在完成测试后轮换曾发到聊天中的密钥。调用真实模型会产生 API 用量费用。

## 验证

- 官方适配源码通过 `pnpm typecheck` 和 `pnpm build`。
- 官方 `dsh headless` 通过 DeepSeek API 返回指定测试响应。
- 官方 Router 发出任务，Worker 运行 ROS 技能并报告成功；目标距离约 0.089 m，见 `output/motion_result.json`。
- 模型生成语句和模拟选择见 `output/interaction_memory.json`，Worker 的核验报告见 `output/replies.jsonl`。
